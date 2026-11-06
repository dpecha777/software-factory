# group-standards

Normative home for group development standards and graduated templates. What lives
here is the blessed, org-supported version; consume it from here, not from
experiments.

Development and incubation happen in
[starter-kits](https://github.com/<org>/starter-kits) (templates are
field-tested there before graduating; unvalidated rule drafts sit in its
`rule-candidates/`, no authority). Standards content lands here as it clears
review.

| Content | What it is |
|---|---|
| [`agents-core.md`](agents-core.md) | The org agent contract (v0.3): universal behavioral core for every group agent session, incl. the memory contract. Single managed source; context-standard adopters vendor it from here. |
| [`context-standard/`](context-standard/) | The Repository Context Standard (v0.5): where project knowledge lives and how a repo binds to it — AGENTS.md contract behind a CLAUDE.md stub, team-context layer, memory binding, conformance levels, `adopt.sh`. This is its permanent home. |
| [`rules/`](rules/) | Adopted rule packs (the review rubric + working conventions), one directory per activity. Only `status: adopted` packs ship to agents, via the rule-packs marketplace plugin. Not vendored here: the packs are organisation content; `marketplace/plugins/rule-packs` shows the shape. |
| [`templates/devcontainer-template/`](templates/devcontainer-template/) | The standard agent sandbox: host-enforced egress gateway, scoped credential delivery, team-context mount, memspec wiring, one-word `sandbox` launcher. See its README + WINDOWS.md. |
| [`templates/claude-md/`](templates/claude-md/) | CLAUDE.md rule-file templates (group standard, decided 2026-08-06): per-repo shim skeleton + multi-repo workspace router. |
| [`templates/team-context/`](templates/team-context/) | Team-context repo scaffold: bracketed CLAUDE.md template, filled example, CODEOWNERS, setup README. Pairs with STANDARD.md §8 and the wiki setup guide. |

Repos consuming a template track their source in `.devcontainer/TEMPLATE_VERSION`;
`sandbox sync` pulls updates from this repo. Repos adopting the context standard
track it in `.context-standard.lock`; `adopt.sh --update` resyncs.
