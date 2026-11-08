# Onboarding a repository

The Day 1 runbook: how a codebase that has never had an agent run against it gets its
knowledge plane before the first ticket. Retro-generated specs, mined decision records, the
team-context repo, the memory move, the PM workspace. This is turn 0 of the
[adoption playbook](12-adoption-playbook.md) in full, with the kvart Day 1 numbers.

Why it is part of the factory and not a preamble to it: every later turn reads what this day
writes. A ticket written against a repo with no specs forces the agent to reconstruct current
state from code on every ticket. A rule file that describes a retired design will be
re-implemented. A decision that lives only in a design document will be reversed by an agent
that never saw it. The onboarding day is where the write-backs of [02-loop](02-loop.md) get
something to write back into.

Cost, as measured: one long session for a ~250-feature product, including the audit it
produced as a side effect `[measured 2026-09-07]`. Record the wall-clock; it is the honest price
of the standard and a number an organisation needs before asking a team to pay it.

## 0. Preconditions

- The operating contract and the context standard exist (or this repository's templates stand
  in for them).
- A person who can judge business truth is available to review two tables: the spec candidate
  table and the ADR candidate table. Without that reviewer the output is generated text, not
  knowledge.
- A memory engine is installed on the operator's machine.
- Branch protection can be turned on in the team-context repo, or its absence is recorded as a
  named shortcut.

## 1. Create the team-context repo

From the template: a front-door instructions file (bracketed template plus a filled example to
copy from, or let an agent interview the owner and draft it), a CODEOWNERS routing `specs/**`
to PM-through-lead and `.memspec/**` to the lead, a decision-record folder with the numbered
template, and ADR 0001 naming every shortcut this team takes against the standard.

Then enable branch protection requiring code-owner review, and only after CODEOWNERS has a
real owner: protection with an unresolved placeholder makes the gated paths unmergeable.

Where the plan refuses protection, write that into ADR 0001 as the shortcut it is: the merge
gate is a habit, every change lands through a PR the owner reads `[measured 2026-09-07]`.

## 2. Adopt the context standard in each code repo

Run the adopt script against the code repo, then point the memory binding at the team repo.
The script seeds the agent instructions sentinel, a lock file recording the standard version,
the memory pointer, and skeleton current-state docs (architecture, manifest, agent-memory)
that are the repo's to fill. It is idempotent; a dry-run and a check mode exist, and the check
is what CI runs.

Fill the placeholders from the existing docs, not from memory. Mark seeded docs "for L1
review" rather than leaving them looking finished.

What kvart found: the standard's team import path did not exist on the operator's platform,
so the team layer reached agents only through the memory binding; the docs-lint workflow called
a reusable workflow in a private organisation and was disabled; the memory engine read its
store list from its own config, not from the standard's pointer, so both files were kept
`[measured 2026-09-07]`. Each mismatch is a finding for the standard, recorded in ADR 0001 of
the code repo.

## 3. Split the agent instructions

If the repo's instructions file is one large block, split it: a lean root carrying only what
applies to every change, and path-scoped rule files that load when a matching file is read,
with a routing table in the root so a rule can be read before its paths are touched. Content
moves verbatim. Then check every rule file's paths against the tree.

Read every rule file against the code while you are there. kvart's authentication rule
described a token model retired 2026-06-25 and was loading into every session
`[measured 2026-09-07]`.

## 4. Move the memory store

If a memory store lives inside the code repo, move it into the team-context repo with history
(a subtree split preserves it), delete it from the code repo, and bind the code repo read-only.
Verify with the engine's store listing: the team store read-only with its record count, the
operator's scratch store read-write.

From this point durable writes are promote PRs. Local writes at the moment of discovery go to
scratch under the project's scope. Whether the owner keeps writing under that friction is a
result to collect; kvart's first two cycles did not promote `[measured 2026-09-07]`.

## 5. Retro-generate the current-state specs

Three modes, run in order, with the owner in the PM role between modes 2 and 3. The skills:
[templates/skills/retrogenerate-specs](../templates/skills/retrogenerate-specs/SKILL.md),
[update-specs-for-commits](../templates/skills/update-specs-for-commits/SKILL.md) and the
checker, [check-specs](../templates/skills/check-specs/SKILL.md).

**Mode 1, prepare.** One read-only explorer per project (backend, web client, mobile client),
each confined to its own directory, returns a feature map from the user's perspective (routes,
pages, endpoints, controllers, domain models, stack, notable boundaries). Saved as one memory
file per project so later runs do not re-explore.

**Mode 2, suggest.** From the maps, an exhaustive candidate table: feature slug, subdomain,
projects involved, one line. Decomposition rules make it long on purpose: every entity's
create-edit-remove is a slug, every role's distinct view is a slug, every multi-step flow,
configuration screen, report, integration channel and lifecycle operation is a slug. Sorted by
subdomain, never truncated.

**Owner review.** The table is reviewed for business truth by the person in the PM role:
merge, split, rename, drop, and mark what is known to be unbuilt. kvart: 3 feature maps →
264 candidate slugs → owner review on a shared review artifact with recorded decisions
`[measured 2026-09-07]`.

**Mode 3, generate.** Per approved slug, parallel confined explorers return precise relative
paths; a writer produces the pair: a business-facing spec (overview, who can do this, one
section per user action with inputs, validation in plain language and what happens on save,
customer-facing impact, downstream effects) with no class names, file paths or framework
jargon, and a technical-references sibling listing paths per project under labelled headings.
The writer verifies each claim against code and flags what it finds inline as a note.

kvart: 20 parallel writers → **247 spec pairs across 20 subdomains, 5 marked NOT
IMPLEMENTED** `[measured 2026-09-07]`.

**Check.** A script over every spec folder: both files present, every cited path exists, no
code identifiers in the business spec. Run it before the PR, and keep it in the team repo so
it survives the session that wrote it (kvart's lived in a scratch directory that was gone by
cycle 1, and the three checks were done by hand `[measured 2026-09-07]`).

**Findings file.** Collect every inline note the writers left into one file in the team repo:
defects, dead or unreachable surface, design docs behind the code, governance facts pinned from
code. This is the audit the bootstrap produces for free and it became the entire ticket
backlog for the first cycles. Cross out rows as cycles resolve them, with the PR that did.

The specs enter through a PR. Under adr 0011 the context repo auto-merges that PR rather than
waiting on a human read; the earlier "the owner reads for business truth before merge" model is
superseded for this agent-managed layer, and the state-check (14-pm-surface) is where a proposal
mislabelled as current state is caught.

## 6. Mine and write the decision records

The skill: [templates/skills/mine-decision-records](../templates/skills/mine-decision-records/SKILL.md),
written from this section after the reference implementation ran it by hand.

Two levels. Repo-level records (structure, contracts, data, security, deployment) in the code
repo; team-level rules that hold across the product's repos in the team repo.

**Candidate table first.** Sweep the existing design documents and the rule files for
architecturally load-bearing decisions that are live in the code. For each candidate: proposed
title, the decision in one sentence, source documents, code evidence paths, status (candidate,
unconfirmed, rejected), note. Confirm every candidate against code before it is written;
a candidate whose code evidence cannot be found stays a candidate. Keep a "rejected as not
ADR-worthy" list with the reasoning so nobody re-raises commercial terms, visual design waves
or feature-level UX choices as architecture.

kvart: a candidate table of 30, 13 written as repo ADRs (tenant isolation enforced in the
database, the billing engine as pure functions, ports and adapters for every external system,
the product as its own OAuth server, read-only in-process MCP excluding money and governance,
scheduled jobs only under systemd timers, one payment rail per association, document storage
port with tenant prefix, three bank gateways plus an aggregator, single-VM deploy with
credential loading, migrations behaviour-preserving with row-level-security DDL outside them),
8 written as team ADRs (money is decimal end to end, API enum values are English, domain terms
preserved in code, the mobile app consumes the public API only, four-locale parity, AI output
auditable and never authoritative on figures, agents never move money, vote or delete, durable
memory lives in the team repo), and the remaining candidates left in the table with the rule
that each becomes a record when its code is next touched `[measured 2026-09-07]`.

One candidate carried an UNCONFIRMED status because which storage mode production actually
ran could not be read from the repo. That is the correct state for it: confirm on the box,
then write.

## 7. Set up the PM workspace

Copy the PM workspace template; fill the pointers (repos, team context, design standards,
ticket tracker or "none"); copy the five skills from [templates/skills](../templates/skills/)
into `.claude/skills/`. Run one skill against the copy before trusting the rest: kvart's
ticket skill referenced a style file the copy did not have, and its lookups missed until the
specs PR merged `[measured 2026-09-07]`. See [14-pm-surface](14-pm-surface.md).

## 8. Bring in the design system, if there is one

If the design system already has its own repository (a package the product repos install, a
home for design-tool exports, a structural catalogue), it is one of the team's code repos for
the rest of this day: scaffold it with `deploy/02-scaffold-a-project.md`, run its spec bootstrap
with each component as a feature, and name it, with the version each product pins, in the
team-context front door. It binds to the owning team's context even when other teams consume
it.

If it does not, recover design-tool handoff exports from wherever they are (kvart's were
git-ignored zips in the docs folder), extract tokens, patterns and components into their own
repo, and write the divergence log between the canvas and what shipped. Either way, see
[15-design-system](15-design-system.md#the-design-system-repo-in-the-loop).

## 9. Verify on arrival

The commands a fresh session runs before trusting the day's work:

```
git log -1 --oneline                          # code repo at or past the bootstrap merge
memspec stores | head -2                      # team [ro] N items, global [rw]
ls team-context/specs/*/ | wc -l              # spec pairs present
<spec-checker> team-context/specs             # every folder passes
ls code-repo/docs/adr/ team-context/docs/adr/ # records present, candidates file present
gh pr list -R <team-context> --state open     # nothing left unmerged from Day 1
```

## What Day 1 is not

- Not a one-off. Mode 3 runs again for a subdomain the moment a ticket touches something the
  first pass marked unbuilt; the candidate table gets a row when a design document is added;
  the findings file is a live backlog.
- Not a documentation project. Its outputs are read by agents at every turn, and a wrong one
  is executed, not ignored. The reviewer's job is business truth, not prose.
- Not skippable for a legacy core. It runs before or alongside the verification net of
  [09-legacy-adoption](09-legacy-adoption.md); the spec pass over a legacy monolith surfaced
  a dozen defects and one self-contradicting business rule before any test was written
  `[measured 2026-09-05]`.
