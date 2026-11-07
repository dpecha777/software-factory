# Skills a team copies on day one

Anonymised, generic copies of the skills the reference implementation ran, in the shape a
Claude Code project consumes them: one directory per skill, a `SKILL.md` with frontmatter, and
scripts next to the skill that needs them. Copy a directory into a workspace's or a repository's
`.claude/skills/` and it fires on the conditions its description names.

Names are generic on purpose. Rename freely, but keep the description's firing conditions: the
description is the only text the model reads when deciding whether to invoke a skill, so a
vague one is a skill that never fires or fires always.

| Skill | Produces | Used at | Ported from | Notes |
|---|---|---|---|---|
| [`ticket`](ticket/SKILL.md) | a story or epic draft under the tickets folder with its tracker fields (type, project, epic parent, labels, links) deduced and shown for approval, saved on approval, never pushed to the tracker | SPEC intake | the PM workspace's ticket skill | enforces discovery, features, ticket for epics; relaxed for a single story; tracker configuration read once from the workspace, corrections written back so nothing is asked twice |
| [`readiness-evaluator`](readiness-evaluator/SKILL.md) | a score out of 100 against seven criteria, per-criterion gaps, one highest-impact question; on a bigger ticket one extra question the build's design will need | SPEC readiness | the PM workspace | 85 is Ready; below it hands off to the improver |
| [`task-improver`](task-improver/SKILL.md) | a polished ticket, a drift check, a session log with score progression | SPEC readiness | the PM workspace | one question at a time; the session logs feed the optimizer |
| [`task-splitter`](task-splitter/SKILL.md) | a split proposal with a coverage check; the parent promoted to an epic | SPEC readiness | the PM workspace | for tickets over about two person-days |
| [`graduate`](graduate/SKILL.md) | a rewritten features file plus a handoff package the human submits | SPEC to the team layer | the PM workspace | six checks, all must pass, no partial packages |
| [`retrogenerate-specs`](retrogenerate-specs/SKILL.md) | feature maps, a candidate table, spec pairs (`<slug>.md` + `<slug>.tech-refs.md`) | Day 1, and again when a ticket touches unbuilt surface | the group's spec-repos plugin | owner review between suggest and generate; findings file and check added from the reference run |
| [`update-specs-for-commits`](update-specs-for-commits/SKILL.md) | the sister spec delta for a merged code change | LEARN, and at gate time once the delta is a receipt | the group's spec-repos plugin | the skill the reference implementation lacked in cycle 1, so the delta was typed by hand |
| [`check-specs-references`](check-specs-references/SKILL.md) | a list of repositories cited by the specs that are not checked out | before any spec work | the group's spec-repos plugin | `scripts/check-tech-refs-repos.js` |
| [`check-specs`](check-specs/SKILL.md) | one line per finding: missing pair file, cited path that does not exist, code identifier in a business spec; exit 1 on findings | before the specs PR; in CI of the team repo | new, from the three checks in 17-onboarding §5 | `scripts/check-specs.py`, stdlib only; the reference implementation's copy lived in a scratch directory and was gone by cycle 1 |
| [`mine-decision-records`](mine-decision-records/SKILL.md) | `docs/adr/CANDIDATES.md`, numbered records at repo and team level, a rejected list | Day 1, and when a design document is added | new, from the procedure in 17-onboarding §6 | a record is written only for a decision live in the code |
| [`factory-reviewer-setup`](factory-reviewer-setup/SKILL.md) | a chosen Consort reviewer route (reference Vertex, existing local Pi with explicit provider and model, or Codex-only when no second vendor is reachable), user-scope env only, and a handoff of what was and was not tested | agent-led factory deploy and workstation reviewer routing | shortened from a draft setup skill | not a product-code review skill; copy into a deploy workspace, not into every code repo |

Concept and conventions for the spec skills: [README-specs.md](README-specs.md).

What is deliberately not here: the tracker skill, because its wiring is tracker-specific. Its
write path (a staged ticket into the tracker, and the walk to review when a merge request
opens) ships instead as `apply` in the vendored pm-workspace plugin from 1.8.0,
[deploy/marketplace](../../deploy/marketplace/plugins/pm-workspace/skills/apply/SKILL.md). Also
not here: the daily-ops skills (morning, wrap-up, checkpoint), and the two skills that improve
the skills (degrader, optimizer). All are catalogued with their inputs and outputs in
[docs/14-pm-surface.md](../../docs/14-pm-surface.md) and follow the skeleton in
[pm-skill.md](../pm-skill.md).
