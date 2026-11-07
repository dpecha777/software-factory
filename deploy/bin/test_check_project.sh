#!/usr/bin/env bash
# Fixture tests for check-project.sh: each accepted layout passes its line, and the matching
# negative control fails it (a check that cannot fail proves nothing). Stubs gh and memspec on
# PATH; touches nothing outside a temp dir. Run: bash deploy/bin/test_check_project.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK="$HERE/check-project.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
pass=0; failn=0
expect() { # expect <name> <output-file> <regex>   (line must appear)
  if grep -qE "$3" "$2"; then pass=$((pass+1)); else failn=$((failn+1)); echo "FAIL $1: no line matching /$3/"; sed 's/^/    /' "$2"; fi; }
reject() { # reject <name> <output-file> <regex>   (line must not appear)
  if grep -qE "$3" "$2"; then failn=$((failn+1)); echo "FAIL $1: unexpected line /$3/"; grep -E "$3" "$2" | sed 's/^/    /'; else pass=$((pass+1)); fi; }

# Stubs. gh: behaviour chosen by GH_MODE; absent mode = "not a GitHub repo".
mkdir -p "$T/bin"
cat > "$T/bin/gh" <<'GH'
#!/usr/bin/env bash
[ -n "${GH_MODE:-}" ] || exit 1
case "$*" in
  "repo view --json defaultBranchRef"*) echo main ;;
  "repo view"*) exit 0 ;;
  *"/rulesets --jq"*) [ "$GH_MODE" = ruleset ] && echo 7 ;;
  *"/rulesets/7"*) printf 'cleat\nenola\ntrivy\n' ;;
  *"/protection"*) if [ "$GH_MODE" = protection ]; then printf 'test\ntrivy\n'; else echo '{"message":"Not Found","status":"404"}'; exit 1; fi ;;
  "pr list"*) echo abc123 ;;
  *"commits/abc123/status"*) [ "$GH_MODE" = poller ] && echo pr-ticket-key ;;
  *"commits/abc123/check-runs"*) echo trivy ;;
  "secret list"*|"variable list"*) ;;
esac
exit 0
GH
cat > "$T/bin/memspec" <<'MS'
#!/usr/bin/env bash
[ "$1" = stores ] || exit 0
echo "Store layers (highest priority first):"
echo "  team [ro] (priority 10) — ${MS_PATH:-/nowhere} (3 items)"
echo "  global [rw] (priority 0) — $HOME/.memspec (9 items)"
MS
chmod +x "$T/bin/gh" "$T/bin/memspec"
export PATH="$T/bin:$PATH"

# repo <dir>: a minimal adopted repo, v0.5 layout, team store bound at $T/ctx/.memspec.
repo() {
  local d="$1"; mkdir -p "$d" && cd "$d" && git init -q . && git config user.email t@t && git config user.name t
  printf '<!-- context-standard:begin -->\n<!--\ncontext-standard: v0.5\nteam-context: acme/acme-team-context\n-->\n<!-- context-standard:end -->\n' > AGENTS.md
  printf '@AGENTS.md\n' > CLAUDE.md
  printf 'context-standard: v0.5\n' > .context-standard.lock
  mkdir -p docs/standard docs/adr .memspec && : > docs/standard/agents-core.md
  printf 'stores:\n  - name: team\n    path: %s/ctx/.memspec\n    priority: 10\n    writable: false\n' "$T" > .memspec/config.yaml
  cp .memspec/config.yaml .memspec.yaml
  git add -A && git commit -qm init
}
run() { ( cd "$1" && bash "$CHECK" ) > "$2" 2>&1; }

# 1. hooks follow core.hooksPath; cleat installed makes pre-push required there.
repo "$T/r1"; mkdir -p .githooks quality/bin && echo '{}' > quality.json && : > quality/bin/gate.py
git config core.hooksPath .githooks; : > .githooks/pre-push
run "$T/r1" "$T/o1"
expect hooks-dir "$T/o1" '^OK +\.githooks/pre-push'
reject hooks-dir-noscripts "$T/o1" 'scripts/git-hooks/pre-push'
rm .githooks/pre-push; run "$T/r1" "$T/o1n"
expect hooks-dir-neg "$T/o1n" '^MISSING +\.githooks/pre-push'

# 2. an absent sensor reports once, without its files, hooks or CI job.
repo "$T/r2"; run "$T/r2" "$T/o2"
expect cleat-once "$T/o2" '^MISSING +cleat \(sensor 3\)'
expect enola-once "$T/o2" '^MISSING +enola \(sensor 4\)'
reject cleat-cascade "$T/o2" '^[A-Z]+ +(quality/bin/gate\.py|quality\.json|\.claude/settings\.json|\.gitignore ignores \.enola|[^ ]*/pre-push|enola-intent)'
expect gate-jobs-trivy-only "$T/o2" 'no workflow defines: trivy \('

# 3. .enola/ ignore rule is recognised before the baseline directory exists.
repo "$T/r3"; : > enola-intent.yaml; printf '.enola/\n' > .gitignore; run "$T/r3" "$T/o3"
expect enola-ignored "$T/o3" '^OK +\.gitignore ignores \.enola/'
: > .gitignore; run "$T/r3" "$T/o3n"
expect enola-ignored-neg "$T/o3n" '^MISSING +\.gitignore ignores \.enola/'

# 4. team context: a header without the field may bind through memspec; "unset" may not.
repo "$T/r4"; sed -i.bak '/^team-context:/d' AGENTS.md && rm AGENTS.md.bak; run "$T/r4" "$T/o4"
expect team-binding "$T/o4" '^OK +team context bound +read-only store '"$T"'/ctx/.memspec'
sed -i.bak 's/^context-standard: v0.5$/context-standard: v0.5\nteam-context: unset/' AGENTS.md && rm AGENTS.md.bak; run "$T/r4" "$T/o4n"
expect team-unset-neg "$T/o4n" '^MISSING +AGENTS.md: team-context wired'

# 5. memspec stores: OK only for a store this repo binds (no binding = user config, proves nothing).
repo "$T/r5"; mkdir -p "$T/ctx/.memspec"
MS_PATH="$T/ctx/.memspec" run "$T/r5" "$T/o5"
expect memspec-bound "$T/o5" '^OK +memspec stores'
MS_PATH="/elsewhere/.memspec" run "$T/r5" "$T/o5n"
expect memspec-foreign-neg "$T/o5n" '^MISSING +memspec stores +none of the bound'
rm .memspec/config.yaml .memspec.yaml; MS_PATH="$T/ctx/.memspec" run "$T/r5" "$T/o5u"
expect memspec-unbound-neg "$T/o5u" '^MISSING +memspec stores +this repo binds no'

# 6. version drift is one OPTIONAL line naming the current version.
repo "$T/r6"; printf 'context-standard: v0.3\n' > .context-standard.lock; run "$T/r6" "$T/o6"
expect version-drift "$T/o6" '^OPTIONAL +context-standard version +v0\.3, current v0\.[0-9]+'

# 7. ledger shapes, offline: local toml + scripts/jira_sync.py; a toml without project fails.
repo "$T/r7"; mkdir -p scripts tests && : > scripts/jira_sync.py && : > tests/test_jira_sync.py
printf '[jira]\nbase_url = "https://x"\nproject = "ACME"\n' > .jira-sync.toml; git add -A; git commit -qm l
run "$T/r7" "$T/o7"
expect ledger-script "$T/o7" '^OK +jira_sync\.py +scripts/jira_sync\.py'
expect ledger-tests "$T/o7" '^OK +jira_sync tests'
expect ledger-local "$T/o7" '^OK +ledger driver +local'
printf '[jira]\nbase_url = "https://x"\n' > .jira-sync.toml; run "$T/r7" "$T/o7n"
expect ledger-local-neg "$T/o7n" '^MISSING +ledger driver +\.jira-sync\.toml lacks'

# 8. GitHub-side: poller proven by its status; classic protection read when no ruleset; a 404 body
#    never reads as a required check.
repo "$T/r8"; GH_MODE=poller run "$T/r8" "$T/o8"
expect poller "$T/o8" '^OK +ledger driver +external poller'
expect ticket-key-status "$T/o8" '^OK +ticket-key gate'
GH_MODE=none run "$T/r8" "$T/o8n"
expect poller-neg "$T/o8n" '^MISSING +ledger driver'
expect ticket-key-neg "$T/o8n" '^MISSING +ticket-key gate'
expect protection-404 "$T/o8n" '^MISSING +branch ruleset +no active branch ruleset or protection'
reject protection-404-body "$T/o8n" 'Not Found'
GH_MODE=protection run "$T/r8" "$T/o8p"
expect protection "$T/o8p" '^OK +branch protection \(main\) +required checks: test trivy'
reject protection-trivy-ok "$T/o8p" 'required checks lack'
GH_MODE=ruleset run "$T/r8" "$T/o8r"
expect ruleset "$T/o8r" '^OK +branch ruleset +required checks: cleat enola trivy'

echo "check-project tests: $pass passed, $failn failed"
[ $failn -eq 0 ]
