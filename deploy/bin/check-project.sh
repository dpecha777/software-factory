#!/usr/bin/env bash
# Scaffold check for a code repository wired into the software-factory loop. Run from
# anywhere inside the repo. One line per artifact, exit 1 if a REQUIRED one is absent.
# Read-only. Pair with deploy/02-scaffold-a-project.md, which says how each is created.
set -u
NOTRACKER=0; [ "${1:-}" = "--no-tracker" ] && NOTRACKER=1   # the tracker was skipped as a named shortcut (ADR 0001)
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
fail=0
ok()   { printf 'OK       %-44s %s\n' "$1" "${2:-}"; }
miss() { printf 'MISSING  %-44s %s\n' "$1" "${2:-}"; fail=1; }
warn() { printf 'OPTIONAL %-44s %s\n' "$1" "${2:-}"; }
skip() { printf 'SKIP     %-44s %s\n' "$1" "${2:-}"; }
f()  { [ -f "$1" ] && ok "$1" "${2:-}" || miss "$1" "${2:-}"; }
fo() { [ -f "$1" ] && ok "$1" "${2:-}" || warn "$1" "${2:-}"; }
g()  { grep -qE "$2" "$1" 2>/dev/null && ok "$1: $3" || miss "$1: $3"; }

echo "== knowledge plane (context standard, memory binding)"
# v0.5: the contract is AGENTS.md and CLAUDE.md imports it; a v0.4 repo keeps it in CLAUDE.md.
RF=AGENTS.md
if ! grep -q '<!-- context-standard:begin -->' AGENTS.md 2>/dev/null && grep -q '<!-- context-standard:begin -->' CLAUDE.md 2>/dev/null; then
  RF=CLAUDE.md; warn "AGENTS.md contract (v0.5)" "v0.4 layout, contract in CLAUDE.md: adopt.sh --migrate-rule-file ."
fi
f "$RF"
g "$RF" '<!-- context-standard:begin -->' "managed header (adopt.sh ran)"
g "$RF" 'team-context: [A-Za-z0-9._-]+/[A-Za-z0-9._-]+' "team-context wired to an org/repo (not none, not unset)"
if [ "$RF" = AGENTS.md ]; then
  grep -qxF '@AGENTS.md' CLAUDE.md 2>/dev/null && ok "CLAUDE.md: imports AGENTS.md" || miss "CLAUDE.md: imports AGENTS.md" "Claude Code skips AGENTS.md when any CLAUDE.md sits above the repo (adopt.sh --update .)"
fi
f .context-standard.lock
f docs/standard/agents-core.md "the operating contract, vendored"
f .memspec.yaml "standard pointer"
f .memspec/config.yaml "engine binding: team store [ro] + scratch [rw]"
if command -v memspec >/dev/null 2>&1; then
  if memspec stores 2>/dev/null | grep -q '\[ro\]'; then ok "memspec stores" "$(memspec stores 2>/dev/null | grep '\[ro\]' | head -1 | sed 's/^ *//')"; else miss "memspec stores" "no read-only team store resolves from here"; fi
fi
[ -d docs/adr ] && ok "docs/adr/" "$(find docs/adr -maxdepth 1 -name "[0-9]*.md" | wc -l | tr -d " ") records" || miss "docs/adr/" "mine-decision-records"
[ -d .claude/rules ] && ok ".claude/rules/" "$(ls .claude/rules | wc -l | tr -d ' ') rule files" || warn ".claude/rules/" "path-scoped rules (17-onboarding §3)"

echo "== sensors"
f quality.json "cleat config"
f quality/bin/gate.py "cleat vendored (attach.py)"
if [ -f quality/bin/gate.py ]; then python3 quality/bin/gate.py >/dev/null 2>&1 && ok "cleat gate" "green" || miss "cleat gate" "red: run python3 quality/bin/gate.py"; fi
f enola-intent.yaml "layer declaration"
f .claude/settings.json "tracked hooks: cleat guard + stop, enola stop + session-start"
g .claude/settings.json 'gate.py --guard' "PreToolUse cleat guard"
g .claude/settings.json 'gate.py --hook' "Stop cleat hook"
g .claude/settings.json 'enola-stop.sh' "Stop enola hook"
if [ -f .claude/settings.json ] && python3 -c 'import json,sys; sys.exit(0 if json.load(open(".claude/settings.json")).get("enabledPlugins",{}).get("chisle@chisle") is True else 1)' 2>/dev/null; then
  ok "chisle on for this project" "sensor 2, enabledPlugins in the tracked settings"
else
  miss "chisle on for this project" "enabledPlugins chisle@chisle: true in .claude/settings.json (the install is user scope and off there)"
fi
f scripts/claude-hooks/enola-stop.sh
f .mcp.json "ripwire + enola MCP servers"
fo .claude/rules/ripwire.md "orientation-map rule"
fo .claude/rules/enola.md "architecture rule (enola install)"
if [ -d .enola ]; then ok ".enola/ baseline" "pinned"; else warn ".enola/ baseline" "first session pins it: enola baseline pin ."; fi
git check-ignore -q .enola && ok ".gitignore ignores .enola/" || miss ".gitignore ignores .enola/" "36 MB of snapshots must not be committed"
git check-ignore -q quality/bin/gate.py && miss "quality/bin tracked" "a bin/ ignore rule hides the gate from every worktree" || ok "quality/bin tracked"

echo "== git hooks and merge authority"
hp="$(git config core.hooksPath || true)"
[ -n "$hp" ] && ok "core.hooksPath" "$hp" || miss "core.hooksPath" "git config core.hooksPath scripts/git-hooks"
f scripts/git-hooks/pre-push "cleat ratchets + receipts before push"
fo scripts/git-hooks/commit-msg "provenance trailer"
fo scripts/git-hooks/post-commit "memspec reconciliation"
if git log -1 --format=%B | grep -qE '^Provenance: (human|agent:)'; then ok "provenance trailer on HEAD"; else warn "provenance trailer on HEAD" "absent (hook not installed, or a merge commit)"; fi
if command -v gh >/dev/null 2>&1 && gh repo view >/dev/null 2>&1; then
  # An active BRANCH ruleset whose required status checks name the three gate jobs; any other
  # ruleset (a tag rule, a push rule, a ruleset missing a gate) does not count.
  ctx="$(for id in $(gh api 'repos/{owner}/{repo}/rulesets' --jq '.[] | select(.enforcement=="active" and .target=="branch") | .id' 2>/dev/null); do
           gh api "repos/{owner}/{repo}/rulesets/$id" --jq '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context' 2>/dev/null; done | sort -u | tr '\n' ' ')"
  missing_ctx=""; for c in cleat enola trivy; do case " $ctx " in *" $c "*) ;; *) missing_ctx="$missing_ctx $c" ;; esac; done
  if [ -n "$ctx" ] && [ -z "$missing_ctx" ]; then ok "branch ruleset" "required checks: $ctx"
  elif [ -n "$ctx" ]; then miss "branch ruleset" "required checks lack:$missing_ctx (have: $ctx)"
  else miss "branch ruleset" "no active branch ruleset with required status checks: gh api repos/{owner}/{repo}/rulesets --input deploy/templates/github/ruleset.json"; fi
fi

echo "== CI and ledger"
# All three gate JOBS must exist somewhere under .github/workflows/ (a file name proves nothing).
missing_jobs=""; for j in cleat enola trivy; do grep -qE "^  $j:" .github/workflows/*.yml 2>/dev/null || missing_jobs="$missing_jobs $j"; done
if [ -z "$missing_jobs" ]; then ok "gate jobs cleat, enola, trivy" "in $(grep -lE '^  (cleat|enola|trivy):' .github/workflows/*.yml 2>/dev/null | sort -u | tr '\n' ' ')"
else miss "gate jobs" "no workflow defines:$missing_jobs (deploy/templates/github/workflows/gates.yml)"; fi
if [ $NOTRACKER -eq 1 ]; then
  skip "ledger (jira-sync, pr-ticket-key, jira_sync.py, vars)" "--no-tracker: the shortcut must be named in the team repo's ADR 0001"
else
  f .github/workflows/jira-sync.yml
  f .github/workflows/pr-ticket-key.yml
  f scripts/ci/jira_sync.py
  f tests/unit/test_ci_jira_sync.py
  if command -v gh >/dev/null 2>&1 && gh repo view >/dev/null 2>&1; then
    for s in JIRA_API_TOKEN JIRA_USER_EMAIL; do gh secret list 2>/dev/null | grep -q "^$s" && ok "secret $s" || miss "secret $s" "gh secret set $s"; done
    gh variable list 2>/dev/null | grep -q '^JIRA_BASE_URL' && ok "variable JIRA_BASE_URL" || miss "variable JIRA_BASE_URL" "gh variable set JIRA_BASE_URL"
    gh variable list 2>/dev/null | grep -q '^JIRA_PROJECT_KEY' && ok "variable JIRA_PROJECT_KEY" || warn "variable JIRA_PROJECT_KEY" "unset = the script's default project key"
  fi
fi

echo "== verify gate"
[ -d .claude/rules ] && ls .claude/rules/*.md >/dev/null 2>&1 && ok "rule packs for the reviewer" ".claude/rules/*.md (consort picks them up)" || warn "rule packs" "CONSORT_RULE_PACKS or .claude/rules/"
fo sonar-project.properties "static-analysis leg (else the scan reports SKIPPED)"
fo .gate-receipts/.keep "receipt directory (gitignored contents)"

echo
if [ $fail -eq 0 ]; then echo "project: every REQUIRED artifact present"; else echo "project: REQUIRED artifacts missing (see MISSING lines)"; fi
exit $fail
