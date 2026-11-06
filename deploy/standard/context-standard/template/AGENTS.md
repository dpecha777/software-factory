<!-- context-standard:begin -->
<!--
context-standard: v0.5
conformance: L0
starter-kit: {{STARTER_KIT_LINEAGE_OR_none}}
team-context: unset
-->
**First, read `docs/standard/agents-core.md`** — the org-wide agent operating
contract (operating triad, memory contract, model tiering). It applies to this
repo in full and is managed by the context-standard: never edit it here, changes go
to the context-standard repo. Claude Code reaches this file through `CLAUDE.md`
(`@AGENTS.md`) and loads the contract via this import; other agents open it by path:
@docs/standard/agents-core.md
<!-- Team layer key semantics: `<org>/<repo>` = wired (team import injected above by
     adopt.sh --set-team or the devcontainer's set-team.sh), `none` = deliberate opt-out,
     `unset` = the team question is still unanswered.
     Never hand-edit inside this block — adopt.sh overwrites it. -->
<!-- context-standard:end · managed header — edits inside this block are overwritten by adopt.sh -->

# {{PRODUCT}} — Agent Operating Contract

**{{PRODUCT}}** is {{ONE_LINE_WHAT_THIS_SERVICE_IS}}.

Everything below this line is team-owned. Central updates never touch it.

## No-touch zones

Do NOT modify these without explicit human sign-off in the PR:

- `{{MIGRATIONS_PATH}}` — schema migrations (never edit an applied migration).
- Generated code (`{{GENERATED_PATHS}}`) — regenerate from source, never hand-edit.
- Security/auth config, secrets, `{{PAYMENT_OR_MONEY_PATHS}}`.
- `.github/workflows/**` release/deploy gates.
- `docs/standard/**` and `.context-standard.lock` — org-managed (see header).

<!-- TODO(review): fill the real paths per repo at adopt time. -->

## Done-when

A change is complete only when these gates pass locally and in CI:

- Build / test / lint green — the invocations are in **Commands** below.
- Contract-drift guard green (if this repo consumes a shared contract).
- ADR added for any architectural decision.
- your working memory updated for anything non-obvious you learned — durable team
  knowledge travels via promote PRs into the team store, never direct edits.

## Commands

Canonical invocations for this repo (Done-when points into these):

```
{{BUILD_COMMAND}}    # e.g. ./gradlew build   |  npm run build
{{TEST_COMMAND}}     # e.g. ./gradlew check   |  npm test && npm run lint
{{RUN_COMMAND}}      # e.g. ./gradlew bootRun  |  npm run dev
```

## Repo-specific notes

{{Anything else an agent must know that is unique to this repo: local conventions,
sharp edges, links to the relevant runbooks. See also docs/agent-memory.md.}}
