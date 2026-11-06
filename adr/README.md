# Decision records of this design

The design's own decisions, in the format it asks adopters to use
([templates/adr.md](../templates/adr.md)).

| # | Decision | Status |
|---|---|---|
| [0001](0001-adopt-a-standard-not-build-a-harness.md) | Adopt a standard; do not build a harness | accepted |
| [0002](0002-mechanical-sensors-before-inferential-review.md) | Mechanical sensors run before any inferential review | accepted |
| [0003](0003-cross-vendor-non-inheriting-review-is-the-merge-gate.md) | The merge gate is a cross-vendor, non-inheriting review, verified before action | accepted |
| [0004](0004-ratchets-not-floors-baselines-are-human-decisions.md) | Ratchets, not floors; baselines are a person's reviewed commit | accepted |
| [0005](0005-humans-approve-never-author.md) | Humans approve and merge; they never author | accepted / proposed for organisations |
| [0006](0006-pr-gated-output-human-release.md) | PR-gated output; production release stays human; delegation is earned | accepted / proposed |
| [0007](0007-specs-are-derived-memory-promotes-by-pr.md) | Specs are derived; memory promotes by PR | accepted |
| [0008](0008-browser-qa-drives-a-cli-not-a-protocol-server.md) | The browser QA pass drives a CLI, not a protocol server or a browser extension | accepted |
| [0009](0009-the-spec-is-a-gate-input.md) | The spec is a gate input; scope drift is a finding with its own disposition | proposed |
| [0010](0010-program-design-before-the-plan.md) | Program design before the plan on sized tickets; red-first becomes a gate (fail-on-base) | proposed |
| [0011](0011-agent-managed-context-repos-auto-merge.md) | Agent-managed context repos auto-merge; agents refresh shared context continuously | accepted; decision 1 superseded for graduation PRs by 0018 |
| [0012](0012-money-paths-are-mapped-and-agree.md) | Money paths are mapped end to end, and every exit agrees | proposed |
| [0013](0013-merge-serialization-substrate-for-delegated-merge.md) | Merge serialization is the substrate for delegated merge | proposed |
| [0014](0014-agents-merge-on-green-in-the-operators-own-repositories.md) | Agents merge on green in the operator's own repositories | withdrawn 2026-10-01: an operator-local practice, not part of the reference design |
| [0015](0015-every-agent-station-runs-the-top-tier.md) | Every agent station runs the top tier | accepted (reference implementation) |
| [0016](0016-the-reviewer-gets-a-computed-impact-set.md) | The reviewer gets a computed impact set, and every module in it gets a verdict | proposed |
| [0017](0017-mechanical-changes-ship-as-a-recipe.md) | Mechanical changes ship as a recipe: the recipe is reviewed, the diff is checked to be its output | proposed |
| [0018](0018-graduation-into-a-context-repo-is-pr-only-by-default.md) | Graduation into a context repo is PR-only by default; a repo opts into auto-merge | accepted |
| [0019](0019-the-repo-contract-is-agents-md-behind-a-claude-md-stub.md) | The repo contract is AGENTS.md, behind a CLAUDE.md stub | accepted |
