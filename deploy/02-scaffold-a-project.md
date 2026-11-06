# Scaffold a project: the agent runbook

This document is a brief for an agent. Hand it over as the task ("read
`deploy/02-scaffold-a-project.md` and run it against `<code repo>`") or drive it yourself
leg by leg. It wires one code repository, its team-context repository, the ticket ledger and
the PM workspace into the loop the reference implementation runs, and it stops for a person at
exactly the points where the design says a person decides.

It does not repeat the design. Each leg names the flightlist row it satisfies
([docs/18](../docs/18-flightlist.md)) and the document that says why. The Day 1 knowledge-plane
work (specs, decision records) is [docs/17](../docs/17-onboarding.md) and is pointed to, not
copied. When a leg here and the design disagree, the design wins and this file gets a fix.

Rules for the agent running it:

- **Isolate first.** Every mutating git operation happens in a worktree you created for this
  run, never in a shared checkout ([docs/08](../docs/08-sandbox-and-isolation.md)).
- **One check per leg, run fresh, output kept.** A leg is done when its check passed in this
  session and the evidence pointer is written into the run record (section R).
- **Ask the human the questions in section 0 once, up front.** Everything else that needs a
  person is marked **Human** and is a stop, not a guess.
- **Never push, merge or release.** You open PRs; a person merges. A handoff may instruct a
  verify, never a merge ([adr/0006](../adr/0006-pr-gated-output-human-release.md)).
- **Run `deploy/bin/check-workstation.sh` before anything.** A missing binary found at leg G4
  is an hour lost. Fix the machine with [01-workstation-macos.md](01-workstation-macos.md) first.

Paths below assume this repository is cloned at `~/git/software-factory`; adjust if not.
`$SF` means that path, `$REPO` the code repository being wired, `$TEAM` its team-context
repository, `$PM` the PM workspace directory.

## 0. Inputs to collect from the human

Ask these together, record the answers at the top of the run record, and do not start a leg
whose input is blank.

| Input | Example from the reference implementation | Used by |
|---|---|---|
| Code repository (org/repo, default branch) | `siimvene/kvart`, `main` | everything |
| Team-context repository name (org/repo); create it, or it exists | `siimvene/kvart-team-context` | D0.1, D0.3, D0.5 |
| Code owner (GitHub handle or team) for `specs/**` and `.memspec/**` | the owner | D0.1, D0.2 |
| Business-truth reviewer for the spec and ADR candidate tables | the owner, in the PM role | D1 (docs/17) |
| Ticket tracker: Jira site URL and project key, or "none" (a named shortcut) | a Jira Cloud site, `KVART` | M4, G6 |
| The stack's test command, coverage report path, and the module layers outermost-first | pytest with `coverage.xml`; entry, service, domain, models, foundation | G4, CI |
| Money or otherwise high-consequence paths, if any | billing engine, payment rails | P2 (a surface file) |
| PM workspace location and the PM's machine | `~/git/<product>-pm` | M0 |
| Bot identity: may a GitHub App be created on the org (needs an admin)? | `kvart-factory`, contents + pull-requests write | G6, S2 |
| Supervision level for the first cycles | interactive on the operator's machine | P5 |
| Reviewer route | reference Vertex, or existing local Pi with explicit provider and model ids | G1 to G3, factory-reviewer-setup |
| Consort root the caller will invoke | `~/git/consort` at `5f68ef6`, or the installed plugin scripts directory | G1 to G3 |
| Caller that will run the panel | a Claude session that inherits user-scope env, or a shell with the same exports | G1 to G3 |

## D0. Repositories

### D0.1 Team-context repo (Agent)

```
gh repo create <org>/<team>-team-context --private --clone && cd <team>-team-context
cp $SF/deploy/standard/templates/team-context/{CLAUDE.md,CODEOWNERS} .
mkdir -p specs docs/adr && cp $SF/templates/adr.md docs/adr/0000-template.md
memspec init . --force                      # lays out .memspec/; the store the code repos read
```

`--force` because the repo sits under the home directory, whose `~/.memspec` (workstation guide
section 2) memspec would otherwise treat as this repo's store and refuse to nest under.

Fill `CLAUDE.md` from the interview (the template's example file shows what good looks like:
`EXAMPLE-CLAUDE.md` beside it; copy the template, not the example). Put the real owner into
`CODEOWNERS`; a placeholder there plus branch protection makes the gated paths unmergeable.
Write `docs/adr/0001-<shortcuts>.md` from `$SF/templates/adr.md`: every leg this run skips goes
in there the day it is skipped, and the reference implementation's first ADR is the model
(kvart-team-context ADR 0001: self-review as code-owner review, no Jira at first, specs per
subdomain when first touched; two of the three were closed within a day and the ADR says so).

Check: `ls CLAUDE.md CODEOWNERS docs/adr/0000-template.md docs/adr/0001-*.md .memspec/config.yaml`
lists five files and `grep -c '@' CODEOWNERS` is above zero with no `<` placeholder. Commit,
push the branch, open the PR; the owner merges.

### D0.2 Branch protection on the team repo (**Human**)

```
gh api -X PUT repos/<org>/<team>-team-context/branches/main/protection \
  --input - <<'EOF'
{"required_status_checks":null,"enforce_admins":true,"restrictions":null,
 "required_pull_request_reviews":null}
EOF
```

Under adr 0011 the team-context repo is agent-managed and its PRs auto-merge, so it carries **no
required review** (`required_pull_request_reviews: null` above) - a required code-owner review would
physically block the auto-merge. `enforce_admins` and status checks stay. A code repository is the
opposite case and keeps `require_code_owner_reviews: true`.

Graduation PRs into the context repo are PR-only by default (adr 0018): the repo carries a
`.graduation.yml` (`merge: pr-only`) and a CODEOWNERS file naming who reviews them, and its default
branch requires the repo's check status (`required_status_checks: {"strict":false,"contexts":["<check>"]}`
in the call above), so a client that still merges on open is refused and the PR
waits for a code owner. Review stays requested, not required, for the reasons above.

Check: the same endpoint with GET returns `required_pull_request_reviews: null` on the context repo. Where the plan
refuses (HTTP 403 on a free private repo, as kvart hit on 2026-09-07), write the refusal into
ADR 0001 with the date and move on: the gate is a habit until the plan changes.

### D0.3 Adopt the context standard in the code repo (Agent)

In a worktree of `$REPO` on a branch `chore/adopt-context-standard`:

```
$SF/deploy/standard/context-standard/adopt.sh --dry-run .          # read what it will write
$SF/deploy/standard/context-standard/adopt.sh .
$SF/deploy/standard/context-standard/adopt.sh --set-team <org>/<team>-team-context .
$SF/deploy/standard/context-standard/adopt.sh --check .
```

The script seeds the contract in `AGENTS.md` (sentinel header plus team body) and a tracked
`CLAUDE.md` stub whose line `@AGENTS.md` is how Claude Code reaches it (standard v0.5; a v0.4
repo with the contract in `CLAUDE.md` moves with `--migrate-rule-file`). An existing `CLAUDE.md`
keeps its lines below the import; move the repo rules out of it into `AGENTS.md`. It vendors `docs/standard/agents-core.md` (the
operating contract; never edited in the repo), writes `.context-standard.lock`, the
`.memspec.yaml` pointer and skeleton docs. Fill the seeded `{{PLACEHOLDERS}}` from the existing
documentation, not from memory, and mark seeded docs "for L1 review".

If the repo gitignores `CLAUDE.md` or `AGENTS.md` as personal files, un-ignore both, ignore
`CLAUDE.local.md` instead, and tell every developer to run `mv CLAUDE.md CLAUDE.local.md` (and to move a personal
`AGENTS.md` aside) before pulling the adoption: git overwrites an ignored file without asking when a tracked one arrives
`[measured 2026-11-05]`.

Then bind the memory engine, which reads its own file rather than the standard's pointer:

```
mkdir -p .memspec && cp $SF/deploy/templates/memspec/config.yaml .memspec/config.yaml   # edit the team path
cp $SF/deploy/templates/memspec/memspec.yaml .memspec.yaml                              # edit the team name
printf '.memspec/*\n!.memspec/config.yaml\n' >> .gitignore
```

Check: `adopt.sh --check .` exits 0; `memspec stores` run in the repo lists the team store
`[ro]` and the scratch store `[rw]` (D0.5 is folded in here for a repo that never carried its
own store; a repo that did follows [docs/17 §4](../docs/17-onboarding.md) and subtrees it into
the team repo first). The seeded `docs-lint` workflow calls a reusable workflow in the group's
private repository; if this repo cannot reach it, disable the workflow and record that in the
code repo's ADR 0001, as kvart did.

### D0.4 Split the instructions file (Agent, owner reads)

Only if `CLAUDE.md` is one large block. Procedure and the kvart numbers:
[docs/17 §3](../docs/17-onboarding.md). Check: every rule file's `paths:` globs match at least
one file (`git ls-files | grep -E '<glob as regex>'` per rule), and one stale rule found and
fixed is the expected result, not a surprise.

### D0.6 and M0. The PM workspace (Agent, then the PM)

On the PM's machine, or your own for a solo owner, after the PM profile of
[01-workstation-macos.md](01-workstation-macos.md) passed:

```
mkdir -p $PM && cd $PM && git init
claude   # in $PM:  /pm-workspace-setup .
```

The plugin's setup skill writes the folder layout, `CLAUDE.md`, `CONVENTIONS.md`, the registers,
`POINTERS.md`, `SENSITIVITY.md` and `TRACKER.md`. Its repository discovery reads through a hosted
GitHub connector and leaves `POINTERS.md` blank when that connector is absent; the PM profile
reads local clones instead (decided 2026-09-15), so the engineer fills the file. Clone read-only
next to `$PM`: the team-context repo and each code repo, with a token that cannot push (a
fine-grained token with contents read, or the PM's own account with no write access on those
repos). Then:

- `POINTERS.md`: one entry per clone with its local path, its `org/repo` slug and what it
  answers; written by you, not by the skill's discovery.
- `SENSITIVITY.md`: the tier; default Sensitive, which means generic topics only leave the
  machine.
- `TRACKER.md`: project key, issue types, the folder-to-epic mapping, the label table. Filled
  once, corrected from ticket previews, never asked twice.
- The five skills the reference run added on top of the plugin's, if the plugin version
  installed lacks them: copy from `$SF/templates/skills/{ticket,readiness-evaluator,task-improver,task-splitter,graduate}`
  into `$PM/.claude/skills/`. Version 1.6.0 of the plugin, vendored here, carries all five.

Check: run the ticket skill once against a real spec before trusting anything else
(`/ticket <features file>`), and read the draft. kvart's first run found the skill citing a
style file the copy did not have; that class of defect only shows on a run.

## G. Gate wiring, in the code repo

All of G runs in one worktree on one branch (`chore/quality-gates`), lands as one PR the owner
reads with the settings diff in front of them, because the tracked settings file is a
supply-chain tripwire.

### G4 Sensor stack (Agent wires, **Human** baselines)

```
# sensor 3: cleat, vendored into the repo
python3 ~/git/cleat/quality/bin/attach.py --into . --dry-run
python3 ~/git/cleat/quality/bin/attach.py --into .
```

Attach writes `quality/`, `quality.json`, the baselines and a block into the instructions file.
Then edit `quality.json` by hand, with [templates/sensor-config-examples.md](../templates/sensor-config-examples.md)
open: add `skip_dirs` for the runtime clutter (`.claude`, `.enola`, `.nodeterm`, `tmp`, the
build outputs), because cleat's walkers prune by name and read nested worktrees otherwise
(kvart went 3 of 6 gates red in the primary checkout until this was done); set the
`complexity.tool` to `lizard` with the `exclude` list and a `_note` per exclusion; set
`changed_coverage.report` to the stack's report path and `base_ref` to `origin/main`; give the
documents an agent reads a token ceiling. Do not pass `--git-hooks`: this repo uses
`core.hooksPath`, under which `.git/hooks` is ignored, and the tracked pre-push below already
runs the gate.

```
# sensor 4: enola, with the layer declaration
enola install --targets=claude .            # writes .claude/rules/enola.md; agents target overflows AGENTS.md ceilings
$EDITOR enola-intent.yaml                   # the layers from section 0, outermost first; shape in templates/sensor-config-examples.md §2
printf '.enola/\n' >> .gitignore            # 36 MB of snapshots, machine-local
enola baseline pin . && enola check --fail-on=layers,cycles,intent .
# sensor 1: ripwire, rule file and MCP server
cp $SF/deploy/templates/claude/rules/ripwire.md .claude/rules/ripwire.md
cp $SF/deploy/templates/claude/mcp.json .mcp.json
# sensor 2: chisle enabled per project (installed at user scope, see the workstation guide); and the hooks that make 3 and 4 gates
cp $SF/deploy/templates/claude/settings.json .claude/settings.json
mkdir -p scripts/claude-hooks && cp $SF/deploy/templates/claude-hooks/enola-stop.sh scripts/claude-hooks/
```

Read the settings file you just copied: a PreToolUse guard that refuses edits to the gate
policy, a Stop hook that runs the ratchets on changed files and then the architecture check,
a SessionStart hook for the architecture snapshot, `chisle` enabled from a marketplace pinned
to tag v3.0.0 (the install itself is user scope and switched off there; a project-scope install would
bind to this directory and miss every worktree). Every entry is PATH-guarded so it is a no-op where a binary is absent. Make sure
`.gitignore` tracks `.claude/settings.json`, `.claude/rules/` and any skill you want every
worktree to have, and ignores the rest of `.claude/` (kvart's pattern: `.claude/*` then
`!.claude/rules/`, `!.claude/settings.json`).

Then the git hooks:

```
mkdir -p scripts/git-hooks
cp $SF/deploy/templates/git-hooks/{pre-push,post-commit,commit-msg,README.md} scripts/git-hooks/
git config core.hooksPath scripts/git-hooks   # per clone; the README says so
```

The pre-push runs the cleat gate (coverage gate only when a fresh report exists) and the
receipt checks; the commit-msg hook requires a `Provenance:` trailer; the post-commit surfaces
memory records the commit touched. `pre-commit.example` is the reference stack's staged-file
tripwire (lint, single migration head, staged tests); port it to your stack or leave it out.

Check, in this order:

1. `python3 quality/bin/gate.py` is green in the worktree **and** in the primary checkout with
   its real clutter (the second is the one that found the walker defect).
2. Plant a `# type: ignore` (or the stack's equivalent) in a source file, run the gate, see
   `FAIL escapes` naming the file and line, remove it.
3. Ask the agent to edit a baseline; the guard refuses. Run `gate.py --tighten` if the gate
   says the baseline is looser than the code; it only ever writes a lower number.
4. Plant an import from a lower layer to a higher one; `enola check` exits 1; remove it.
5. `git commit` without the trailer is refused; with `Provenance: agent:<name>` it lands.
6. **Human:** re-cut the baselines on main, naming the accepted sites in the commit message.
   This is the one step an agent must not do; the guard enforces it.

Evidence: the settings diff, the two gate outputs, one line per planted failure.

### G1 to G3 The verify gate (Agent)

Nothing to install in the repo beyond rule packs. Consort picks up `.claude/rules/*.md` as the
reviewer's brief when `CONSORT_RULE_PACKS` is unset, and an organisation's adopted packs come
with the `rule-packs` plugin (it ships one example pack; replace it with your own). Keep reviewer env out of tracked project settings. Follow
[factory-reviewer-setup](../templates/skills/factory-reviewer-setup/SKILL.md) for the route
choice, then the workstation guide sections 3 and 7 for the machine-side keys. Use the Consort
root and caller recorded in section 0. A shell panel does not read Claude settings.

Prove it here, on this repo's first real diff (the G4 branch is a fine subject). Export the same
env the caller will use. `$CONSORT_ROOT` is that recorded checkout or plugin scripts parent.

Vertex route:

```
bash "$CONSORT_ROOT/scripts/consort-panel.sh" origin/main
bash "$CONSORT_ROOT/scripts/consort-scan.sh" .
CONSORT_REVIEWERS=codex,pi:google-vertex:this-model-does-not-exist CONSORT_GCP_PROJECT=does-not-exist bash "$CONSORT_ROOT/scripts/consort-panel.sh" origin/main; echo "exit=$?"
```

Local Pi route. Do not export `CONSORT_GCP_PROJECT`. Do not invent `CONSORT_PI_BIN`.

```
bash "$CONSORT_ROOT/scripts/consort-panel.sh" origin/main
bash "$CONSORT_ROOT/scripts/consort-scan.sh" .
CONSORT_REVIEWERS='codex,pi:<provider-id>:this-model-does-not-exist' bash "$CONSORT_ROOT/scripts/consort-panel.sh" origin/main; echo "exit=$?"
```

Check. The first run produces two findings files with one `[label] started` line each and a
wall-clock proportional to the diff. The fail-closed run exits 3 (a syntactically valid leg
failed at runtime). Exit 2 for malformed configuration is not that test. The gate must not
return 0 with one leg dropped. Then the blind security side-pass. Spawn consort's
`agents/security-reviewer` brief in a fresh session with no context from this one, on the same
diff, and plant one fake credential in a scratch file first. The plant must be found. Record
both outputs. The design's three axes and the no-re-run rule are in
[docs/06](../docs/06-verify-gate.md).

### G5 Receipt-checked pre-push gates (Agent, later)

The browser pass and the static-analysis receipt are project-specific scripts in the reference
implementation (`scripts/e2e-gate.sh`, `scripts/sonar-gate.sh`, receipts under
`.gate-receipts/` keyed by tree id). They are not templated here because their scope maps are
the project's own route and module tables. Wire them at the first UI cycle, following
[docs/06 §Receipt-checked](../docs/06-verify-gate.md); until then, `mkdir -p .gate-receipts`
and ignore its contents.

### G6 and S2 Merge authority and the bot identity (Agent prepares, **Human** grants)

CI first, so the required checks exist before the ruleset names them:

```
mkdir -p .github/workflows && cp $SF/deploy/templates/github/workflows/gates.yml .github/workflows/
```

`gates.yml` carries the three gate jobs with stable names (`cleat`, `enola`, `trivy`). The
project's own lint and test jobs live in its `ci.yml`, also with stable names, and the test job
uploads its coverage report as the `backend-coverage` artifact if the changed-coverage gate is
to run in CI. Edit `templates/github/ruleset.json` so `required_status_checks` names exactly
the jobs that exist, then:

```
gh api repos/<org>/<repo>/rulesets --input $SF/deploy/templates/github/ruleset.json
```

The bot identity is a GitHub App on the org: permissions contents write and pull-requests
write, nothing else, installed on the code repos; its id and private key go into the repo
secrets (`<NAME>_APP_ID`, `<NAME>_APP_PRIVATE_KEY`) for the workflows that open PRs, and the
key file stays on the administering engineer's machine, mode 600. An admin creates it; you
write the request with the exact permission list and stop.

Check, after the first PR exists: a direct push to main by the owner is refused; a direct push
by the App is refused; a PR opened by the App triggers the required checks (a PR opened with the
workflow token would not). kvart's ruleset refused both on 2026-09-08; that refusal is the
evidence line.

### M4 The ticket ledger (Agent, **Human** for the tracker admin steps)

Skip with a named shortcut if the tracker answer in section 0 was "none"; the project checker
then runs with `--no-tracker`.

Tracker side, once per project, by someone with Jira admin. The workflow is six statuses in a
chain, Backlog, Ready, In Progress, In Test, Ready for LIVE, Done, with three loopbacks (In
Test back to In Progress, Ready for LIVE back to In Progress, Ready back to Backlog).
`templates/jira/workflow_payload.json` is the bulk-create body the reference project used; the
status references inside it are UUIDs the site issues, so create the statuses first
(`POST /rest/api/3/statuses`), substitute the references, then `POST /rest/api/3/workflows/create`,
a workflow scheme, the project, and reassign the scheme to the project. Two things the API does
not do and a person does in the UI: the board's column mapping, and the **Resolution** field on
the Done transition (a post-function `update-field Resolution=Done`; without it every Done
ticket reads Unresolved, as kvart's did until 2026-09-09).

Repo side:

```
mkdir -p scripts/ci tests/unit
cp $SF/deploy/templates/ci/jira_sync.py scripts/ci/ && cp $SF/deploy/templates/ci/test_ci_jira_sync.py tests/unit/
cp $SF/deploy/templates/github/workflows/{jira-sync.yml,pr-ticket-key.yml} .github/workflows/
gh variable set JIRA_BASE_URL --body https://<site>.atlassian.net
gh secret set JIRA_USER_EMAIL && gh secret set JIRA_API_TOKEN          # a service account's token, not a person's, where one exists
gh variable set JIRA_PROJECT_KEY --body <KEY>                          # both workflows pass it to jira_sync.py; default KVART
```

`jira_sync.py` is stdlib-only and unit-tested; its docstring is the contract (pickup stamps the
assignee and walks to In Progress, PR open moves to In Test, a green `ci` run to Ready for LIVE,
a red one back, merge forward, deploy to Done, and every transition planned from the current
status so replays are no-ops). The workflows always run main's copy of the script, never the
PR's. `pr-ticket-key` refuses a PR whose branch or title names no ticket unless the `no-ticket`
label is present; the ledger opens at pickup, at the head of the work
([docs/03](../docs/03-operating-contract.md)).

Check: `uv run pytest tests/unit/test_ci_jira_sync.py -q` passes; `jira whoami` (the wrapper
from the workstation guide) prints the account; on the first PR the ticket moves to In Test
within a minute of the PR opening, and the transition log on the ticket names the PR.

## D1. Day 1: the knowledge plane

This one is a whole document rather than a leg. Run [docs/17](../docs/17-onboarding.md) sections 5 to
8 with the skills in `$SF/templates/skills/` (or the `spec-repos` plugin from the marketplace,
which is where they came from): feature maps, the candidate table, the **human** review for
business truth, the spec pairs, `check-specs.py` exit 0, the findings file, the ADR candidate
table, the records. Record the wall-clock; kvart's was one long session for about 250 features.

## T. Test the test, then verify on arrival

Flightlist G7. Every gate made to fail once, in this run, with the red observed:

| Gate | Plant | Expected |
|---|---|---|
| escapes (cleat) | a suppression comment in a source file | `FAIL escapes` with file and line |
| guard (cleat) | ask the agent to edit `quality/*-baseline.json` | the PreToolUse guard refuses |
| layers (enola) | an import from a lower layer to a higher | `enola check` exit 1; the Stop hook blocks once |
| provenance | a commit without the trailer | commit-msg refuses |
| ticket key | a PR from a branch with no key and no label | `pr-ticket-key` red |
| panel hard-fail | one leg pointed at nothing | panel exit 3 |
| security side-pass | one fake credential in the diff | found |
| merge authority | `git push origin HEAD:main` from the owner | refused by the ruleset |

Then, in a fresh session, before trusting any of it:

```
bash $SF/deploy/bin/check-project.sh                # in the code repo: every REQUIRED line OK (--no-tracker if M4 was skipped)
memspec stores | head -2                            # team [ro] N items, scratch [rw]
python3 quality/bin/gate.py                         # green
enola check --fail-on=layers,cycles,intent .        # exit 0
gh api repos/<org>/<repo>/rulesets --jq '.[].enforcement'   # active
gh pr list -R <org>/<team>-team-context --state open        # nothing left unmerged from Day 0
```

## R. The run record

Write `docs/factory-setup-<date>.md` in the team-context repo (through a PR), one row per leg
above: leg id, ticked or skipped, the evidence pointer (commit, PR, command output line), the
wall-clock. Skipped legs also go into ADR 0001 the same day. This file is what the next machine
and the next engineer read first, and it is what turns this runbook from one person's habits
into a design that reproduced. The reference implementation's equivalent is the flightlist
itself; a second project's record is what the flightlist's `proposed` class is waiting for.
