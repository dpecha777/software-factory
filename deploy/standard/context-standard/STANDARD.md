# Repository Context Standard — v0.4

Normative conventions for **where project knowledge lives and how a repo binds to
it**: agent instructions, machine-operated memory, human decision records, and
current-state docs. Repo-true knowledge is colocated with the code, reviewed in the
same PR, versioned with the same commit; team-true knowledge lives once in the
team-context repo and is bound, not copied (§0, §1a).

The keywords MUST / SHOULD / MAY are used per RFC 2119.

---

## 0. Why placement, not colocation everywhere

Docs in a separate wiki rot the moment the code moves — so repo-true knowledge
(rules, state docs, ADRs) lives in the same repo as the code it describes, and
the developer wiki *links* here rather than holding source of truth. The same
rot argument cuts the other way at a wider radius: knowledge true for a whole
team, copied into N repos, drifts N ways. So team knowledge and team memory
are NOT colocated — they live once in the team-context repo (§1a, §8) and
every code repo *binds* to them. The rule in one line: knowledge lives at the
highest layer where it is true, and everything else is a link, an import, or
a pointer. If a doc can go stale without a failing check, it will.

## 1. The four knowledge layers

| Layer | Lives in | Answers | Operated by | Lifecycle |
|---|---|---|---|---|
| **Delta** | Jira / PR description | "what changed this iteration, and why" | humans | per ticket |
| **State** | `docs/**/*.md` + `docs/manifest.md` | "what is true *now*" | humans + agents | edited to match reality |
| **Decisions** | `docs/adr/NNNN-*.md` | "*why* the state is what it is" | humans | append-only + supersede |
| **Memory** | team store, bound via `.memspec.yaml` | "facts / decisions / procedures, with evidence" | agents (read); promote PRs (write) | witness-tracked; write path is §8 |

State-vs-delta is the group's own Unified-proposal doctrine (Jira = delta; per-module
`*.md` + `manifest.md` = current state). This standard adopts it verbatim and adds
the machine layer (memspec) and the decision layer (ADRs) beside it. Nothing here
overrides the Unified proposal — it operationalizes it.

## 1a. The three-layer knowledge stack (org / team / repo)

The four layers above describe *kinds* of knowledge inside one repo. Orthogonal to
that is *where the knowledge is true* — for one repo, for a whole team, or for the
org. v0.4 makes that split explicit and gives each layer exactly one home.

| Layer | Lives in | Carries | Reaches the agent via |
|---|---|---|---|
| **Org** | group-standards: `agents-core.md` | org agent contract, operating triad, model/effort tiering | vendored `docs/standard/agents-core.md` (managed) |
| **Team** | `<org>/<team>-team-context` | domain knowledge, specs, cross-repo decisions, team memory | fixed-path mount + `@import` from the repo shim (NEW in v0.4) |
| **Repo** | `<repo>/AGENTS.md` (+ `CLAUDE.md` stub) + `docs/` + `.memspec.yaml` | build/test/run, protected areas, repo conventions, pointer binding memory to the team store | native cwd load (unchanged) |

**Rule of placement: knowledge goes in the highest layer where it is true.** If a
fact holds for every repo the team owns, it belongs in team-context, not copied into
N repo shims. The repo `AGENTS.md` carries only what is cwd-coupled — the invocations,
the no-touch paths, the sharp edges specific to *this* checkout. Duplicating team or
org content per repo recreates exactly the drift the split exists to kill.

The team layer's read path (mount + import) is specified in §8. Its write path
(batched promote PRs) is specified in §6 and §8; only the promote cadence and
per-team reviewer assignment sit outside this standard.

## 2. Required layout (per code repo)

```
<repo>/
├── AGENTS.md                        # MUST — managed sentinel header + team-owned body (v0.5)
├── CLAUDE.md                        # MUST — stub carrying `@AGENTS.md` (Claude Code entry point)
├── .context-standard.lock               # MUST — generated receipt: version + managed-file shas
├── .memspec.yaml                    # MUST — pointer binding this repo to the team memspec store
├── docs/
│   ├── standard/
│   │   └── agents-core.md           # MUST — org agent contract (managed, never edited here)
│   ├── manifest.md                  # MUST@L1 — module → state-doc index
│   ├── architecture.md              # MUST@L1 — current-state architecture
│   ├── agent-memory.md              # SHOULD  — durable agent-facing notes
│   ├── adr/                         # MUST  — decision records
│   │   ├── README.md
│   │   ├── 0000-template.md
│   │   └── NNNN-<kebab-title>.md
│   └── runbooks/                    # MAY
└── .github/workflows/docs-lint.yml  # MUST@L2 — thin caller of the shared check workflow
```

Every file is either **managed** (center-owned, byte-identical, checksummed in
`.context-standard.lock`, overwritten by updates), **seeded** (copied once at adoption,
team-owned forever), or **referenced** (lives centrally, pinned, nothing to copy).
The class of each template file is declared in `template/MANIFEST`; the full
day-2 mechanics are in `governance/distribution.md`.

The **team** layer is not a file in this layout — it lives in a separate
`*-team-context` repo, declared by the `team-context:` front-matter key in `CLAUDE.md`
and mounted at a fixed path in the sandbox (§4, §8).

**Polyglot-safe by design.** This standard governs documentation and memory only.
It imposes nothing on build tooling, language, or framework, so a Spring Boot repo
and a Nuxt repo carry the identical doc skeleton. Stack-specific conventions belong
in the relevant starter kit, not here.

## 3. Conformance levels — adopt gradually

Adoption is **staged**. A repo declares its level in `CLAUDE.md`; it ratchets up as
the team matures. **No repo is expected to reach L2 on day one.** Rules tighten with
observed maturity, not by mandate — that is deliberate, and it is also the anti-drift
mechanism: a repo can sit at L0 honestly instead of faking L2 compliance.

- **L0 — Seeded** (~15 min, every repo starts here)
  `CLAUDE.md` present with the standard header + memspec contract; the `team-context:`
  front-matter key present with a **resolved** value (`<org>/<repo>` or `none` — a
  bare `unset` does **not** pass L0; a migrated repo can't sit at L0 with the team
  question unanswered); `.memspec.yaml` pointer present;
  `docs/adr/0001-adopt-context-standard.md` recorded.
- **L1 — Documented**
  `docs/architecture.md` reflects current reality; `docs/manifest.md` indexes the
  modules; every *currently-live* architectural decision has an ADR; `agent-memory.md`
  seeded.
- **L2 — Enforced**
  `docs-lint` CI is required and green; the adopted standard version is pinned;
  module state docs are complete and reconciled against the bound team store. `docs-lint`
  additionally checks that the team import path inside the sentinel matches the
  `team-context:` front-matter key (drift tripwire).

A team picks its target level per repo. Promotion is a PR that flips the level in
`CLAUDE.md` and satisfies the gate. Demotion is allowed and honest.

## 4. `AGENTS.md` contract (and the `CLAUDE.md` stub)

Root file, since v0.5. `AGENTS.md` is the name every agent tool reads natively (Codex,
Gemini CLI, Pi, Cursor, opencode), and teams run more than one of them. Claude Code
reads it too, but only as a fallback: its built-in AGENTS.md support skips the file
whenever a `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the repo or
**any parent directory**, and `~/.claude/CLAUDE.md` is one for every repo under
`$HOME` (measured 2026-11-06, Claude Code 2.1.316; ADR 0019 in software-factory). So
the failure asymmetry that made `CLAUDE.md` canonical in v0.4 still holds, and it is
closed with a stub: the repo MUST also carry a tracked `CLAUDE.md` whose contract line
is `@AGENTS.md`. A team MAY add Claude-only lines to the stub; repo rules go in
`AGENTS.md`. Personal notes go in `CLAUDE.local.md`, which stays gitignored.

`AGENTS.md` MUST contain, in order:

1. **Managed sentinel header** (`<!-- context-standard:begin -->` … `end`) — front-matter:

   ```
   context-standard: vX.Y
   conformance: L0|L1|L2
   starter-kit: <lineage or "none">
   team-context: <org>/<team>-team-context   # or "none", or "unset"
   ```

   plus the pointer to `docs/standard/agents-core.md`, dual-mode: a Claude Code
   `@import` **and** a plain-English imperative any instruction-following agent honors.
   The `@docs/standard/agents-core.md` pointer stays **MUST** — `adopt.sh --check`
   greps for it and the org layer loads through it.

   Below the front-matter, still inside the sentinel block, the dual-mode **team
   import** (present only when the key is `<org>/<repo>`; absent for `none` and
   `unset`):

   ```
   @/workspaces/<team>-team-context/CLAUDE.md
   <!-- Non-Claude agents: read /workspaces/<team>-team-context/CLAUDE.md before working. -->
   ```

   The import path is derived from the `team-context:` key by `adopt.sh --set-team` /
   `--update`; **teams never hand-edit inside the sentinel.** This whole block is
   rewritten by `adopt.sh` (team front-matter values preserved); teams MUST NOT edit
   inside it. Key values:

   - **`<org>/<repo>`** — wired: import + boot mount active.
   - **`none`** — deliberate opt-out (single-repo teams, sandbox/experimental repos,
     public repos). Suppresses the import and the boot tripwire. A legal *permanent*
     state, not merely transitional.
   - **`unset`** — what `--update` writes when migrating a pre-v0.4 repo that never
     ran `--set-team`. Keeps the boot tripwire firing until someone answers; a
     migrated repo MUST NOT silently pass as opted-out. Does not satisfy L0.
2. **Identity** — one line: what this service is.
3. **No-touch zones** — paths an agent MUST NOT modify without explicit human sign-off (migrations, generated code, security config, payment paths).
4. **Done-when** — the mechanical definition of done for this repo: the *gates* that prove a change is complete (build green, contract-drift guard, ADR added, memspec updated). Points into the Commands section for the exact invocations.
5. **Commands** — canonical build / test / run / lint invocations for this repo.
   Done-when holds the gates; Commands holds the invocations Done-when points into.
   This is the cwd-coupled payload that justifies the file existing per repo.

The org-wide content — operating triad (Bounded, Provably done, Owned), model/effort
tiering, and the memspec agent contract — lives in `docs/standard/agents-core.md`,
which the repo MUST vendor unmodified. Everything below the sentinel header is
team-owned and is never touched by a central update.

The seeded body baseline (decided 2026-08-19) is the graduated project template
(`templates/claude-md/project/CLAUDE.md`) **minus** the sections `agents-core.md`
already covers org-wide (model/effort tiering, guardrails, verification,
response format) — the shim must stay thin. Duplicating agents-core content in
every repo recreates the drift the layer split exists to kill.

## 5. Decision records (ADRs)

MADR-lite. One decision per file. Filename `NNNN-<kebab-title>.md`, zero-padded,
monotonically increasing. Status is one of `proposed | accepted | superseded-by-NNNN
| deprecated`. **Never edit an accepted ADR's decision** — supersede it with a new
record and update both statuses. ADRs capture *why*; they are the audit trail a due
diligence reviewer reads.

## 6. Memory binding (memspec)

Code repos carry **no** memspec store of their own. Each repo MUST carry a committed
`.memspec.yaml` pointer at its root binding it to the team memspec store (§8); the
pointer declares that store as a read layer and resolves it at the fixed team-context
mount path (§8.2). This is the only durable memory a code repo references.

- The team store (`.memspec/` at the team-context repo root, §8.1) is the **only** durable
  home for team knowledge. Repos bind to it; they do not copy it.
- An agent's working memory is disposable **local scratch** — whatever memspec holds
  locally during a session. It MUST NOT be committed to the code repo.
- Writes to the team store happen **exclusively** via promote PRs (§8): the agent
  promotes a scratch candidate, a code-owner reviews it, the PR merges. Agents never
  write the team store directly; it is read-only to them.
- Cross-product or org-wide knowledge stays in the org/operator store, never in a
  product repo. Secrets never enter memory.
- **Hygiene is event-attached, not scheduled.** The promote PR grooms the store it
  writes to (stale, contradicted, and duplicate claims ride the same PR as supersede
  proposals), spec regeneration cross-checks memory against changed behavior, and the
  sandbox boot nags on aging scratch and drift. There is deliberately no cleanup cron:
  hygiene frequency tracks write frequency, and every grooming pass happens in front of
  a human who is already reviewing.

## 7. Versioning & governance

This standard is versioned `vMAJOR.MINOR` (see `governance/VERSIONING.md`). A repo
records the version it adopted in `CLAUDE.md` front-matter and `.context-standard.lock`.
`docs-lint` verifies managed-file shas against the lock and flags a repo that trails
the current major. MAJOR updates arrive as automatically-opened `chore/context-standard-vX.Y`
PRs; MINOR updates are advisory; check-logic fixes ship via the referenced reusable
workflow with no PRs at all. Full push/pull matrix, fleet report, and the
managed/seeded/referenced mechanics: `governance/distribution.md`. One canonical
template, forked per repo — divergence is visible in a diff and on the weekly fleet
report, never silent drift across 20+ repos.

## 8. Team-context repo contract

The team layer (§1a) lives in a dedicated `*-team-context` repo. This section
specifies the **read path** — what makes such a repo importable and how it
reaches the agent — plus the store location repos bind to (§6). The write path is
**promote PRs** (§6): an agent promotes a local-scratch candidate and a code-owner
merges it; agents never write the team store directly. The detailed promote-PR gates
are governed by the team-context operating model. PM ideation stays out of
team-context (2026-07-24 decision).

### 8.1 Minimum contract

```
<team>-team-context/
├── CLAUDE.md          # MUST — the team's agent-facing front door; small, curated
├── specs/             # SHOULD — current-state specs (state, not delta)
├── docs/              # MAY — decisions, onboarding, domain notes
├── rules/             # MAY — review rule packs wired into consort (§8.4)
├── .memspec/          # SHOULD — team memspec store, engine-standard layout (records
│                      #        under .memspec/memory/); read-only to agents, writes via
│                      #        promote PRs only
└── CODEOWNERS         # MUST — .memspec/** and specs/** → team lead/devs; the PM
                       #        reviews specs for business truth through the code
                       #        owner, never as a merge gate (2026-08-18 decision).
                       #        Branch protection requires code-owner review (the
                       #        gates are mechanics, not etiquette)
```

The team-context `CLAUDE.md` is what repo shims import, so it MUST hold only
current-state, agent-useful content and SHOULD stay under ~150 lines, linking
outward rather than inlining.

The team-context `CLAUDE.md` MUST carry a `## Code repositories` section listing
the code repositories the team owns, one `org/repo` slug per line (a short
trailing note per line is fine). A team that genuinely owns none writes `none`
in that section, so an absent section is a real omission a lint can catch, never
an ambiguous empty case. This is the single place a consumer resolves the team's
code from the team-context repo alone: `pm-workspace-setup` reads this section to
populate a PM workspace's `POINTERS.md`, and any agent uses it to find where a
domain is implemented.

### 8.2 Mount convention

Fixed path: **`/workspaces/<team>-team-context`**, cloned read-only by devcontainer
setup, default branch, pulled on boot. A fetch failure is not a boot failure: warn
and continue with the stale checkout. No checkout at all → loud warn.

### 8.3 Honest failure mode outside the sandbox

Claude Code silently skips a missing `@import` path. On a bare host checkout or a CI
clone the team layer therefore degrades to *absent, with no signal*. The fixed path
makes the import deterministic **wherever setup ran**; it does not conjure the clone.
The standard says so rather than pretending otherwise:

- (a) The sentinel's plain-English comment names the path, so a capable agent can
  self-serve the clone.
- (b) CI/cloud pipelines that want the team layer MUST add the documented one-line
  clone step:
  `git clone --depth 1 <team-context> /workspaces/<team>-team-context`.
- (c) The devcontainer remains the only surface where presence is *guaranteed*.

### 8.4 Review-side wiring (consort)

Codex never reads `CLAUDE.md` or the mounted team-context — consort feeds it composed
prompts plus rule packs (`CONSORT_RULE_PACKS` → repo `.claude/rules/` → rule-packs
plugin cache). A team's domain invariants in team-context are therefore invisible to
cross-vendor review unless wired in. The cheap fix, with zero consort changes: a
team-context repo MAY carry a `rules/` directory, and devcontainer setup appends
`/workspaces/<team>-team-context/rules` to `CONSORT_RULE_PACKS` when it exists.
Generation context and review rubric stay separate concerns; the mount serves both.

---

*This is the neutral core. An organisation's adoption profile (estate-specific no-touch
zones, required starter-kit lineages, the L2 CI gate wired to its shared workflows) lives in
`governance/<org>-profile.md` and is layered on top, so the core stays employer-agnostic.*
