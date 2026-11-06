# 0019. The repo contract is AGENTS.md, behind a CLAUDE.md stub

- **Status:** accepted
- **Date:** 2026-11-06
- **Deciders:** the operator (chief architect)
- **Supersedes:** the group's 2026-08-06 decision that made `CLAUDE.md` the rule file (context standard v0.4)

## Context

Context standard v0.4 named `CLAUDE.md` the repo rule file. The argument was the failure
asymmetry: Claude Code was the majority tool, it did not read `AGENTS.md`, and a missing
`CLAUDE.md` fails silently. Other tools were served by a plain-English pointer sentence.

Two things moved. Teams now run several agent tools side by side (Codex, Gemini CLI, Pi,
opencode, Cursor), all of which read `AGENTS.md` natively and none of which read `CLAUDE.md`.
And Claude Code gained built-in `AGENTS.md` support, which suggests the stub is no longer
needed. It is: the support is a fallback. Its default mode loads `AGENTS.md` only when no
`CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the repo or in any parent
directory, and `~/.claude/CLAUDE.md` is such a file for every repo under the user's home.

Probed with `claude -p` and a marker word in `AGENTS.md`, Claude Code 2.1.316
`[measured 2026-11-06]`:

| Setup | AGENTS.md loaded |
|---|---|
| `AGENTS.md` only, repo outside `$HOME` | yes |
| `AGENTS.md` only, repo under `$HOME` with a `~/.claude/CLAUDE.md` | no |
| `AGENTS.md` and a personal `CLAUDE.local.md` | no |
| a parent directory holding `.claude/CLAUDE.md` | no |
| `CLAUDE.md` containing `@AGENTS.md`, plus `CLAUDE.local.md` | yes |

## Decision

We will keep the contract in `AGENTS.md` and make `CLAUDE.md` a tracked stub whose required
line is `@AGENTS.md`.

- **`AGENTS.md`** carries the managed sentinel header and the team-owned body (the v0.4
  `CLAUDE.md` content, unchanged in shape).
- **`CLAUDE.md`** is a new `stub` file class: written when absent, required to carry
  `@AGENTS.md`, free to carry Claude-only lines below it, not checksummed.
- **Personal instructions live in `CLAUDE.local.md`**, gitignored. Repos that gitignored
  `CLAUDE.md` or `AGENTS.md` as personal files un-ignore both.
- **`adopt.sh` enforces it:** seed writes both files and prepends the import to an existing
  `CLAUDE.md`; `--migrate-rule-file` moves a v0.4 contract into `AGENTS.md` with history;
  `--check` fails a missing import and warns on a v0.4 layout, so the fleet is not broken by
  the release. `adopt.test.sh` pins each path, a missing import included.

## Consequences

- **Positive:** one contract file every agent tool reads; Claude Code reaches it through an
  import that does not depend on what sits above the repo; the old seed defect (an existing
  `CLAUDE.md` left without a sentinel) is gone.
- **Cost:** every v0.4 repo runs one migration; a repo that gitignored `CLAUDE.md` makes each
  developer move a personal file before pulling, because git overwrites an ignored file when a
  tracked one arrives `[measured 2026-11-05]`.
- **Follow-ups:** the group repo of the standard takes the same change (operator); the
  `docs-lint` reusable workflow checks `AGENTS.md` and the stub (standard owner); team-context
  repos keep `CLAUDE.md` until their own move is decided, since repo shims import them by that name.

## Alternatives considered

- **`AGENTS.md` alone, relying on the fallback:** silently empty for most developers, per the
  table above.
- **Keep `CLAUDE.md` canonical with an `AGENTS.md` pointer:** inverts the majority. Every
  non-Claude tool then reads a pointer and has to follow it, and they do not expand imports.
- **A symlink `CLAUDE.md -> AGENTS.md`:** loads the same text twice where both are read, and
  symlinks fail on some Windows checkouts and archive exports.
- **Set Claude Code's instruction-file mode to load both files:** per machine, not per repo;
  nothing in the repo can enforce it.
