#!/usr/bin/env bash
# bash adopt.test.sh — pins adopt.sh's v0.5 layout (AGENTS.md contract + CLAUDE.md
# stub) and its handling of v0.4 repos, against throwaway git repos.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A="$HERE/adopt.sh"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
fails=0
ok()  { echo "ok   $1"; }
bad() { echo "FAIL $1"; fails=$((fails + 1)); }
expect() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

repo() { # repo <dir> — git repo with a vendored agents-core (the source repo is a placeholder)
  mkdir -p "$1/docs/standard" && git -C "$1" init -q
  printf '# agents-core fixture\n' > "$1/docs/standard/agents-core.md"
}
run() { "$A" "$@" > "$W/out" 2>&1; }

# 1. fresh seed → AGENTS.md contract, CLAUDE.md stub, check passes once the team is set
R="$W/fresh"; repo "$R"; run "$R"
expect "seed writes the AGENTS.md sentinel"   'grep -q "context-standard:begin" "$R/AGENTS.md"'
expect "seed pins v0.5 in AGENTS.md"          'grep -q "^context-standard: v0.5" "$R/AGENTS.md"'
expect "seed writes the CLAUDE.md stub"       'grep -qxF "@AGENTS.md" "$R/CLAUDE.md"'
expect "stub carries no sentinel"             '! grep -q "context-standard:begin" "$R/CLAUDE.md"'
run --set-team acme/x-team-context "$R"
expect "set-team writes the key into AGENTS.md" 'grep -q "^team-context: acme/x-team-context" "$R/AGENTS.md"'
expect "set-team wires the team import"       'grep -qxF "@/workspaces/x-team-context/CLAUDE.md" "$R/AGENTS.md"'
expect "check passes on a fresh v0.5 repo"    'run --check "$R"'

# 2. negative control: the stub line removed → check fails
sed -i.bak '/^@AGENTS\.md$/d' "$R/CLAUDE.md"
expect "check fails without @AGENTS.md in CLAUDE.md" '! run --check "$R" && grep -q "lacks the line" "$W/out"'
run --update "$R"
expect "update restores the stub import"      'grep -qxF "@AGENTS.md" "$R/CLAUDE.md" && run --check "$R"'

# 3. a team's own CLAUDE.md (no sentinel) survives seeding below the import
R="$W/own"; repo "$R"; printf 'MY OWN RULE\n' > "$R/CLAUDE.md"; run "$R"
expect "own CLAUDE.md gets the import first"  '[ "$(grep -v "^<!--\|^ *Claude Code\|^$" "$R/CLAUDE.md" | head -1)" = "@AGENTS.md" ]'
expect "own CLAUDE.md content kept"           'grep -qxF "MY OWN RULE" "$R/CLAUDE.md"'
expect "own CLAUDE.md: AGENTS.md seeded"      'grep -q "context-standard:begin" "$R/AGENTS.md"'

# 4. v0.4 layout (contract in CLAUDE.md) → recognised, warned, migrated
R="$W/legacy"; repo "$R"; run "$R"; run --set-team acme/y-team-context "$R"
printf 'TEAM BODY LINE\n' >> "$R/AGENTS.md"
rm "$R/CLAUDE.md"; mv "$R/AGENTS.md" "$R/CLAUDE.md"
git -C "$R" add -A && git -C "$R" -c user.name=t -c user.email=t@t commit -qm v04
run "$R"
expect "seed into v0.4 does not create AGENTS.md" '[ ! -e "$R/AGENTS.md" ] && grep -q "v0.4 layout" "$W/out"'
expect "check passes on v0.4 with a warning"  'run --check "$R" && grep -q "v0.4 layout" "$W/out"'
run --migrate-rule-file "$R"
expect "migrate moves the contract to AGENTS.md" 'grep -q "context-standard:begin" "$R/AGENTS.md" && grep -qxF "TEAM BODY LINE" "$R/AGENTS.md"'
expect "migrate keeps team-context"           'grep -q "^team-context: acme/y-team-context" "$R/AGENTS.md"'
expect "migrate leaves CLAUDE.md as the stub" 'grep -qxF "@AGENTS.md" "$R/CLAUDE.md" && ! grep -q "TEAM BODY LINE" "$R/CLAUDE.md"'
git -C "$R" add -A && git -C "$R" -c user.name=t -c user.email=t@t commit -qm migrate
expect "AGENTS.md history follows into the v0.4 file" '[ "$(git -C "$R" log --follow --format=%s -- AGENTS.md | tail -1)" = v04 ]'
expect "check passes after migrate, no warning" 'run --check "$R" && ! grep -q "v0.4 layout" "$W/out"'

# 5. ambiguous: AGENTS.md without sentinel next to a v0.4 CLAUDE.md → touch nothing
R="$W/ambig"; repo "$R"; run "$R"; rm "$R/CLAUDE.md"; mv "$R/AGENTS.md" "$R/CLAUDE.md"
printf 'someone else\n' > "$R/AGENTS.md"; cp "$R/CLAUDE.md" "$W/c.before"
run --migrate-rule-file "$R"
expect "ambiguous migrate warns and changes nothing" 'grep -q "Merge AGENTS.md" "$W/out" && cmp -s "$R/CLAUDE.md" "$W/c.before" && grep -qxF "someone else" "$R/AGENTS.md"'

# 6. an existing AGENTS.md without the sentinel keeps its text and gains the header
R="$W/ownagents"; repo "$R"; printf 'TEAM AGENTS RULE\n' > "$R/AGENTS.md"; run "$R"
expect "own AGENTS.md gains the sentinel"     'grep -q "context-standard:begin" "$R/AGENTS.md" && grep -qxF "TEAM AGENTS RULE" "$R/AGENTS.md"'
expect "own AGENTS.md: set-team then works"   'run --set-team acme/z-team-context "$R" && run --check "$R"'
expect "rewritten files stay 0644"            '[ "$(stat -f %Lp "$R/AGENTS.md" 2>/dev/null || stat -c %a "$R/AGENTS.md")" = 644 ]'

# 7. migrate brings managed files to the version it stamps into the lock
R="$W/stale"; repo "$R"; run "$R"; run --set-team acme/s-team-context "$R"
rm "$R/CLAUDE.md"; mv "$R/AGENTS.md" "$R/CLAUDE.md"; printf '# stale v0.4 caller\n' > "$R/.github/workflows/docs-lint.yml"
run --migrate-rule-file "$R"
expect "migrate syncs a stale managed file"   'cmp -s "$R/.github/workflows/docs-lint.yml" "$HERE/template/.github/workflows/docs-lint.yml" && run --check "$R"'

# 8. a planted symlink at the old fixed temp name is never written through
R="$W/plant"; repo "$R"; printf 'MINE\n' > "$R/CLAUDE.md"; printf 'OUTSIDE\n' > "$W/outside"
ln -s "$W/outside" "$R/CLAUDE.md.tmp"; run "$R"
expect "no write through a planted .tmp symlink" 'grep -qxF OUTSIDE "$W/outside" && [ "$(wc -l < "$W/outside")" -eq 1 ] && grep -qxF "@AGENTS.md" "$R/CLAUDE.md"'
expect "no temp file left behind"             '[ -z "$(find "$W" -name ".adopt.*")" ]'

# 9. symlinks on any path adopt.sh writes are refused, files and parent dirs alike
for f in AGENTS.md CLAUDE.md; do
  R="$W/sym-$f"; repo "$R"; printf 'OUTSIDE_SECRET\n' > "$W/secret-$f"; ln -s "$W/secret-$f" "$R/$f"
  expect "seed refuses a symlinked $f"         '! run "$R" && grep -q "is a symlink" "$W/out" && [ -L "$R/$f" ]'
done
R="$W/symdir"; repo "$R"; mkdir -p "$W/elsewhere"; ln -s "$W/elsewhere" "$R/docs/adr"
expect "seed refuses a symlinked parent dir"   '! run "$R" && [ -z "$(ls -A "$W/elsewhere")" ]'
R="$W/dangling"; repo "$R"; run "$R"; run --set-team acme/d-team-context "$R"; rm "$R/AGENTS.md"; mkdir -p "$W/nowhere"; ln -s "$W/nowhere/AGENTS.md" "$R/AGENTS.md"
expect "update refuses a dangling AGENTS.md link" '! run --update "$R" && [ ! -e "$W/nowhere/AGENTS.md" ]'

# 10. every managed file is pinned to LF, so a CRLF checkout cannot fake drift
R="$W/lf"; repo "$R"; run "$R"
expect "gitattributes pins each managed file"   'grep -qxF "docs/adr/README.md text eol=lf" "$R/.gitattributes" && grep -qxF ".github/workflows/docs-lint.yml text eol=lf" "$R/.gitattributes"'
run "$R"; expect "gitattributes lines are not duplicated" '[ "$(grep -c "docs/adr/README.md" "$R/.gitattributes")" = 1 ]'

if [ "$fails" -eq 0 ]; then echo "adopt.test.sh: all passed."; else echo "adopt.test.sh: $fails FAILED"; exit 1; fi
