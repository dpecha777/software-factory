# Distribution — how central updates reach product repos (day 2)

Adoption (`adopt.sh <repo>`) is day 1. This document specifies day 2: how changes to
the standard and its templates propagate to ~20–28 polyglot product repos on an
ongoing basis, and how central updates coexist with local edits to the same files
without clobbering each other or drifting silently.

Status: **implemented in v0.2** (2026-07-16). `propagate.yml` and `fleet-report.yml`
ship credential-gated — inert until the GitHub App of §11 decision 1 exists.

---

## 1. The tension, stated precisely

Teams MUST edit `CLAUDE.md` (no-touch zones, done-when, identity are per-repo by
design) and will edit other seeded docs. The center MUST be able to update the
operating triad, the memspec contract, and the enforcement workflow in every repo.
Today's `adopt.sh` cannot do both: skip-if-exists never delivers updates to an
edited file; `--force` clobbers team content. Any mechanism that patches *inside* a
file both parties edit inherits merge conflicts forever.

**Resolution: make the ownership boundary a *file* boundary, not a region boundary.**
Content is split into three classes with different owners and different update
mechanics. Files are never co-owned; the one unavoidable shared surface (the
`CLAUDE.md` header) is a ~10-line sentinel block that changes only on version bumps.

## 2. The three content classes

| Class | Owner | Update mechanism | Drift guard |
|---|---|---|---|
| **Managed** — byte-identical in every repo | center | whole-file overwrite via bot PR / `adopt.sh --update` | sha256 vs `.context-standard.lock`, verified in `docs-lint` (the OpenAPI-contract pattern) |
| **Seeded** — copied once, then team-owned | team | never overwritten (only `--force`); improvements reach new adoptions only | none — divergence is the point |
| **Referenced** — lives centrally, pinned by version, never copied | center | tag/version moves centrally; nothing in the repo to update | the pin itself |

Classification of the current template:

| Path | Class | Notes |
|---|---|---|
| `docs/standard/agents-core.md` *(new)* | managed | operating triad + memspec contract + model tiering, moved out of `CLAUDE.md` (§3) |
| `docs/adr/0000-template.md`, `docs/adr/README.md` | managed | convention files, no repo-specific content |
| `.github/workflows/docs-lint.yml` | managed (thin caller) | 5-line caller of a reusable workflow; the lint *logic* is referenced, not copied (§6) |
| `CLAUDE.md` | seeded body + managed sentinel header | §3 |
| `docs/manifest.md`, `docs/architecture.md`, `docs/agent-memory.md`, `docs/adr/0001-*` | seeded | placeholders filled by team, owned forever |
| `.memspec/config.yaml`, `.memspec/README.md` | seeded | team tunes retrieval/decay per repo |
| `.context-standard.lock` *(new)* | managed (generated) | written by `adopt.sh`, never hand-edited |
| docs-lint check logic | referenced | reusable workflow in this repo, pinned `@v1` |
| Claude Code skills (adopt/resync helpers) | referenced | the org plugin marketplace (org profile, §10) |

Principle order: **reference > managed copy > seeded copy.** Reference when the
platform supports it (reusable workflows, marketplace plugins, `@` imports); copy
with a checksum when the artifact must physically exist in the repo; seed and let
go when the content is repo-specific by nature.

## 3. `CLAUDE.md`: managed-vs-owned resolution

### Options considered

**(a) Inline managed region** — sentinel comments delimit a managed block inside
`CLAUDE.md`; `docs-lint` checksums the normalized region. Mirrors the OpenAPI
precedent at region granularity. Maximally portable (every agent sees the content
with zero indirection). Costs: bot updates need in-file surgery (awk/sed between
sentinels) instead of `cp`; team edits on adjacent lines produce merge conflicts
with update PRs; checksumming needs normalization rules (line endings, trailing
whitespace); a ~60-line managed block visually dominates a file teams are told to
own.

**(b) Pure `@import` of a pinned shared fragment** — nothing inlined, so nothing
to overwrite. But Claude Code `@path` imports resolve only within the checkout:
the fragment must still be vendored into the repo, so this is (c)-for-one-file
plus an import line, not a copy-free mechanism. And `@import` is Claude Code
syntax; Codex and other non-Claude agents reading the rule file do not expand it,
so the import must never be the *only* route to the content — hence the dual-mode
pointer (`@import` + plain-English imperative) required by `STANDARD.md` §4.
(CLAUDE.md was the canonical rule-file name from the 2026-08-06 decision, v0.4, to
v0.5, which moved the contract to AGENTS.md behind a `CLAUDE.md` stub; see
`STANDARD.md` §4.)

**(c) Whole-file replace** (baseline) — trivially correct update mechanics, but
destroys team-owned no-touch zones and done-when. Rejected outright; this is the
tension, not a resolution.

### Decision: vendored managed fragment + thin sentinel header (hybrid of a and b)

The verbatim org-wide content (operating triad, memspec contract, model tiering)
moves out of `CLAUDE.md` into **`docs/standard/agents-core.md`** — a managed,
byte-identical, checksummed file no team ever edits. `CLAUDE.md` keeps a small
sentinel-delimited header carrying the front-matter and a dual-mode pointer:
a Claude Code `@import` **and** a plain-English imperative that any instruction-
following agent honors. Everything below the sentinel block is team-owned and is
never touched by an update.

Why this wins: updates to the org contract are a conflict-free `cp` + lock bump
(the exact `verify-contract.sh` mechanics already proven in an existing repo family);
merge conflicts with team edits are structurally impossible (different files);
portability is preserved through the imperative sentence (and the group's primary
runtime, Claude Code, gets automatic expansion via `@`). The residual in-file
surgery is confined to a 10-line header that changes only when the version does.

### `CLAUDE.md` v0.2 layout (exact; the file was named `AGENTS.md` until the v0.4 rename)

```markdown
<!-- context-standard:begin -->
<!--
context-standard: v0.2
conformance: L0
starter-kit: {{STARTER_KIT_LINEAGE_OR_none}}
-->
**First, read `docs/standard/agents-core.md`** — the org-wide agent operating
contract (operating triad, memory contract, model tiering). It applies to this
repo in full and is managed by the context-standard: never edit it here, changes go
to the context-standard repo. Claude Code loads it automatically via this import:
@docs/standard/agents-core.md
<!-- context-standard:end · managed header — edits here are overwritten by adopt.sh -->

# {{PRODUCT}} — Agent Operating Contract

**{{PRODUCT}}** is {{ONE_LINE_WHAT_THIS_SERVICE_IS}}.

## Where things live
… (unchanged from v0.1 template — team-owned)

## No-touch zones
… (team-owned)

## Done-when
… (team-owned)
```

`docs/standard/agents-core.md` receives, verbatim from the v0.1 template: the
Operating triad section, the model/effort tiering paragraph, and the entire
Memory (Memspec) section. It contains **no placeholders** — that is what makes
byte-identical checksumming possible. Anything needing a placeholder is by
definition seeded, not managed.

`STANDARD.md` §4 changes accordingly: the MUST-contain list for `CLAUDE.md`
becomes: (1) managed sentinel header, (2) identity, (3) where-things-live,
(4) no-touch zones, (5) done-when; triad + memory move to "MUST vendor
`docs/standard/agents-core.md` unmodified".

## 4. `.context-standard.lock`

Generated by `adopt.sh`, committed, never hand-edited:

```yaml
# Managed by adopt.sh — do not edit. Divergence policy: governance/distribution.md §8.
context-standard: v0.2
managed:
  docs/standard/agents-core.md: "sha256:3f1a…"
  docs/adr/0000-template.md:    "sha256:9c02…"
  docs/adr/README.md:           "sha256:aa41…"
  .github/workflows/docs-lint.yml: "sha256:57de…"
```

The lock is the consumer-side source of truth for "what the center last shipped
here". Local tampering with a managed file → sha mismatch → `docs-lint` fails.
Tampering with the lock *and* the file (a conscious fork) passes locally by
design — divergence must be possible but explicit — and is caught center-side by
the fleet report (§7), which compares each repo's lock against the canonical shas
for its pinned version.

Seeding also appends to the repo's `.gitattributes`:
`docs/standard/* text eol=lf` and `.context-standard.lock text eol=lf`, so an
autocrlf checkout can never silently change the committed bytes the sha covers.

## 5. `adopt.sh` v0.2 changes

The template gains a `template/MANIFEST` declaring each file's class:

```
managed  docs/standard/agents-core.md
managed  docs/adr/0000-template.md
managed  docs/adr/README.md
managed  .github/workflows/docs-lint.yml
seeded   AGENTS.md
stub     CLAUDE.md
seeded   docs/manifest.md
seeded   docs/architecture.md
seeded   docs/agent-memory.md
seeded   docs/adr/0001-adopt-context-standard.md
seeded   .memspec/config.yaml
seeded   .memspec/README.md
```

Behavior matrix (replaces the current single skip-if-exists loop):

| Mode | Managed files | Seeded files | CLAUDE.md sentinel header | Lock |
|---|---|---|---|---|
| *(seed, default)* | copy | copy if missing | included in seeded copy | write |
| `--update` | **overwrite unconditionally** | copy if missing; report drift vs template as FYI | rewrite block in place, body untouched | rewrite |
| `--check` | verify sha vs lock (docs-lint parity, local) | — | verify block structure | verify version |
| `--force` | overwrite | overwrite (destructive, confirmation-prompted) | rewrite | rewrite |

Core additions (proposed, not applied):

```bash
# classify() reads template/MANIFEST; sync_managed replaces the skip logic for managed paths
sync_managed() {          # always safe: teams do not own these files
  local rel="$1" src="$TEMPLATE/$1" dst="$target/$1"
  mkdir -p "$(dirname "$dst")"
  cmp -s "$src" "$dst" 2>/dev/null && { echo "  ok (current): $rel"; return; }
  echo "  sync: $rel"; [ "$dryrun" = 1 ] || cp "$src" "$dst"
}

write_lock() {            # lock = version + sha256 per managed file, from target bytes
  { echo "# Managed by adopt.sh — do not edit."
    echo "context-standard: $VERSION"
    echo "managed:"
    awk '$1=="managed"{print $2}' "$TEMPLATE/MANIFEST" | while read -r rel; do
      printf '  %s: "sha256:%s"\n' "$rel" "$(shasum -a 256 "$target/$rel" | cut -d' ' -f1)"
    done
  } > "$target/.context-standard.lock"
}

update_sentinel() {       # in-place header refresh; the only in-file surgery, ~10 lines
  awk -v hdr="$(sed -n '/<!-- context-standard:begin -->/,/<!-- context-standard:end/p' \
                "$TEMPLATE/CLAUDE.md")" '
    /<!-- context-standard:begin -->/ {inblk=1; print hdr; next}
    /<!-- context-standard:end/       {inblk=0; next}
    !inblk {print}' "$target/CLAUDE.md" > "$target/CLAUDE.md.tmp" \
  && mv "$target/CLAUDE.md.tmp" "$target/CLAUDE.md"
}
```

(`update_sentinel` must preserve the repo's filled front-matter values —
implementation detail: re-inject `conformance:` and `starter-kit:` captured from
the old block; only the version line and pointer text come from the template.)

## 6. `docs-lint` becomes a referenced check, not a copied one

The current `docs-lint.yml` vendors all check logic into every repo — meaning
every improvement to a check is a 25-repo PR wave. v0.2 splits it:

- **In each repo (managed, checksummed):** a thin caller —

  ```yaml
  name: docs-lint
  on:
    pull_request: { paths: ["docs/**", "CLAUDE.md", ".memspec/**", ".context-standard.lock"] }
    push: { branches: [main] }
  permissions: { contents: read }
  jobs:
    docs-lint:
      uses: <org>/context-standard/.github/workflows/docs-lint-reusable.yml@v1
  ```

- **In this repo (referenced):** `docs-lint-reusable.yml` holding all logic. The
  `@v1` tag is the workflow's *interface* major; moving `v1` to a new patch ships
  improved checks to all repos instantly, with no consumer PR. Only an interface
  break (new required input) bumps to `@v2`, which is a MAJOR standard change
  propagated like any other managed-file update.

This mirrors the FluxCD mental model teams already have (repos point at a
versioned source of truth; the pointer, not the logic, lives locally).
Prerequisite: the org Actions setting allowing private-repo workflow reuse
("Accessible from repositories in the organization" on this repo). Fallback if
that is refused: keep `docs-lint.yml` fat and managed — the propagation mechanics
of §8 still work, just noisier.

### Checks (consumer-side, by conformance level)

| Level | Check | Failure meaning |
|---|---|---|
| L0+ | `CLAUDE.md` exists; sentinel block present; front-matter fields parse; the literal pointer line to `docs/standard/agents-core.md` present | header deleted or mangled |
| L0+ | `.memspec/` exists; `.context-standard.lock` exists and parses | adoption incomplete |
| L0+ | sha256 of every `managed:` entry matches the file bytes | **a managed file was edited locally** — the actionable error message says: "this file is org-managed; propose the change as a PR to `<org>/context-standard`, or fork consciously by documenting an ADR and accepting fleet-report visibility" |
| L1+ | ADR filename shape; markdownlint; manifest rows resolve to real files | (as v0.1) |
| L2 | lock's `context-standard:` major == `CURRENT_STANDARD_MAJOR` (a constant baked into the reusable workflow, updated at each standard release — no cross-repo fetch, no extra auth) | repo trails a major beyond the grace window |
| L2 (warn only) | lock minor < current minor | informational annotation, never blocks |

## 7. Center-side: fleet report

A scheduled weekly workflow **in this repo** (org-scoped App token, read-only):
enumerate adopters (repos carrying the `context-standard` topic, self-applied at
adoption — no hand-maintained list), fetch each `.context-standard.lock` via the
API, and publish one table (issue in this repo or the existing dashboards):
repo × pinned version × managed-sha match vs canonical × open unmerged
`chore/context-standard-*` PRs. This is where conscious forks and ignored MAJOR PRs
become visible to the architecture function. Consumer CI never needs cross-repo
credentials; all cross-repo reading happens here, where the credential already
must exist for propagation.

## 8. Push vs pull, by change class

Tied to `governance/VERSIONING.md` semantics (MAJOR = must act, MINOR = at leisure):

| Change class | Version | Channel | Blocking? |
|---|---|---|---|
| Agent-guardrail / policy change in `agents-core.md` (new no-touch class, memory-contract change, supply-chain rule) | **MAJOR** (even if textually additive — policy is never "at leisure") | `propagate.yml` opens a PR in every adopter repo | L2: `docs-lint` red after grace window; L0/L1: warning only |
| Structural change (new required file, moved path, sentinel format) | MAJOR | propagate PR | same |
| Managed-content improvement (wording, new optional section, better ADR template) | MINOR | propagate PR, labeled `advisory` — merge or close freely; closing ≠ drift (lock still matches its pinned version) | never |
| Seeded-template improvement | MINOR | none — reaches new adoptions only; changelog entry; teams may cherry-pick via `adopt.sh --update` drift report | never |
| `docs-lint` logic fix (same interface) | none | reusable-workflow tag move — transparent, zero PRs | n/a |
| `docs-lint` interface change | MAJOR | propagate PR updates the thin caller | L2 |
| New standard adoption / multi-version catch-up | — | pull: team runs `adopt.sh` / `adopt.sh --update` | — |

**Push mechanics — `propagate.yml` in this repo** (~40 lines, plain Actions):
trigger on release (tag `vX.Y`) or `workflow_dispatch`; enumerate adopters by
topic; for each: clone, run `./adopt.sh --update <checkout>`, and if the tree
changed, push branch `chore/context-standard-vX.Y` and open a PR (`gh pr create`)
whose body is the CHANGELOG excerpt + MAJOR/MINOR label. Idempotent: re-runs
update the existing branch.

**Why not Renovate as the file-sync channel:** Renovate stays the dependency-
currency channel it already is in every kit. Making it sync file *contents* needs
a custom datasource plus `postUpgradeTasks`, which are unavailable on hosted
Renovate and awkward self-hosted — more configuration than the 40-line workflow,
on infra (Actions + `gh`) the org already runs. Renovate MAY additionally pin
the `@v1` reusable-workflow ref via its existing github-actions manager; that
comes free.

**Why not `copier`/`cruft`:** they solve template re-sync via answer files and
three-way merges — strictly more machinery than needed once the managed/seeded
split removes the co-ownership problem, and a new toolchain dependency for every
team against `bash + sha256 + gh` that exists everywhere already. Re-evaluate
only if the managed set grows templated (placeholder-bearing) files that must
update in place — that is the one case checksummed copies cannot serve.

## 9. Starter-kit code updates: the fork story, honestly

A repo created from a kit shares no ongoing merge relationship with it. "Use this
template" produces no common git history; even with a preserved `template` remote,
merging kit deltas into a 6-month-diverged fork is conflict archaeology nobody
will do. **Kit code is copy-time inheritance. Post-fork, code does not propagate
— and the design does not pretend otherwise.** What actually keeps forks current,
per channel:

1. **Dependency currency** → Renovate (`config:recommended`, already in every
   kit) runs *in the fork*, independent of the kit. This covers the majority of
   ongoing "kit updates" by volume without any kit→fork mechanism.
2. **Cross-cutting conventions with enforcement value** (contract-drift guard
   scripts, CI patterns, docs-lint) → promote out of the kit into the managed or
   referenced class of *this* standard, and they propagate via §8. The
   `verify-contract.sh` + pinned-sha pattern is already effectively managed
   content; a kit convention that must hold fleet-wide has outgrown the kit.
3. **Everything else** (a kit adopts a better logging setup, a new test pattern)
   → does not propagate. The kit tags releases and keeps a CHANGELOG; forks
   record their lineage in `CLAUDE.md` front-matter (`starter-kit:`), which makes
   the audience of each kit release enumerable. Adoption is a conscious per-team
   cherry-pick. Optional accelerator, not load-bearing: the per-team `*-team-specs`
   Claude Code actions can take a standing task "diff our repo against kit release
   notes `vN`, propose applicable changes as a PR" — agent-assisted cherry-pick,
   using marketplace plugins already in place.

The rule of thumb: **if a kit improvement must reach every fork, it was never
kit content — it is standard content.** Move it up a layer and let §8 carry it.

## 10. Organisation profile wiring (layer, not core)

Everything above is neutral-core mechanism. An organisation's overlay (belongs in
`<org>-profile.md` once accepted) typically sets:

- Adopter discovery: GitHub topic `context-standard` on org repos, applied at
  adoption (adopt.sh prints the reminder; fleet report treats missing topic +
  present lock as a finding).
- Propagation credential: an org GitHub App (contents:write, pull-requests:write
  on product repos) installed org-wide; used by `propagate.yml` and read-only by
  the fleet report.
- The org plugin marketplace ships a `context-standard` plugin: `/adopt-standard` and
  `/resync-standard` skills wrapping `adopt.sh`, so MINOR resyncs are a slash
  command; the plugin self-updates via the marketplace (a referenced channel —
  updating the skill needs no repo PRs).
- Grace window for MAJOR at L2: **2 sprints** from propagate-PR open to
  docs-lint red (recommendation; see open decisions).
- Legacy repos being phased out stay L0: they receive propagate PRs but docs-lint
  never blocks them, so no effort goes into documenting code that is being decommissioned.

## 11. Open decisions (org calls, not design choices)

1. **Bot identity** for propagate + fleet report: dedicated GitHub App (recommended:
   scoped, auditable, no personal PAT) vs an existing org machine user. Owner:
   whoever governs org GitHub settings.
2. **Reusable-workflow home**: this repo vs a dedicated shared-workflows
   repo, and flipping the org Actions access setting for private reuse.
   Recommended: this repo until a second shared workflow exists.
3. **Enforcement SLA**: confirm the 2-sprint MAJOR grace window and whether
   `docs-lint` becomes a required status check (branch protection) for L2 repos —
   that is the difference between "red check" and "cannot merge".

## 12. Summary of v0.2 deltas this design implies

- `template/CLAUDE.md`: split — sentinel header + team body; triad/memory content
  moves to new `template/docs/standard/agents-core.md` (placeholder-free).
- New: `template/MANIFEST`, `.context-standard.lock` (generated), `.gitattributes`
  entries for managed paths.
- `adopt.sh`: class-aware modes per §5 (`sync_managed`, `write_lock`,
  `update_sentinel`, `--check`).
- `docs-lint.yml`: thin caller → `docs-lint-reusable.yml` here, checks per §6.
- New in this repo: `propagate.yml`, `fleet-report.yml`.
- `STANDARD.md` §4 and §7 updated to reference the managed/seeded/referenced
  classes; `VERSIONING.md` gains the push/pull matrix pointer.
