# 0001. Adopt the context standard

- **Status:** accepted
- **Date:** {{YYYY-MM-DD}}
- **Deciders:** {{team}}

## Context

Knowledge about this service was scattered across Confluence, tribal memory, and stale
READMEs. Agentic engineering needs machine-readable, colocated, current context to be
reliable, and the estate needs a consistent shape across 20+ repos so tooling and
onboarding compose.

## Decision

We adopt the org context standard (`context-standard`) at conformance level
**{{L0|L1|L2}}**. Agent instructions (`AGENTS.md`, with a `CLAUDE.md` stub that imports
it for Claude Code), decision records (`docs/adr/`) and current-state docs (`docs/`) live
in this repo, versioned with the code. Memory does not: the repo carries only the
`.memspec.yaml` pointer, and durable memory lives in the team store in the team-context
repo, reached through promote PRs. We pin `context-standard: v0.5` and resync via `adopt.sh`.

## Consequences

- **Positive:** agents and new engineers get consistent, current, in-repo context;
  decisions are auditable; drift across repos is a visible diff.
- **Negative / cost:** docs must be maintained in the same PR as code; a `docs-lint`
  gate is added at L2.
- **Follow-ups:** raise conformance level as the team matures; keep the pinned standard
  version current.
