#!/usr/bin/env bash
# Scaffold check for a code repository wired into the software-factory loop. Run from
# anywhere inside the repo. One line per artifact, exit 1 if a REQUIRED one is absent.
# Read-only. Pair with deploy/02-scaffold-a-project.md, which says how each is created.
#
# Accepted layouts. The factory's reference scaffold is checked as written, but an artifact
# that a working repo keeps elsewhere counts where it really lives:
#   - git hooks are looked up in whatever core.hooksPath names (scripts/git-hooks, .githooks, ...);
#   - the team context binds through the AGENTS.md header OR, for a pre-v0.5 header that has no
#     team-context field, through a read-only store in the memspec binding;
#   - the ledger runs from CI (jira-sync workflow + secrets), from a local script with a
#     committed .jira-sync.toml (agents walk tickets themselves), or from an external poller,
#     proven by the pr-ticket-key status on the last merged PR;
#   - a sensor that is not installed reports once, not once per file, hook and CI job it owns.
set -u
NOTRACKER=0; [ "${1:-}" = "--no-tracker" ] && NOTRACKER=1   # the tracker was skipped as a named shortcut (ADR 0001)
SF_BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
fail=0
ok()   { printf 'OK       %-44s %s\n' "$1" "${2:-}"; }
miss() { printf 'MISSING  %-44s %s\n' "$1" "${2:-}"; fail=1; }
warn() { printf 'OPTIONAL %-44s %s\n' "$1" "${2:-}"; }
skip() { printf 'SKIP     %-44s %s\n' "$1" "${2:-}"; }
f()  { [ -f "$1" ] && ok "$1" "${2:-}" || miss "$1" "${2:-}"; }
fo() { [ -f "$1" ] && ok "$1" "${2:-}" || warn "$1" "${2:-}"; }
g()  { grep -qE "$2" "$1" 2>/dev/null && ok "$1: $3" || miss "$1: $3"; }
ver() { sed -n 's/^context-standard: *\(v[0-9][0-9.]*\).*/\1/p' "$1" 2>/dev/null | head -1; }
# First read-only store path in the memspec binding files (block-scoped: a path counts only
# when its own list entry says writable: false).
ro_store() { awk '/^[[:space:]]*-[[:space:]]/{p=""} /^[[:space:]]*-?[[:space:]]*path:/{sub(/.*path:[[:space:]]*/,""); p=$0}
                  /^[[:space:]]*writable:[[:space:]]*false/{ if (p!="") { print p; exit } }' "$@" 2>/dev/null; }
# Every read-only store path in one binding file.
ro_store_all() { awk '/^[[:space:]]*-[[:space:]]/{p=""} /^[[:space:]]*-?[[:space:]]*path:/{sub(/.*path:[[:space:]]*/,""); p=$0}
                      /^[[:space:]]*writable:[[:space:]]*false/{ if (p!="") print p }' "$@" 2>/dev/null; }
GH=0; command -v gh >/dev/null 2>&1 && gh repo view >/dev/null 2>&1 && GH=1

echo "== knowledge plane (context standard, memory binding)"
# v0.5: the contract is AGENTS.md and CLAUDE.md imports it; a v0.4 repo keeps it in CLAUDE.md.
RF=AGENTS.md
if ! grep -q '<!-- context-standard:begin -->' AGENTS.md 2>/dev/null && grep -q '<!-- context-standard:begin -->' CLAUDE.md 2>/dev/null; then
  RF=CLAUDE.md; warn "AGENTS.md contract (v0.5)" "v0.4 layout, contract in CLAUDE.md: adopt.sh --migrate-rule-file ."
fi
f "$RF"
g "$RF" '<!-- context-standard:begin -->' "managed header (adopt.sh ran)"
binding="$(ro_store .memspec/config.yaml .memspec.yaml)"
if grep -qE 'team-context: [A-Za-z0-9._-]+/[A-Za-z0-9._-]+' "$RF" 2>/dev/null; then
  ok "$RF: team-context wired to an org/repo"
elif ! grep -q '^team-context:' "$RF" 2>/dev/null && [ -n "$binding" ]; then
  ok "team context bound" "read-only store $binding (header predates the team-context field)"
else
  miss "$RF: team-context wired to an org/repo" "adopt.sh --set-team <org>/<team>-team-context ."
fi
if [ "$RF" = AGENTS.md ]; then
  grep -qxF '@AGENTS.md' CLAUDE.md 2>/dev/null && ok "CLAUDE.md: imports AGENTS.md" || miss "CLAUDE.md: imports AGENTS.md" "Claude Code skips AGENTS.md when any CLAUDE.md sits above the repo (adopt.sh --update .)"
fi
f .context-standard.lock
have="$(ver .context-standard.lock)"; cur="$(ver "$SF_BIN/../standard/context-standard/template/AGENTS.md")"
if [ -n "$have" ] && [ -n "$cur" ] && [ "$have" != "$cur" ]; then warn "context-standard version" "$have, current $cur: adopt.sh --update ."
elif [ -n "$have" ]; then ok "context-standard version" "$have"; fi
f docs/standard/agents-core.md "the operating contract, vendored"
if [ -f .memspec.yaml ]; then ok .memspec.yaml "standard pointer"
elif [ -n "$(ro_store .memspec/config.yaml)" ]; then warn .memspec.yaml "standard pointer absent; the engine binding below carries the team store"
else miss .memspec.yaml "standard pointer"; fi
f .memspec/config.yaml "engine binding: team store [ro] + scratch [rw]"
if command -v memspec >/dev/null 2>&1; then
  # A read-only store counts only when it is initialized here AND this repo's binding names it:
  # with no binding, memspec falls back to the user's own config and lists whatever stores that
  # names, which proves nothing about this repo. "(not initialized)" is a layer that resolves
  # nowhere on this machine (a devcontainer mount on a bare host).
  bound="$(ro_store_all .memspec/config.yaml | sed "s#^~#$HOME#; s#/*\$##")"
  live=""
  while IFS= read -r line; do
    path="$(printf '%s\n' "$line" | sed -n 's/.*\[ro\].* — \(.*\) ([0-9][0-9]* items)$/\1/p')"
    [ -n "$path" ] && printf '%s\n' "$bound" | grep -qxF "${path%/}" && { live="$(printf '%s' "$line" | sed 's/^ *//')"; break; }
  done < <(memspec stores 2>/dev/null)
  if [ -n "$live" ]; then ok "memspec stores" "$live"
  elif [ -z "$bound" ]; then miss "memspec stores" "this repo binds no read-only team store (.memspec/config.yaml)"
  else miss "memspec stores" "none of the bound team stores resolves here: $(echo $bound)"; fi
fi
[ -d docs/adr ] && ok "docs/adr/" "$(find docs/adr -maxdepth 1 -name "[0-9]*.md" | wc -l | tr -d " ") records" || miss "docs/adr/" "mine-decision-records"
[ -d .claude/rules ] && ok ".claude/rules/" "$(ls .claude/rules | wc -l | tr -d ' ') rule files" || warn ".claude/rules/" "path-scoped rules (17-onboarding §3)"

echo "== sensors"
CLEAT=0; { [ -f quality.json ] || [ -f quality/bin/gate.py ]; } && CLEAT=1
ENOLA=0; [ -f enola-intent.yaml ] && ENOLA=1
if [ $CLEAT -eq 1 ]; then
  f quality.json "cleat config"
  f quality/bin/gate.py "cleat vendored (attach.py)"
  if [ -f quality/bin/gate.py ]; then python3 quality/bin/gate.py >/dev/null 2>&1 && ok "cleat gate" "green" || miss "cleat gate" "red: run python3 quality/bin/gate.py"; fi
  git check-ignore -q quality/bin/gate.py && miss "quality/bin tracked" "a bin/ ignore rule hides the gate from every worktree" || ok "quality/bin tracked"
else
  miss "cleat (sensor 3)" "not installed: quality.json, its hooks, pre-push and CI job (02-scaffold, sensor 3)"
fi
if [ $ENOLA -eq 1 ]; then
  f enola-intent.yaml "layer declaration"
  f scripts/claude-hooks/enola-stop.sh
  fo .claude/rules/enola.md "architecture rule (enola install)"
  if [ -d .enola ]; then ok ".enola/ baseline" "pinned"; else warn ".enola/ baseline" "first session pins it: enola baseline pin ."; fi
  # Trailing slash: a `.enola/` rule matches only a directory, and the baseline may not exist yet.
  git check-ignore -q .enola/ && ok ".gitignore ignores .enola/" || miss ".gitignore ignores .enola/" "36 MB of snapshots must not be committed"
else
  miss "enola (sensor 4)" "not installed: enola-intent.yaml, its Stop hook and CI job (02-scaffold, sensor 4)"
fi
if [ $CLEAT -eq 1 ] || [ $ENOLA -eq 1 ]; then
  f .claude/settings.json "tracked hooks for the installed sensors"
  [ $CLEAT -eq 1 ] && g .claude/settings.json 'gate.py --guard' "PreToolUse cleat guard"
  [ $CLEAT -eq 1 ] && g .claude/settings.json 'gate.py --hook' "Stop cleat hook"
  [ $ENOLA -eq 1 ] && g .claude/settings.json 'enola-stop.sh' "Stop enola hook"
fi
if [ -f .claude/settings.json ] && python3 -c 'import json,sys; sys.exit(0 if json.load(open(".claude/settings.json")).get("enabledPlugins",{}).get("chisle@chisle") is True else 1)' 2>/dev/null; then
  ok "chisle on for this project" "sensor 2, enabledPlugins in the tracked settings"
else
  miss "chisle on for this project" "enabledPlugins chisle@chisle: true in .claude/settings.json (the install is user scope and off there)"
fi
f .mcp.json "ripwire + enola MCP servers"
fo .claude/rules/ripwire.md "orientation-map rule"

echo "== git hooks and merge authority"
hp="$(git config core.hooksPath || true)"
if [ -n "$hp" ]; then ok "core.hooksPath" "$hp"; HD="${hp%/}"; else miss "core.hooksPath" "git config core.hooksPath scripts/git-hooks"; HD=scripts/git-hooks; fi
[ $CLEAT -eq 1 ] && f "$HD/pre-push" "cleat ratchets + receipts before push"
fo "$HD/commit-msg" "provenance trailer"
fo "$HD/post-commit" "memspec reconciliation"
if git log -1 --format=%B | grep -qE '^Provenance: (human|agent:)'; then ok "provenance trailer on HEAD"; else warn "provenance trailer on HEAD" "absent (hook not installed, or a merge commit)"; fi
# The factory gates a merge on trivy plus every installed sensor; an absent sensor is reported once above.
NEED="trivy"; [ $CLEAT -eq 1 ] && NEED="cleat $NEED"; [ $ENOLA -eq 1 ] && NEED="$NEED enola"
if [ $GH -eq 1 ]; then
  # Required status checks: active BRANCH rulesets (repo and inherited org ones), else classic protection.
  ctx="$(for id in $(gh api 'repos/{owner}/{repo}/rulesets' --jq '.[] | select(.enforcement=="active" and .target=="branch") | .id' 2>/dev/null); do
           gh api "repos/{owner}/{repo}/rulesets/$id" --jq '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context' 2>/dev/null; done | sort -u | tr '\n' ' ')"
  src="branch ruleset"
  if [ -z "$ctx" ]; then
    # Classic branch protection on the default branch carries required checks too.
    db="$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name 2>/dev/null)"
    ctx="$(gh api "repos/{owner}/{repo}/branches/${db:-main}/protection" --jq '.required_status_checks.contexts[]' 2>/dev/null)" || ctx=""   # a 404 body lands on stdout
    ctx="$(printf '%s\n' "$ctx" | sed '/^$/d' | sort -u | tr '\n' ' ')"
    [ -n "$ctx" ] && src="branch protection ($db)"
  fi
  if [ -n "$ctx" ]; then
    ok "$src" "required checks: $ctx"
    missing_ctx=""; for c in $NEED; do case " $ctx " in *" $c "*) ;; *) missing_ctx="$missing_ctx $c" ;; esac; done
    [ -n "$missing_ctx" ] && miss "required gate checks" "required checks lack:$missing_ctx"
  else miss "branch ruleset" "no active branch ruleset or protection with required status checks: gh api repos/{owner}/{repo}/rulesets --input deploy/templates/github/ruleset.json"; fi
fi

echo "== CI and ledger"
# The gate JOBS must exist somewhere under .github/workflows/ (a file name proves nothing).
missing_jobs=""; for j in $NEED; do grep -qE "^  $j:" .github/workflows/*.yml 2>/dev/null || missing_jobs="$missing_jobs $j"; done
if [ -z "$missing_jobs" ]; then ok "gate jobs: $NEED" "in $(grep -lE "^  ($(echo $NEED | tr ' ' '|')):" .github/workflows/*.yml 2>/dev/null | sort -u | tr '\n' ' ')"
else miss "gate jobs" "no workflow defines:$missing_jobs (deploy/templates/github/workflows/gates.yml)"; fi
if [ $NOTRACKER -eq 1 ]; then
  skip "ledger (jira-sync, pr-ticket-key, jira_sync.py, vars)" "--no-tracker: the shortcut must be named in the team repo's ADR 0001"
else
  # Statuses and check runs on the last merged PR's head: what actually gated it, whoever posted it.
  posted=""
  if [ $GH -eq 1 ]; then
    sha="$(gh pr list --state merged --limit 1 --json headRefOid --jq '.[0].headRefOid // empty' 2>/dev/null)"
    [ -n "$sha" ] && posted="$( { gh api "repos/{owner}/{repo}/commits/$sha/status" --jq '.statuses[].context' 2>/dev/null
                                  gh api "repos/{owner}/{repo}/commits/$sha/check-runs" --jq '.check_runs[].name' 2>/dev/null; } | sort -u | tr '\n' ' ')"
  fi
  script=""; for p in scripts/ci/jira_sync.py scripts/jira_sync.py; do [ -f "$p" ] && { script="$p"; break; }; done
  [ -n "$script" ] && ok "jira_sync.py" "$script" || miss "scripts/ci/jira_sync.py" "the ledger script"
  t="$(git ls-files | grep -E '(^|/)test[^/]*jira_?sync[^/]*$|(^|/)[^/]*jira_?sync[^/]*test[^/]*$' | head -1)"
  [ -n "$t" ] && ok "jira_sync tests" "$t" || miss "tests/unit/test_ci_jira_sync.py" "tests for the ledger script"
  if [ -f .github/workflows/jira-sync.yml ]; then
    ok "ledger driver" "CI: .github/workflows/jira-sync.yml"
    if [ $GH -eq 1 ]; then
      for s in JIRA_API_TOKEN JIRA_USER_EMAIL; do gh secret list 2>/dev/null | grep -q "^$s" && ok "secret $s" || miss "secret $s" "gh secret set $s"; done
      gh variable list 2>/dev/null | grep -q '^JIRA_BASE_URL' && ok "variable JIRA_BASE_URL" || miss "variable JIRA_BASE_URL" "gh variable set JIRA_BASE_URL"
      gh variable list 2>/dev/null | grep -q '^JIRA_PROJECT_KEY' && ok "variable JIRA_PROJECT_KEY" || warn "variable JIRA_PROJECT_KEY" "unset = the script's default project key"
    fi
  elif [ -f .jira-sync.toml ]; then
    if grep -qE '^base_url *=' .jira-sync.toml && grep -qE '^project *=' .jira-sync.toml; then
      ok "ledger driver" "local: .jira-sync.toml, agents walk tickets with the script (credentials stay personal)"
    else miss "ledger driver" ".jira-sync.toml lacks base_url or project"; fi
  else
    case " $posted " in
      *" pr-ticket-key "*) ok "ledger driver" "external poller (it posted pr-ticket-key on the last merged PR)" ;;
      *) miss "ledger driver" "no jira-sync workflow, no .jira-sync.toml, no poller status seen (deploy/templates/github/workflows/jira-sync.yml)" ;;
    esac
  fi
  if [ -f .github/workflows/pr-ticket-key.yml ]; then ok "ticket-key gate" ".github/workflows/pr-ticket-key.yml"
  else case " $posted " in
    *" pr-ticket-key "*) ok "ticket-key gate" "pr-ticket-key posted on the last merged PR" ;;
    *) miss "ticket-key gate" "no pr-ticket-key workflow and no such status on the last merged PR" ;;
  esac; fi
fi

echo "== verify gate"
[ -d .claude/rules ] && ls .claude/rules/*.md >/dev/null 2>&1 && ok "rule packs for the reviewer" ".claude/rules/*.md (consort picks them up)" || warn "rule packs" "CONSORT_RULE_PACKS or .claude/rules/"
fo sonar-project.properties "static-analysis leg (else the scan reports SKIPPED)"
fo .gate-receipts/.keep "receipt directory (gitignored contents)"

echo
if [ $fail -eq 0 ]; then echo "project: every REQUIRED artifact present"; else echo "project: REQUIRED artifacts missing (see MISSING lines)"; fi
exit $fail
