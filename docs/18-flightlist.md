# Flightlist: setting up the next project

The checklist form of turn 0 and the first turn, in the order the reference implementation
ran them, with the mechanical check per leg and the evidence each leg leaves behind. It exists
because the second project is where a design either reproduces or turns out to have been one
person's habits. Prose for every leg lives in the documents named in the last column; this
page is the thing you tick.

Three rules for using it:

- **No leg without a check.** A leg whose check is judgement says so and names the person.
- **A skipped leg is a named shortcut**, written into ADR 0001 of the team-context repo the
  day it is skipped, never later.
- **Tick with evidence, not with memory.** Each `[x]` carries a pointer: a commit, a PR, a
  report line, a command's output. The verify-on-arrival block at the end is what a fresh
  session runs before trusting any of it.

Legend: `[ ]` not started, `[x]` done with evidence, `[~]` skipped, shortcut recorded.
The commands that execute the D0, G and M legs, with the files they copy, are in
[deploy/02-scaffold-a-project.md](../deploy/02-scaffold-a-project.md); the machine they run on is
[deploy/01-workstation-macos.md](../deploy/01-workstation-macos.md).
"Human" in the who column means the leg cannot be delegated to an agent by this design.

## P. Pre-flight: decide before anything is created

| # | Leg | Do | Check | Evidence | Who | Where |
|---|---|---|---|---|---|---|
| P1 | Standard adopted or substituted | Decide whether the organisation's contract, context standard, sandbox template and plugin catalog are adopted, or this repository's `templates/` stand in | ADR 0001 in the team-context repo names the choice and every shortcut | the ADR | Human | [12](12-adoption-playbook.md), [adr/0001](../adr/0001-adopt-a-standard-not-build-a-harness.md) |
| P2 | Money surface tiered | List the code where a wrong change moves wrong money or shows wrong numbers; tier per class | a surface file exists; every listed path resolves in the tree | the file, in the code repo | Human with an agent | [09](09-legacy-adoption.md) |
| P2.1 | Money paths mapped | For each figure or payment state people pay on, list entry, hops in order and exits, with the test per hop and one agreement test | the resolver passes; every transaction-tier file is a hop or declared off-path with a reason | `money-paths.yaml`, in the code repo | Human with an agent | [adr/0012](../adr/0012-money-paths-are-mapped-and-agree.md) |
| P3 | Baselines taken on human-written code | Revert rate per 100 merged PRs, defect escape per PR, lead time request to prod, all dated | a dated memory record carrying the three numbers | the record id | Agent, owner confirms | [10](10-measurement.md) |
| P4 | Business-truth reviewer named | One person who will review two tables: spec candidates and ADR candidates | the name and a booked slot | the front door file | Human | [17 §0](17-onboarding.md) |
| P5 | Supervision level chosen | Autonomous only inside the sandbox; interactive on the operator's machine; hands-on for the first legacy turns | the level written into the first ticket | the ticket | Human | [02](02-loop.md) |

## D0. Day 0: the repositories

| # | Leg | Do | Check | Evidence | Who | Where |
|---|---|---|---|---|---|---|
| D0.1 | Team-context repo | From `templates/`: front door, CODEOWNERS routing `specs/**` and `.memspec/**`, `docs/adr/` with the numbered template and ADR 0001 | `ls` shows the four files; CODEOWNERS has a real owner, no placeholder | first commit | Agent | [17 §1](17-onboarding.md), [04](04-knowledge-plane.md) |
| D0.2 | Branch protection | Require code-owner review on the team repo, after CODEOWNERS is real | protection API returns the rule; or the plan refuses and ADR 0001 records the habit | API output or the ADR line | Human | [17 §1](17-onboarding.md) |
| D0.3 | Context standard in each code repo | Run the adopt script; fill seeded docs from existing docs, mark them "for L1 review" | the standard's check mode passes; docs-lint runs, or its absence is recorded | the check output | Agent | [17 §2](17-onboarding.md) |
| D0.4 | Instructions split | Lean root plus path-scoped rule files with a routing table; every rule read against the code | every rule glob matches at least one file; one rule found stale and fixed is the expected result | the fix commit | Agent, owner reads | [17 §3](17-onboarding.md), [03](03-operating-contract.md) |
| D0.5 | Memory store moved | Subtree the store into the team repo with history; bind the code repo read-only | `memspec stores` lists the team store `[ro]` with a count and scratch `[rw]` | the command output | Agent | [17 §4](17-onboarding.md) |
| D0.6 | PM workspace | Copy the template; fill `POINTERS.md` and `SENSITIVITY.md`; copy `templates/skills/*` into `.claude/skills/` | run the `ticket` skill once against the specs before trusting the rest | the drafted ticket | PM with an agent | [14](14-pm-surface.md), [17 §7](17-onboarding.md) |

## D1. Day 1: the knowledge plane

| # | Leg | Do | Check | Evidence | Who | Where |
|---|---|---|---|---|---|---|
| D1.1 | Feature maps | `retrogenerate-specs prepare`, one confined explorer per project | one memory file per project | the files | Agent | [17 §5](17-onboarding.md), `templates/skills/retrogenerate-specs` |
| D1.2 | Candidate table | `retrogenerate-specs suggest`; long on purpose, sorted by subdomain, never truncated | the count is recorded; no "and more" | the table | Agent | same |
| D1.3 | Owner review | Merge, split, rename, drop, mark unbuilt, on a shared review artifact | every row carries a decision | the artifact | **Human** | [17 §5](17-onboarding.md) |
| D1.4 | Spec pairs | `retrogenerate-specs generate` per approved slug; writers verify each claim against code and leave notes inline | `check-specs.py <specs>` exits 0 | the checker output | Agent | `templates/skills/check-specs` |
| D1.5 | Findings file | Collect every writer note (defects, dead surface, docs behind code) into one file in the team repo | the file exists; it is the first backlog | the file | Agent | [17 §5](17-onboarding.md) |
| D1.6 | Specs PR | Owner reads for business truth and merges | `ls specs/*/ \| wc -l` equals the approved count | the merged PR | **Human** merges | [adr/0007](../adr/0007-specs-are-derived-memory-promotes-by-pr.md) |
| D1.7 | ADR candidates | `mine-decision-records`: sweep design docs and rule files, one row per load-bearing decision live in code, status per row, a rejected list | every evidence path resolves; UNCONFIRMED rows stay rows | `CANDIDATES.md` | Agent | `templates/skills/mine-decision-records`, [17 §6](17-onboarding.md) |
| D1.8 | Decision records | Repo-level records in the code repo, team-level in the team repo, both from `templates/adr.md`; PRs the owner reads | `ls` both `adr/` folders; candidates file present | the merged PRs | Agent writes, **Human** merges | [17 §6](17-onboarding.md) |
| D1.9 | Design system, if one exists | An existing design-system repo is scaffolded as a code repo (D0.3, G, M4 apply to it); otherwise recover the handoff exports, put tokens, patterns, components into their own repo, write the divergence log | `check-project.sh` run in the design-system repo, residue named; or the repo exists and the log is non-empty or says "none" | the checker output or the repo | Agent | [15](15-design-system.md), [17 §8](17-onboarding.md) |
| D1.10 | Day 1 wall-clock | Record start, end, elapsed for the day | a number in the onboarding record | the record | Agent | [17](17-onboarding.md) |

## G. Gate wiring, per code repo

| # | Leg | Do | Check | Evidence | Who | Where |
|---|---|---|---|---|---|---|
| G1 | Review panel reachable | Two cross-vendor legs configured; probe each; then break one on purpose | probe returns the token; the broken leg makes the gate exit 3, not degrade | both outputs | Agent | [06](06-verify-gate.md) |
| G2 | Scanner tier | Secret scan and dependency scan on main; static analysis where a server exists; every SKIPPED line repeated in the report | one run recorded with its baseline count | the report | Agent | [06](06-verify-gate.md) |
| G3 | Blind security side-pass | Non-inheriting security reviewer on a diff with one planted secret | the plant is found | the run | Agent | [06](06-verify-gate.md) |
| G4 | Sensor stack | In a throwaway worktree: orientation map, YAGNI ladder, quality ratchets, architecture diff with a layer declaration; read the settings diff; then baselines re-cut on main **by a person**, accepted sites named in the commit | gate green; the guard refuses a baseline write; `N functions judged` is above zero in the primary **and** in a worktree; `enola check --fail-on=layers,intent,cycles` passes | the baseline commit, both gate outputs | Agent wires, **Human** baselines | [05](05-sensor-stack.md), `templates/sensor-config-examples.md` |
| G5 | Receipt-checked pre-push | Browser pass scoped by routes; static analysis; the spec delta once KVART-23 ships; each writes a receipt keyed by tree id | a diff reaching a surface without its receipt is refused; with it, passes | both push attempts | Agent | [06](06-verify-gate.md), [adr/0009](../adr/0009-the-spec-is-a-gate-input.md) |
| G6 | Merge authority | Branch protection or the pre-push hook; provenance trailer on every commit | a push without the trailer is rejected; a dry-run push to the default branch is blocked | both refusals | Agent | [adr/0005](../adr/0005-humans-approve-never-author.md), [adr/0006](../adr/0006-pr-gated-output-human-release.md) |
| G7 | Every gate made to fail once | Planted escape, planted secret, planted drift, planted layer crossing | each red observed | one line per gate | Agent | [01](01-principles.md), test the test |
| G8 | Fail-on-base check | Wire the check on the Stop hook or as a receipt; plant a test that passes on the base, run a real red-first test, declare one characterization test | the first is refused, the second passes, the third passes with its label in the receipt | the three runs | Agent | [05](05-sensor-stack.md), [adr/0010](../adr/0010-program-design-before-the-plan.md) |

## S. Sandbox and identity

| # | Leg | Do | Check | Evidence | Who | Where |
|---|---|---|---|---|---|---|
| S1 | Sandbox booted | From the template; egress allowlist | allowlisted host 200, non-allowlisted refused, direct route absent; the build still resolves private packages | the three probes | Agent | [08](08-sandbox-and-isolation.md) |
| S2 | Scoped identity | A bot identity authors PRs; humans merge | a PR opened by the bot; a merge attempted by the bot is refused | the PR, the refusal | Human grants, agent proves | [08](08-sandbox-and-isolation.md), [07](07-roles-and-authority.md) |
| S3 | Worktree per turn | Nested worktrees excluded from every sensor walk; deletion owned by the orchestrator | `git worktree list` is clean after a cycle | the listing | Agent | [08](08-sandbox-and-isolation.md), [05](05-sensor-stack.md) |
| S4 | Test data isolation | One database or schema per tree | two trees, two databases, verified | the listing | Agent | [08](08-sandbox-and-isolation.md) |

## M. The PM surface: structured input

| # | Leg | Do | Check | Evidence | Who | Where |
|---|---|---|---|---|---|---|
| M1 | Ticket shape | `templates/ticket.md`: numbered examples, out-of-scope, escalation triggers | the first ticket has numbered examples the tests will cite | the ticket | PM with the `ticket` skill | [14](14-pm-surface.md), `templates/skills/ticket` |
| M2 | Readiness | `readiness-evaluator` scores; `task-improver` raises below 85; `task-splitter` above two person-days; `graduate` moves a features file into the team repo | the first ticket's score is recorded; a graduate package passes its six checks | the score line, the package | PM with an agent | `templates/skills/readiness-evaluator`, `task-improver`, `task-splitter`, `graduate` |
| M3 | Escalation channel | One thread per cycle: questions and the agent's own dismissals, each with a default and a deadline; labels on the ticket; decision written back | a synthetic round trip measured | the latency | Agent, a named human answers | [03 §11](03-operating-contract.md) |
| M4 | Tracker | Statuses Backlog, Ready, In Progress, In Test, Ready for LIVE, Done; transitions driven by PR events or by hand | a ticket moves on PR open and on green | the transition log | Agent | [14](14-pm-surface.md) |

## C. The first cycle

| # | Leg | Do | Check | Evidence | Who | Where |
|---|---|---|---|---|---|---|
| C1 | One small ticket end to end | A one-line fix (one-shot, so no design note; the plan says so); PM hat and dev hat in two sessions; every stage timed; tokens per agent; what the gate caught; every skipped step named | the cycle report exists and the sister spec delta and memory promote PR are open or merged | `templates/dogfood-cycle-report.md` filled | Agent, **Human** merges and releases | [02](02-loop.md), [06](06-verify-gate.md) |
| C2 | Verify on arrival | A fresh session runs the block below before trusting any of the above | six commands, six expected outputs | the transcript | Agent | [17 §9](17-onboarding.md) |
| C3 | Compare | Against the reference: 12 to 19 min to PR, under 30 min to live without required CI, 41 min with it | the deltas recorded | the cycle report | Agent | [10](10-measurement.md), [STATUS](../STATUS.md) |

## Verify on arrival

```
git log -1 --oneline                          # code repo at or past the bootstrap merge
memspec stores | head -2                      # team [ro] N items, scratch [rw]
ls team-context/specs/*/ | wc -l              # spec pairs present
python3 check-specs.py team-context/specs     # exit 0
ls code-repo/docs/adr/ team-context/docs/adr/ # records and the candidates file present
gh pr list -R <team-context> --state open     # nothing left unmerged from Day 1
```

## What this list is not

It is not the design. Every leg here compresses a document that says why, what was measured,
and what was rejected; a leg ticked without its document read is a habit copied, not a design
adopted. And it is not finished: the reference implementation's rows marked `designed` and
`proposed` in [STATUS.md](../STATUS.md) are legs whose check has not yet been run on a second
project. The second project is where they get one.
