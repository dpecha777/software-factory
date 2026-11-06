# Changelog

## 0.2.22 (2026-11-06)

The repo contract moves to `AGENTS.md`, which every agent tool reads, behind a `CLAUDE.md` stub
that Claude Code needs because it reads `AGENTS.md` only as a fallback (adr 0019).

- `deploy/standard/context-standard/`: v0.5. `template/AGENTS.md` holds the sentinel and body,
  `template/CLAUDE.md` is the `@AGENTS.md` stub (new `stub` class in MANIFEST). `adopt.sh` seeds
  both, prepends the import to an existing `CLAUDE.md`, migrates a v0.4 `CLAUDE.md` contract with
  `--migrate-rule-file`, and `--check` fails a missing import and warns on v0.4. New
  `adopt.test.sh` (32 cases, a missing import among them). adopt.sh refuses any symlink on a
  path it writes (parent directories included) and rewrites through a `mktemp` file, never a
  fixed `.tmp` name; every managed file is pinned to LF in `.gitattributes`. STANDARD §2/§4, VERSIONING, the
  distribution note, the seeded ADR 0001 (pointer topology, v0.5) and `docs-lint.yml` paths follow.
- `deploy/bin/check-project.sh`: checks the contract in `AGENTS.md` plus the stub import, and
  reports a v0.4 layout with the migration command.
- `deploy/02-scaffold-a-project.md`: D0.3 describes the v0.5 seed; the two worked-around seed
  defects are gone, replaced by the gitignored-`CLAUDE.md` step. `deploy/README.md` drops both
  rows and names v0.5.

## 0.2.21 (2026-10-29)

The vendored PM plugin catches up with its source again, so a PM following the workstation guide
gets the product-context-repository offer.

- `deploy/marketplace/plugins/pm-workspace/`: re-vendored at the group catalog's `main` @
  `ff7c175` (1.9.1, conventions 2.8.1): setup discovers the organisation's `<product>-context`
  repositories and offers them for `POINTERS.md`; graduation opens the PR and stops unless the
  target repo's `.graduation.yml` opts in to auto-merge (adr 0018). The source verbatim plus the
  two-step scrub, eleven lines and nothing else (1.9.1 already dropped the example repository
  name that 1.8.0 needed scrubbed). The marketplace index entry and the pin table follow.
- `deploy/01-workstation-macos.md`, `STATUS.md`: name 1.9.1.

## 0.2.20 (2026-10-18)

Two gaps found by reading against the design: the reviewer is never handed the code a change
affects, and a repository-wide mechanical change has no lane of its own. Both proposed.

- `adr/0016`: a script computes the affected modules from the changed symbols plus a declared
  `seams.yaml` (dispatch, registrations, shared tables, whole-tree fences); every leg gets the set
  as a pack and owes one evidenced verdict per module; the gate refuses a module no repo-reading
  leg checked, with a citation inside that module and outside the diff; the set is bound to the
  panel's base and head; escapes add seams; CI test selection reads the same file.
- `adr/0017`: a `mechanical` ticket class; the builder writes a codemod recipe with its tests;
  the PR is recipe, recipe output, hand edits; a script re-runs the recipe on commit 2's parent
  and requires a byte-identical result, a residual query at 0 and the full suite; the panel reviews
  the recipe and a sampled output; a moved base is a re-run of the recipe and of every check,
  never a hand-resolved conflict. Both revised after a two-leg panel (Codex 3, Gemini 4 findings).
- `evidence/field-evidence.md`: §9 deterministic refactoring for agents, §10 Ponytail 5's
  caller-reading review, each with its caveats.
- `adr/README.md`, `STATUS.md`: the rows.

## 0.2.19 (2026-10-18)

The workstation guide moves to memspec 0.12.3, which honours `CLAUDE_CONFIG_DIR` and takes the
store path positionally, so the 0.11.0 workarounds from 0.2.18's contributed fix come out.

- `deploy/01-workstation-macos.md`: sections 2 and 9 pin memspec 0.12.3 and run
  `memspec init ~/.memspec` (hooks land in `$CFG`; `.mcp.json` lands inside the store, not the
  home directory, and the `jq` line drops its memspec entry). The hand-copied hook install for a
  second config directory is gone: the init line runs once per `CLAUDE_CONFIG_DIR` and repoints
  an old `~/.claude` registration. `CLAUDE_CONFIG_DIR` must be absolute. Section 3 notes that
  Consort 0.13.1 finds the Codex plugin under `CLAUDE_CONFIG_DIR`; the pin stays at 5f68ef6. Known
  traps rewritten. The `--min-release-age=0` paragraph no longer claims the flag lifts the gate
  for memspec alone: it drops it for the whole dependency tree, which is stated and accepted.
- `deploy/02-scaffold-a-project.md`: the team-context repo's `memspec init .` gains `--force`.
  On a workstation that followed section 2 the repo sits under the home store, and init refuses
  to nest a store without it (rehearsed on 0.12.3); 0.11.0 refused the positional path as well.
- `deploy/bin/check-workstation.sh`: hook commands are split like a shell would, so a quoted
  path with a space (`Application Support`) or memspec's single-quoted form is recognised, and
  so is an exec-form entry (`command` plus `args`); the old split broke such paths and reported
  `not registered`. Hints name the new init line. With `CLAUDE_CONFIG_DIR` set, a memspec older
  than 0.12.3 is an OPTIONAL warning.
- `deploy/bin/test_check_workstation.py`: the fixture's config directory has a space in it;
  three new cases (single-quoted form, exec form, old memspec version). 54 tests.

## 0.2.18 (2026-10-17)

The vendored PM plugin catches up with its source, and the tracker skill stops being "not here".

- `deploy/marketplace/plugins/pm-workspace/`: re-vendored at the group catalog's `main` @
  `9c32239` (1.8.0, conventions 2.7.0): the new `apply` skill, per-project `TRACKER.md` blocks,
  `project:` front matter, the development and owner-authorised write remotes, the setup upgrade
  notice. The previous copy had been edited in place after vendoring (`a74fdbd`, `cead07b`) and
  matched neither 1.7.0 commit of its source; this one is the source verbatim plus the two-step
  scrub, twelve lines and nothing else. The marketplace index entry and the pin table follow; the
  pin table also stops counting `rule-packs`, which is written here, as vendored.
- `README.md`, `docs/14-pm-surface.md`, `templates/skills/README.md`, `STATUS.md`: `apply` as the
  shipped write path of `tracker-mcp` `[designed]`; the catalogue count corrected to nineteen.

## 0.2.17 (2026-10-01)

Merge on green leaves the reference design: it is the operator's local practice, and at the
reference level the owner merges (adr 0006).

- `adr/0014-agents-merge-on-green-in-the-operators-own-repositories.md`: rejected, withdrawn the
  day after 0.2.16 merged it. The file stays, as every record does.
- `README.md`, `docs/02-loop.md`, `docs/03-operating-contract.md`,
  `docs/07-roles-and-authority.md`, `docs/13-failure-catalogue.md`, `docs/18-flightlist.md`,
  `STATUS.md`, `templates/dogfood-cycle-report.md`, `templates/feature-spec.md`,
  `deploy/02-scaffold-a-project.md`, `docs/img/the-line.png` and its source, the adr index and
  the 0005/0006 status lines: back to the owner merge, as in 0.2.14.
- Unchanged from 0.2.16: adr 0015 (every station on the top tier) and the routing edits in
  `docs/00-glossary.md`, `docs/03`, `docs/07`, `docs/10`, `docs/13`, `STATUS.md` and
  `deploy/01-workstation-macos.md`.

## 0.2.16 (2026-10-01)

The spec catches up with two operator decisions: merge on green in the operator's own
repositories, and one model tier for every station. (0.2.15 and adr 0013 are taken by the
unmerged merge-serialization branch.)

- `adr/0014-agents-merge-on-green-in-the-operators-own-repositories.md` (accepted, 2026-09-30):
  the agent arms auto-merge when it opens a PR and the forge merges on green; a capped watcher
  merges directly, pinned to the checked head with `--match-head-commit`, when armed auto-merge
  does not fire (kvart #333 and #356). Arming only where required checks exist: elsewhere
  `--auto` merges at once, so the watcher is the only path; with no checks at all the merge is
  the owner's. Never red, never unrun, never a head the checks did not see, never admin. Organisations keep adr 0006. 0006's weekly identity check is retired for
  these repositories; its replacement counts merges on red, target 0. The named-human sign-off
  on money, tenant, identity and migration changes moves to the release.
- `adr/0015-every-agent-station-runs-the-top-tier.md` (accepted, 2026-09-29): every station on
  the top tier, reviewers may run the reviewer model, effort floor medium, model passed
  explicitly, alias pinned in every config directory. The mid-tier record is kept as history;
  cost per commit is re-measured.
- `README.md`, `docs/02-loop.md`, `docs/03-operating-contract.md`,
  `docs/07-roles-and-authority.md`, `docs/00-glossary.md`, `docs/10-measurement.md`,
  `docs/13-failure-catalogue.md`, `STATUS.md`, `templates/dogfood-cycle-report.md`,
  `deploy/01-workstation-macos.md` (pin `claude-opus-5-5`, both knobs),
  `deploy/02-scaffold-a-project.md` (choose the merge shape; allow auto-merge),
  `docs/18-flightlist.md` (S2 per merge shape), `templates/feature-spec.md` (money sign-off
  before release under merge on green): both shapes
  described where the merge was stated; the routing rule where the tiers were.
- `docs/img/the-line.png` re-rendered from its source: the human gate is pre-release, and
  pre-merge where the repository keeps a human merge. `docs/img/the-loop.png` still reads "the
  owner merges" in SHIP; it has no source in the repository and is left for a redraw.
- adr 0005 and 0006 status lines and the adr index name the qualification.

## 0.2.15 (2026-09-29)

A green is valid only on its base: two green PRs turned kvart's main red in 20 minutes.

- `evidence/kvart-stale-green-merges-2026-09-29.md`: the stale-base break, the selection-gap
  break, the stale local ref, and the re-check applied to the last three merges.
- `docs/06-verify-gate.md`: "A green is bound to its base": repo-wide fences on every PR,
  merges only on the current base.
- `adr/0013`: one merge serializer in two layers; layer 1 never merges, layer 2 is ADR 0006's
  delegated merge under the bot identity. An arm binds to one head; it is a human decision only
  where agents cannot arm under the human's identity; the serializer's own config and the gate's
  tests are never in a delegated class. Proposed. Panel-reviewed (two vendors plus a blind
  security pass) before merge.
- `docs/08-sandbox-and-isolation.md`: worktrees start from the remote default branch; a
  session-start hook fetches, then fast-forwards the local ref only where git allows it (not
  `fetch <b>:<b>` into a checked-out branch).
- `docs/11-scaling.md`: red-main-after-green-merge as a promotion criterion; stale greens as a
  scale failure. `docs/13-failure-catalogue.md`: one new row, one fix mechanised.
- `STATUS.md`: one row.

## 0.2.14 (2026-09-29)

Sensors 1, 2 and 4 on the ledger: what a trial could measure and what it could not.

- `evidence/kvart-sensor-trial-2026-09-29.md`: five instruments on kvart. The ripwire index
  across worktrees (4 of 4 cases). chisle's install scope and an audit of its output elisions (67,
  1 suspected silent loss). An enola backtest over 201 merges (0 regressions, planted control
  caught) with the live false-block record. One brief built three times with one sensor varied
  per run, and a two-vendor review of each.
- `STATUS.md`: ripwire and chisle move to measured for the index and the elision; their effect on
  a build stays designed. enola's catch stays designed, with the backtest and false-block record
  in the note.
- `docs/05-sensor-stack.md`: the measured results in layers 1, 2 and 4 and the wiring table;
  plugins install at user scope and are enabled per project.
- `deploy/01-workstation-macos.md`, `deploy/02-scaffold-a-project.md`: chisle installs at user
  scope behind a pinned marketplace, switched off there and on per project.
  `deploy/bin/check-workstation.sh` checks the installed commit against the literal pin, the
  install path, and the marketplace source and ref, and fails on a missing, unpinned or
  project-scope install and on a plugin switched on for every repository.
  `deploy/bin/check-project.sh` fails when the project does not switch it on.

## 0.2.13 (2026-09-28)

Lights-on, company-agnostic, and pictures that read.

- `README.md`: the Mermaid line diagram is replaced by a rendered PNG
  (`docs/img/the-line.png`, source `docs/img/src/the-line.html`, `render.sh`), and three slide
  images join it: the factory as components, where the cost went (captioned illustrative, with
  its measured anchor), and the loop, in a new short section.
- Lights-on: the README and `docs/00-glossary.md` say the factory runs lights-on, as a factory
  for one or for a team; the glossary gains the term. Every "lights-out" loop or mode in
  `docs/`, `adr/0003` and `evidence/` is now "unattended", which is what it meant. The public
  post title in `evidence/field-evidence.md` is quoted as published.
- `deploy/`: the vendored trees are company-agnostic. The organisation's rule packs, wiki
  pointers, domain glossary and adoption profile are removed; the `rule-packs` plugin replaces
  the old one and ships one generic example pack (`rules/common/ci-gates.md`). Identifiers are
  placeholders (`<org>`, `group-*`, `dev@example.com`). `WRITING.md` and `deploy/README.md`
  state the rule. History was rewritten to match.

## 0.2.12 (2026-09-19)

The README says what the line is, and where the PM half of it lives.

- `README.md`: the opening states the three human decisions the measured line keeps (ticket
  Ready, merge, release) and places lights-out on the scaling ladder rather than in the present
  tense. New section "Before the code: the PM surface": the intake-to-ticket mechanisms with
  their skills and evidence classes (ingest, ticket, readiness-evaluator, task-improver,
  task-splitter, graduate, the three spec skills, the program design note, the spec as a gate
  input) and where each lives in this repository (`templates/skills/`, `deploy/marketplace/`).
  The line diagram and the layer table gain the ticket as layer 0; a "Where the humans are"
  table names each decision, who takes it and what they read. The measured table points at
  `STATUS.md` rows instead of narrative files.
- `docs/00-glossary.md`: the software-factory definition matches the README (no "runs
  lights-out", no "dark").
- `STATUS.md`: two rows said "Dark-factory"; the design has been called software factory since
  0.2.0.

## 0.2.11 (2026-09-16)

The setup becomes a runbook a second engineer can execute.

- `deploy/`: how the factory is stood up, in the shape it runs on the reference implementation.
  `01-workstation-macos.md` (the tools, plugins, credentials and settings for one Mac, an
  engineer profile and a PM profile, the traps from the reference machine);
  `02-scaffold-a-project.md` (the agent runbook: inputs to collect, then the flightlist's D0, G
  and M legs as commands with a check and an evidence pointer each, test-the-test, verify on
  arrival, the run record); `bin/check-workstation.sh` and `bin/check-project.sh` (one line per
  requirement, exit 1 on a missing required item, tested against a known-true and a known-false
  case); `marketplace/` (a Claude Code marketplace holding the eight plugins from the group's
  catalog the loop uses, verbatim at pinned commits, `pm-workspace` at 1.6.0); `standard/` (the
  group's context standard v0.4 with its adopt script, the operating contract, the team-context
  and instructions templates); `templates/` (kvart's wiring: tracked agent settings with the
  sensor hooks, MCP servers, rule files, git hooks including the provenance trailer, the ledger
  script with its tests, the gate and ledger workflows, the ruleset body, the memory binding, the
  Jira workflow payload). Two changes to the copied workflows: both ledger workflows now pass
  `JIRA_PROJECT_KEY` from a repository variable, so the key regex is not hard-wired to the
  reference project.
- `README.md`, `WRITING.md`, `STATUS.md`, `docs/18-flightlist.md`: the pointer, the file-taxonomy
  entry with the anonymisation exemption for vendored trees, the status row (designed until a
  second engineer runs it), and the flightlist's link to the commands that execute its legs.

## 0.2.10 (2026-09-15)

Design before the plan; red-first becomes a gate.

- `docs/02-loop.md`: program design as the first step of BUILD for sized tickets, with a sizing
  rule (one-shot, one-note, full), the cycle-4 contract as its measured precursor, the trial's
  round-3 redesign and cycle 2's planning document as its cost, two mechanical checks (the module
  list as the spillover scope, section 6 as the fail-on-base list), the rejected alternatives,
  and starter kits as the architecture layer a note builds on.
- `templates/program-design.md`: the note, seven sections.
- `adr/0010`: the decision record for both changes, with the public argument they trace to.
- `docs/05-sensor-stack.md` layer 3: the fail-on-base check `[proposed]`: select by the diff, run
  at the merge base with the branch's tests applied, record the failure kind, declared exemptions
  only, deleted tests always reported, Stop hook or receipt, rehearse both directions; wired-where
  row 3a.
- `docs/01-principles.md` §3: the change has a known-false case of its own, the code before it.
- `docs/06-verify-gate.md`: design review before the build; the note joins the spec pack.
- `docs/14-pm-surface.md`: what the program design note needs from the ticket, section by section,
  the sizing signals only the PM can write, the prototype as a readiness condition for UI work,
  what the PM must not write, and the evaluator's question order on a sized ticket.
- `templates/skills/readiness-evaluator/SKILL.md`: the "Bigger tickets: one extra question"
  section, written for the person who maintains the skill rather than for the design: when it
  applies (from the ticket text only, score-neutral), the four questions in order, the plain-words
  line the author sees, what the skill never asks for and points out as misplaced. Not yet run on
  such a ticket.
- `docs/10-measurement.md`: rework after the first review as the instrument that decides whether
  the note pays; a design-quality row in the instruments table.
- `evidence/field-evidence.md` §7: the talk the two gaps trace to, what is taken and what is not.
- Pointers and rows in 00, 03, 07, 12, 13, 16, 18, README, STATUS, the ADR index, and the gate
  report, cycle report and delegation brief templates.

## 0.2.9 (2026-09-15)

The PM surface after the group's planning session.

- `docs/14-pm-surface.md`: the PM runs the same tooling as the engineer (decided 2026-09-15,
  tooling and access parity, authority unchanged); tracker fields are deduced from the source, the
  code and a `TRACKER.md` configured once, shown with a reason each, approved or corrected, with
  corrections written back so nothing is asked twice; attachments on issues and epics through the
  tracker's REST endpoint because the hosted MCP has none; prototypes are clickable and navigable,
  published only on the PM's explicit decision.
- `templates/skills/ticket/SKILL.md`: step 4b, tracker fields; the never-list now distinguishes
  what is proposed (type, project, parent, labels, links) from what stays with grooming.
- `templates/skills/ticket/references/style-rules.md`: the eleven rules the skill has named since it
  shipped, now present. Step 4b measured on the reference workspace in two fresh sessions, with and
  without the configuration file; both passed, both surfaced the missing epic-key mapping.

## 0.2.8 (2026-09-15)

Test the test applies to the tests.

- `docs/01-principles.md` §3: the suite is a predicate over the code; coverage is its known-true
  case and mutation its known-false case. Numbers from the reference implementation's first
  mutation campaign: kill rate 30.3 % (database-free) and 39.9 % (database-coupled) under green
  changed-line coverage, 11.2 % on the largest billing module.
- `docs/05-sensor-stack.md` layer 3: the mutation kill rate as a ratchet on the touched modules,
  `[proposed]`: scope by the diff, per-module baseline, killed over total, refuse a drop, targets
  on the money lane, generated tests exit on their kills, template-cloned database per run for
  the coupled half.
- Pointers and rows in 00, 06, 09, 10, 11, 13, 16, README, STATUS.

## 0.2.7 (2026-09-10)

The skills ship, and the setup sequence becomes a list you tick.

- `templates/skills/`: ten skills a team copies on day one, anonymised from the reference
  implementation and the group's spec-repos plugin, one directory per skill with scripts beside
  it, indexed in `templates/skills/README.md`. The PM chain that produces the structured input
  every later stage reads: `ticket`, `readiness-evaluator`, `task-improver`, `task-splitter`,
  `graduate`. The spec chain: `retrogenerate-specs` (with the owner-review, check and
  findings-file steps the reference run added), `update-specs-for-commits`,
  `check-specs-references`. Two new: `check-specs`, the three-check spec checker whose original
  lived in a scratch directory and was gone by cycle 1, tested against a clean and a dirty
  folder before landing; and `mine-decision-records`, the Day 1 ADR procedure of 17-onboarding
  §6 made repeatable.
- `docs/18-flightlist.md`: the setup sequence for the next project as legs with a mechanical
  check, an evidence pointer and an owner each: pre-flight decisions, Day 0 repositories,
  Day 1 knowledge plane, gate wiring, sandbox and identity, the PM surface, the first cycle,
  verify on arrival. A skipped leg is a named shortcut in ADR 0001 the day it is skipped.
- `docs/12-adoption-playbook.md`, `docs/14-pm-surface.md`, `docs/16-inventory.md`,
  `docs/17-onboarding.md`, `README.md`, `WRITING.md`: pointers to the skills and the list;
  `templates/skills/` joins the file taxonomy.
- Ported skills keep their logic; every em dash is gone, every employer, product, person and
  example ticket key is generic, every frontmatter `name` matches its directory.

## 0.2.6 (2026-09-10)

The spec becomes a VERIFY input, proposed.

- `adr/0009`: the spec is a gate input; scope drift is a finding with its own disposition.
  Context from cycle 4: the panels ran before the decisions existed, the scope question came
  from code and was adjudicated by the authoring session alone, the pre-build spec and its
  delta were both unmerged; cycle 5's delta open at handoff. Four alternatives weighed,
  including the one that looked obvious (compare with the ticket text) and the one that looked
  disciplined (fold every decision in first); both rejected with reasons.
- `docs/06-verify-gate.md`: "Spec conformance" section: injected spec pack to every leg, the
  spec-drift class both ways, REFINE-SPEC, the delta as a receipt-checked pre-push gate, and
  the test the class must pass before it is trusted.
- `docs/02-loop.md`: REFINE-SPEC in the disposition list; LEARN item 1 names the receipt.
- `docs/03-operating-contract.md`: §11, a decision that changes behaviour also goes into the
  delta; enforcement table row.
- `docs/16-inventory.md`, `STATUS.md`, `adr/README.md`: the rows.
- Merge note: a parallel session designed the same finding class the same evening as a
  "Spec-conformance finding" section in 06, from the principles (NOTE default, flag never fix,
  test the test). That section is kept as the home of the mechanism and this entry's material
  is folded into it; its assumption that the reviewer already holds the spec was checked and
  corrected, the class keeps its name `spec-drift`, and adr/0009 is the decision record for
  both.

## 0.2.5 (2026-09-10)

Sensor 2 changes tool: chisle replaces ponytail on the reference implementation, same ladder.

- `docs/05-sensor-stack.md`: Layer 2 names chisle, what it adds (prose ruleset, tool-output
  elision with its kill switch), why the swap (the vendor's 20-task comparison), the caveats
  (hooks read in full, a tag pin rather than a commit pin, elision as a possible new failure
  class); the wired-where row.
- `evidence/field-evidence.md`: section 5a, the chisle record with the comparison table and the
  pre-adoption audit; section 5 stays as the dated ponytail record.
- `docs/16-inventory.md`, `README.md`, `STATUS.md`: the Sensor 2 rows and the picture.
- `WRITING.md`: chisle joins the nameable tools.
- `templates/ticket.md`: "Escalation triggers" section. Without an explicit list of escalate-when
  conditions the agent infers its own bail-out criteria; the section makes them a first-class
  part of the spec `[field: Ichigo, "Harness Engineering", 2026-08-29]`.
- `docs/10-measurement.md`: headline ratio, accepted outputs over human review minutes. The
  numerator is merged PRs a human said yes to; the denominator is review-active minutes with
  idle wait excluded. The per-turn numbers diagnose; this ratio is the mandate signal.
- Merge note: a parallel session published the tool swap plus the two items above as a second
  "0.2.4" on 2026-09-10 morning; that entry is folded here, and 0.2.4 stays the browser QA
  runtime.

## 0.2.4 (2026-09-10)

The browser QA runtime, after evaluating the Playwright CLI against the kvart stack.

- `adr/0008`: the browser QA pass drives a CLI, not a protocol server or a browser extension;
  one session per persona, state saved once and restored; evidence on disk, a few lines in
  context; a missing runtime stops the pass instead of a hand-written script; the skill is
  tracked so a station worktree has it.
- `docs/06-verify-gate.md`: the runtime paragraph under the receipt gates, with the shakedown.
- `docs/05-sensor-stack.md`, `docs/15-design-system.md`: the row notes; the page tree the runtime
  writes is the input for the still-designed patterns check.
- `docs/13-failure-catalogue.md`: three rows (a gitignored skill is absent from every worktree;
  browser state saved during the SPA callback; the 0-byte auto-named page tree).
- `STATUS.md`: Browser QA pass row carries the runtime, the shakedown, the cold rehearsal and the
  gate on the skill itself (security pass, two-vendor panel, dispositions).

## 0.2.3 (2026-09-09, evening)

The evening's eight loop-infrastructure PRs on kvart, and two decisions the day forced.

- `adr/0004`: decided, option (b): the guard permits a baseline write that only lowers a
  number. The day's seven collisions split into five from a merge-base diff bug and two real
  deadlocks.
- `adr/0006`: incident recorded, an agent merged a green PR under the owner's login on a
  handoff's instruction; decided that the loop does not merge and a handoff never instructs
  one; the qualified class waits for the bot identity to merge as itself.
- `docs/02-loop.md`: receipt-checked pre-push gates as a VERIFY step (browser pass measured,
  static analysis designed); the merge line; cycle 3 and cycle 4 rows in the cost table.
- `docs/05-sensor-stack.md`, `docs/06-verify-gate.md`: the receipt pattern, the rehearse-the-
  blocked-direction rule with its three defects, the strict-mode base_ref hardening, the
  worktree scanner degradation.
- `docs/07-roles-and-authority.md`: the measured worker-tier routing rule and the served-model
  audit (alias leak).
- `docs/14-pm-surface.md`: the tracker is real; the status-line shortcut is a dated past state.
- `docs/03-operating-contract.md`: claim a broken shared gate before fixing it; commit the real
  change before a throwaway commit; a handoff instructs a verify, never a merge.
- `docs/10-measurement.md`: factory-on-itself share (8 of 13 merges on 2026-09-09).
- `docs/13-failure-catalogue.md`: eight rows (introducing PR cannot exercise itself, two
  sessions on one red gate, the probe that swept an uncommitted fix, stale lock and a stale
  shared checkout, a baseline staged but not committed, a gate that cannot fail on bash 3.2,
  base_ref = HEAD, the alias leak).
- `templates/handoff.md`: the merge line.
- `STATUS.md`: static-analysis receipt gate (designed), worker-tier routing, the merge
  incident on the ruleset row, the factory-on-itself metric, the scanner caveat.

## 0.2.2 (2026-09-09)

Cycle 4 on kvart: first batch (an epic with four stories) through the loop with three parallel
stations against a written contract. What it exposed, and where it landed:

- `docs/03-operating-contract.md` §11: agent-surfaced decisions (questions, dismissals,
  deviations) go to the escalation channel and the ledger, with default and deadline; labels
  on the ticket; write-back by hand until automated. Recorded after a measured lapse.
- `docs/13-failure-catalogue.md`: nine rows (queued canvas station, worktree provisioning
  drift, station wiped its venv, brief-planted field name, strict ratchet vs guard deadlock,
  impact-slice coverage floor, two PRs tightening one baseline, a false "suite is red", a
  review finding that contradicts the spec).
- `adr/0004`: follow-up on strict mode versus the agent guard, three options, one recommended.
- `STATUS.md`: escalation row updated; two new measured rows (contract-first parallel
  stations; fix station after the panel).

## 0.2.1 (2026-09-07)

Downstream fixes referenced. The design named the sensors; this records what broke in them on
the first full day and where each fix landed.

- `docs/05-sensor-stack.md`: four new layer-3 rules (a Stop hook reports a failure set once, a
  formatter pass is not a change, a gate that cannot fail is not a gate, a pre-push gate must
  read the ref list), the fork-and-PR path for a third party's tool, and the layer-4 Stop hook
  replaced by a check that blocks once, with its planted cases.
- `STATUS.md`: the ratchet and architecture rows carry the fix references; the pre-push and
  worktree rows carry the open defect and the pile.

## 0.2.0 (2026-09-07)

Coverage of the surfaces the first cut only named.

- `docs/14-pm-surface.md`: the PM workspace, a catalogue of its skills, the readiness rubric,
  the intake-to-ticket pipeline and the proposed/implemented/released boundary.
- `docs/15-design-system.md`: the design-standards repo as a knowledge-plane layer.
- `docs/16-inventory.md`: every mechanism mapped to what provides it today and what an adopter
  without an organisational standard must build.
- `docs/17-onboarding.md`: the Day 1 runbook (team-context repo, standard adoption, instruction
  split, memory move, three-mode spec retro-generation with owner review, ADR candidate table
  and mining, PM workspace, design system), with the kvart numbers.
- `templates/pm-skill.md`: a generic skill skeleton.
- `STATUS.md` and the README reading order extended.

## 0.1.1 (2026-09-07)

Visuals. The design had none: every mechanism was prose and tables only.

- `README.md`: the delivery line end to end, 9 layers in 3 frames (ergonomics, gates,
  after the PR), with an index table naming what each layer refuses and its evidence class.
- `docs/02-loop.md`: the loop redrawn with the knowledge plane at the centre, replacing the
  ASCII sketch that showed LEARN returning straight to SPEC without the hub. Both write-backs
  are now edges, and the memory arrow is drawn dashed because it fired zero times in two
  measured cycles.
- `docs/05-sensor-stack.md`: where each sensor fires inside one agent turn, plus a table of
  which checks are wired on kvart and on the legacy core.

Diagrams are mermaid so they render on the forge, diff as text and can be adapted by a reader.
Fill encodes the evidence class from `WRITING.md`, never severity. `STATUS.md` stays the ledger.

## 0.1.0 (2026-09-07)

First consolidation. Derived from:

- the kvart dogfood, 2026-09-07: Day 1 bootstrap, cycle 1 (public-route fix), cycle 2
  (retire a payment path), the sensor-stack wiring;
- the head-and-hands harness trial on kvart, 2026-09-05;
- the legacy-core flywheel work, 2026-09-04 to 09-07: design v0 and re-base, turn 0 adoption,
  turn 1 verification net, money tiering, ratchets, layering gate, complexity ratchet, sandbox
  boot;
- the operator contract and its rule set as of 2026-09-07;
- the planning-to-validation evidence audit and proposal v3, 2026-09-05;
- the measurement baseline and the scaling analysis, 2026-09-07.

Contents: 14 design documents, 3 case studies, 4 evidence files, 8 templates, 7 decision
records, the status ledger.
