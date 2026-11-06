# Changelog — Repository Context Standard

Versioned `vMAJOR.MINOR`. MAJOR = a change a repo must act on to stay conformant
(new required file, moved path). MINOR = additive or clarifying (new optional
convention, doc fixes). See `governance/VERSIONING.md`.

## v0.5 — 2026-11-06

A repo must act: the contract moves from `CLAUDE.md` to `AGENTS.md`, and `CLAUDE.md`
becomes a stub (`adopt.sh --migrate-rule-file`). A v0.4 repo still passes `--check`,
with a warning, until it migrates.

- Rule file is `AGENTS.md` (template, MANIFEST, adopt.sh, STANDARD §2 and §4): every
  agent tool reads it natively. `CLAUDE.md` is a new `stub` file class whose required
  line is `@AGENTS.md`, because Claude Code loads `AGENTS.md` only when no
  `CLAUDE.md`/`.claude/CLAUDE.md`/`CLAUDE.local.md` sits in the repo or a parent
  directory (`~/.claude/CLAUDE.md` counts for every repo under `$HOME`).
- adopt.sh: seed writes `AGENTS.md` + the stub; an existing `CLAUDE.md` without a
  sentinel keeps its lines below the prepended import (was: left without a sentinel, so
  `--set-team` refused). `--migrate-rule-file` now runs v0.4 `CLAUDE.md` → `AGENTS.md` +
  stub; `--check` fails a v0.5 repo whose `CLAUDE.md` lacks `@AGENTS.md` and warns on a
  v0.4 layout. Paths it writes are refused when they (or a parent directory) are symlinks;
  rewrites go through a `mktemp` file; `.gitattributes` pins every managed file to LF.
  `adopt.test.sh` pins all of it.
- `docs-lint.yml` also triggers on `AGENTS.md` changes (managed file: its sha changes).
- Seeded ADR 0001 describes the pointer topology (no in-repo store) and pins v0.5.

## v0.4 — 2026-08-18 (draft)

MAJOR — a repo must act: rename AGENTS.md → CLAUDE.md and answer the
team-context question.

- Rule file is `CLAUDE.md` throughout (standard, template, MANIFEST, adopt.sh);
  encodes the 2026-08-06 org decision.
- Team layer: org / team / repo stack (§1a); team knowledge lives in a
  `*-team-context` repo, mounted read-only at `/workspaces/<team>-team-context`,
  imported via the sentinel (§8, read path only).
- Sentinel gains a `team-context:` key (`<org>/<repo>` | `none` | `unset`);
  the team `@import` is derived from it, never hand-edited (§4).
- New MUST `Commands` section in the repo CLAUDE.md (§4).
- L0 requires CLAUDE.md + a resolved `team-context:` value; L2 lint checks the
  import matches the key (§3).
- adopt.sh: new `--set-team` and `--migrate-rule-file`; `--update` writes
  `team-context: unset` + warns when the key is absent.
- Memory binding (§6): repos carry a committed `.memspec.yaml` pointer, no
  local store; team store is `.memspec/` in the team-context repo; writes via
  promote PRs only; hygiene is event-attached, no scheduled cleanup.
- Team-context `CLAUDE.md` MUST carry a `## Code repositories` section listing
  the team's code repositories, one `org/repo` slug per line (`none` when the
  team owns none) (§8.1) — the single parseable place a consumer resolves the
  team's code from the team-context repo alone (`pm-workspace-setup` reads it to
  populate a PM workspace's `POINTERS.md`; any agent uses it to locate a domain).
- Permanent home: `<org>/group-standards/context-standard/`;
  `siimvene/context-standard` (v0.3) to be archived at release.

## v0.3 — 2026-07-17 (draft)

Renamed: doc-standard → **context-standard** (Repository Context Standard). MAJOR:
sentinel markers, lock filename (.context-standard.lock), front-matter key, GitHub
topic, and branch prefixes all change. Rationale: docs are the storage format, not
the product — the standard governs the context an agent (or engineer) finds and
trusts in a repo. Thin-caller re-pointed to <org>/starter-kits pending org
re-home. Nothing had adopted v0.2; no migration.

## v0.2 — 2026-07-16 (draft)

Day-2 distribution model implemented (design: `governance/distribution.md`). MAJOR
restructure of `AGENTS.md` and `adopt.sh`; v0.1 was never adopted, so no migration.

- `AGENTS.md` split: org-wide content (operating triad, model tiering, memspec
  contract) moved to new managed file `docs/standard/agents-core.md` (placeholder-free,
  byte-identical, checksummed). `AGENTS.md` keeps a sentinel-delimited managed header
  (version pin + dual-mode pointer: `@import` + plain-English imperative) and a fully
  team-owned body.
- New `template/MANIFEST` declaring each file managed/seeded.
- New `.context-standard.lock` (generated): standard version + sha256 per managed file;
  `.gitattributes` entries force LF on sha-covered paths.
- `adopt.sh` rewritten class-aware: seed / `--update` (managed overwrite, sentinel
  rewrite preserving team front-matter, seeded untouched) / `--check` (CI-parity
  verify) / `--force`; all `--dry-run`able.
- `docs-lint.yml` became a thin caller of `docs-lint-reusable.yml@v1` in this repo
  (check improvements ship by tag move, zero consumer PRs). Checks are
  conformance-level-aware; managed-sha verification added.
- New `propagate.yml` (release → `chore/context-standard-vX.Y` PRs to all adopters,
  topic-discovered; `repos` input for day-1 onboarding waves) and `fleet-report.yml`
  (weekly adopter audit). Both skip gracefully until the GitHub App credential exists.
- `STANDARD.md` §2/§4/§7 updated for the managed/seeded/referenced classes.

## v0.1 — 2026-07-16 (draft)

Initial draft for review.

- Four-layer model (Delta / State / Decisions / Memory).
- Required layout: `AGENTS.md`, `.memspec/`, `docs/{manifest,architecture,agent-memory}.md`, `docs/adr/`, `docs-lint.yml`.
- Staged conformance L0 → L1 → L2.
- `AGENTS.md` contract: front-matter + identity + operating triad + memspec contract + no-touch zones + done-when.
- MADR-lite ADRs.
- `adopt.sh` for seeding and resync; version pinning in front-matter.
- Neutral core + separate group adoption profile.
