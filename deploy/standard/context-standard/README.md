# context-standard

One context standard for product repositories, built on a placement rule:
knowledge lives at the layer where it is true. Repo-true context — the rule
file, current-state docs, decision records — is colocated with the code.
Team knowledge and team memory live once, in the team's `*-team-context`
repo, and every code repo binds to them (sentinel import + committed
`.memspec.yaml` pointer) instead of carrying copies. The org contract is a
managed vendored file. Managed pieces update centrally without touching what
teams own. Adoption starts at L0 (~15 minutes) and tightens as the team
matures.

The normative spec is [`STANDARD.md`](STANDARD.md). The day-2 mechanics — content
classes, ownership, push/pull, fleet audit, the starter-kit fork story — are
[`governance/distribution.md`](governance/distribution.md). This file is just the
front door; if it disagrees with either of those, they win.

## Adopt (day 1, once per repo)

```bash
git clone <this-repo> /tmp/context-standard
/tmp/context-standard/adopt.sh /path/to/your-repo
# in your repo afterwards:
#   1. fill the {{PLACEHOLDERS}} in AGENTS.md and docs/   (seeded files are yours)
#   2. wire the team layer:  ./adopt.sh --set-team <org>/<team>-team-context .
#   3. gh repo edit --add-topic context-standard              ← how updates find you
#   4. commit everything, including .context-standard.lock
```

`adopt.sh` is idempotent; `--dry-run` shows what it would do, `--check` runs the same
verification CI does.

## Day 2: how updates reach you

You don't run anything. On a release, a bot runs `adopt.sh --update` against every
repo carrying the `context-standard` topic and opens a PR where the tree changed:

```
PR: chore: context-standard v0.3                        [MAJOR]

  docs/standard/agents-core.md | 4 ++++    ← the actual change
  .context-standard.lock           | 4 +-      ← version + sha bump
  AGENTS.md                    | 2 +-      ← header version line only
```

Your team-owned files are never in the diff — teams and the center don't co-own any
file. MAJOR PRs must be merged (L2 repos go red after a grace window); MINOR PRs are
advisory and can be closed; check-logic fixes ship via the reusable workflow with no
PR at all. Editing a managed file fails CI with the two honest paths: propose the
change centrally, or fork consciously with an ADR. Full matrix and rationale:
[`governance/distribution.md`](governance/distribution.md) §8.

## Repo map

| Path | What |
|---|---|
| [`STANDARD.md`](STANDARD.md) | The normative spec — layers, layout, conformance levels, AGENTS.md contract and CLAUDE.md stub |
| [`template/`](template/) | The payload a repo receives; [`template/MANIFEST`](template/MANIFEST) declares each file's class |
| [`adopt.sh`](adopt.sh) | Seed / `--update` / `--check` / `--force` |
| [`governance/distribution.md`](governance/distribution.md) | Day-2 design: managed/seeded/referenced, lock, push/pull, fleet report, kit fork story |
| [`governance/VERSIONING.md`](governance/VERSIONING.md) | What MAJOR/MINOR mean |
| `governance/<org>-profile.md` | the adopting organisation's overlay (no-touch zones, starter-kit lineage, conformance targets); write your own, none is vendored |
| [`.github/workflows/`](.github/workflows/) | `docs-lint-reusable` (checks), `propagate` (update PRs), `fleet-report` (weekly audit) |

## Not yet wired

`propagate` and `fleet-report` skip gracefully until a GitHub App credential exists —
see [`governance/distribution.md`](governance/distribution.md) §11 for the three open
org calls (bot identity, workflow home, enforcement SLA).

---

Status: **v0.3 draft, for review.** Open questions are tagged `TODO(review)` — grep
for it.
