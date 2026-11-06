# Versioning & governance

The standard is versioned `vMAJOR.MINOR`. This is the mechanism that keeps 20+ repos
converged without central enforcement: every repo pins the version it adopted, and
drift becomes a visible diff instead of silent rot.

## Version semantics

- **MAJOR** — a change a conformant repo must *act on*: a new required file, a moved
  path, a renamed convention. Bumping MAJOR means repos on the old major will be
  flagged by `docs-lint` until they resync.
- **MINOR** — additive or clarifying: a new optional convention, a better template,
  doc fixes. Safe to ignore; adopt at leisure.

## How a repo pins its version

`AGENTS.md` front-matter carries `context-standard: vX.Y` (`CLAUDE.md` on a v0.4 repo). `docs-lint` checks the field
exists and (at L2) that the major matches the current standard.

The delivery mechanics per change class (auto-PR vs advisory vs tag move) are
specified in `distribution.md` §8 — this file only defines what MAJOR/MINOR *mean*.

## How the standard evolves

1. Propose the change as a PR against **this** repo. Non-trivial changes get an ADR in
   `governance/adr/` here (the standard eats its own dog food).
2. Merge → bump `CHANGELOG.md` and the version stamped in `template/AGENTS.md`.
3. Teams resync: `./adopt.sh --update <repo>`. The script reports every file it would
   change; a human reviews the diff and commits.

## Ownership

- The standard has an owner (the architecture function) who merges changes here.
- Each product team owns its *adoption*: which conformance level, when to resync.
- Divergence is allowed but must be explicit — a repo may hold an old version on
  purpose; `docs-lint` will keep surfacing it so the choice stays conscious.

<!-- TODO(review): name the owner + the resync cadence expectation (e.g. within one
     minor of current within a sprint). -->
