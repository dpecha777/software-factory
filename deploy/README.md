# Deploying the factory

Everything an engineer needs to stand the loop up for themselves or for a PM, in the shape it
runs on the reference implementation (kvart) today: two runbooks, two checkers, the plugins the
loop installs, the group standard it adopts, and the wiring files it copies into a code repo.

The design documents say why. This directory says how, with a command and a check per step, so
that the setup is reproducible by a second person on a second machine rather than one operator's
habits. The two flightlist rules apply throughout: no step without a check, and a skipped step is
a named shortcut in the team's ADR 0001 the day it is skipped.

## Which document

| You are | Read | Then run |
|---|---|---|
| An engineer setting up your own Mac | [01-workstation-macos.md](01-workstation-macos.md) | `bin/check-workstation.sh` |
| An engineer setting up a PM's Mac | [01-workstation-macos.md](01-workstation-macos.md), the PM profile section | `bin/check-workstation.sh --pm` |
| An agent (or an engineer driving one) wiring a code repository, its team-context repo, the ledger and the PM workspace | [02-scaffold-a-project.md](02-scaffold-a-project.md) | `bin/check-project.sh` in the code repo |
| An agent choosing the Vertex, existing local Pi or Codex-only reviewer route during factory deploy | [factory-reviewer-setup](../templates/skills/factory-reviewer-setup/SKILL.md) | then `bin/check-workstation.sh` in the same process environment the panel will inherit |

The scaffold runbook is written to be handed to an agent as its brief: it names the inputs to
collect from the human first, then the legs in order, each with the command, the check and the
evidence to record. The flightlist ([docs/18](../docs/18-flightlist.md)) is the tick sheet it
fills; the onboarding runbook ([docs/17](../docs/17-onboarding.md)) is the Day 1 knowledge-plane
work it points to rather than repeats.

## What is in here

| Path | What | Source and pin |
|---|---|---|
| `01-workstation-macos.md` | tools, plugins, credentials and settings for one macOS workstation; engineer and PM profiles | written from the operator's machine, 2026-09-16 |
| `02-scaffold-a-project.md` | the agent runbook: team-context repo, context standard, memory binding, sensors, verify gate, CI, ruleset, ledger, PM workspace, test-the-test | written from kvart's wiring at `e6b90e18`, 2026-09-16 |
| `bin/check-workstation.sh` | one line per requirement, exit 1 on a missing required item; `--pm` for the PM profile; route-aware reviewer checks from process env | original checker tested on the operator's Mac; route-aware changes tested with Linux CLI fixtures in `bin/test_check_workstation.py`; macOS rerun pending |
| `bin/check-project.sh` | one line per scaffold artifact in a code repo, exit 1 on a missing required one | kvart passes (0 MISSING, 2026-11-07); accepts the brownfield layouts the runbook lists (hooks dir, memspec-bound team store, classic protection, local or poller ledger); fixtures in `bin/test_check_project.sh` (33 cases, red-proofed against the previous checker) |
| `marketplace/` | a Claude Code plugin marketplace named `software-factory`: the eight plugins the loop uses, seven from the group's catalog and one written here | `pm-workspace` 1.9.1 from the group catalog's `main` @ `ff7c175`; the other six from its `main` @ `f2bc651`; `rule-packs` is this repository's own generic example, not vendored |
| `standard/` | the group standard: `context-standard/` v0.5 (AGENTS.md contract + CLAUDE.md stub; ahead of the group repo, which is still v0.4) with `adopt.sh`, `agents-core.md` (the operating contract every session loads), the team-context and instructions-file templates | group standards repo @ `7cb157f` |
| `templates/` | the wiring files kvart runs: tracked agent settings with the sensor hooks, MCP servers, sensor rule files, git hooks, the ledger sync script with its tests, the gate and ledger workflows, the ruleset body, the memory binding, the Jira workflow payload | kvart @ `e6b90e18`; see [templates/README.md](templates/README.md) for per-file notes |

Third-party tools are not vendored; the workstation guide installs them from their own releases
at the versions below. Vendoring them would turn a version pin into a fork.

| Tool | Role | Version on the reference machine | Source |
|---|---|---|---|
| Claude Code | agent runtime | 2.1.267 | Homebrew cask `claude-code` |
| Codex CLI | second vendor, reviewer and implementer | 0.154.0 | Homebrew cask `codex` |
| Codex plugin for Claude Code | the companion runtime consort prefers | 1.0.6 | marketplace `openai/codex-plugin-cc` |
| Gemini CLI | third vendor, cli transport | 0.58.0 | npm `@google/gemini-cli` |
| Pi | multi-provider headless agent; Vertex Gemini or another explicit provider/model for the second panel leg | 0.84.1 | npm `@earendil-works/pi-coding-agent` |
| consort | the cross-vendor verify gate, panel, scan, security side-pass | 0.9.1 (`5f68ef6`) | `siimvene/consort`, plugin plus a checkout |
| memspec | memory engine and MCP server | 0.12.3 | npm `memspec` |
| cleat | quality ratchets (sensor 3) | fork `siimvene/cleat` @ `c2947a5` | vendored into each project by `attach.py` |
| enola | architecture diff (sensor 4) | 0.4.19, the same pin in `templates/github/workflows/gates.yml` | `enola-labs/enola` releases, sha256-verified |
| ripwire | orientation map (sensor 1) | 0.4.0 | `redhat-et/ripwire` installer |
| chisle | YAGNI ladder (sensor 2) | tag v3.0.0, commit `a5486fa112` | marketplace `JayPokale/Chisle` pinned to the tag; installed at user scope and switched off there, switched on per project |
| claude-hud | status line | 0.6.0 | marketplace `jarrodwatts/claude-hud` |
| lizard | complexity analyzer for cleat | 1.23.0 | `uv tool install lizard==1.23.0` |
| Trivy | secrets, misconfig, dependency scan | 0.74.0 | Homebrew `trivy` |
| SonarQube + scanner | optional static-analysis leg | community image; scanner 8.1 | Docker + Homebrew `sonar-scanner` |
| Playwright CLI | headless browser for the QA pass | 0.1.19 | Homebrew `playwright-cli` |

## Anonymisation note

The prose in this directory follows [WRITING.md](../WRITING.md): the group is "the group", no
private hosts, no person names beyond the operator. The vendored trees under `marketplace/` and
`standard/` are copied at the pinned commits and kept company-agnostic in two steps. First, a
mechanical scrub: the organisation's name, GitHub organisation (`<org>`), repository and plugin
names (`group-*`), wiki identifiers, domains, and every person's name and address (replaced by a
role or `dev@example.com`). Second, content that only describes one organisation's estate is
left out: its rule packs (the `rule-packs` plugin ships one generic example instead), its wiki
pointers and domain glossary, and its adoption profile. To update a tree, re-vendor from the
source at a new pin, re-apply both steps, and change the pin in the table above, in the same
commit.

## Findings against the vendored trees, for upstreaming

The gate on this directory (two-vendor panel plus a blind security pass, 2026-09-16) read the
vendored copies too. Defects in them are not fixed here, because a vendored tree is re-vendored,
never edited; they are listed so the next person does not rediscover them, with the workaround
the runbooks carry.

| Where | Finding | Disposition |
|---|---|---|
| `standard/context-standard/adopt.sh --check` | passes with the team import line missing or pointing elsewhere | `bin/check-project.sh` greps the wired `org/repo` and `memspec stores` proves the binding; upstream: check the import |
| `standard/context-standard/adopt.sh` | a token passed to curl on the command line is visible in the process list | upstream: `gh api` or a header file |
| `standard/context-standard/.github/workflows/{propagate,fleet-report}.yml` | `create-github-app-token@v1` and `checkout@v4` by movable tag while holding the App private key | upstream: pin both to full commit SHAs, as every workflow in `templates/` does |
| `marketplace/plugins/secret-guard/hooks/` | intercepts Read and Bash only (a Grep call reads the file); the Bash path passes when an allowlisted template name appears in the same command; fails open without `jq` | described as a deterrent, not a boundary, in both guides and the marketplace index; upstream: add Grep and per-path checks |
| `marketplace/plugins/pm-workspace/skills/pm-workspace-setup` | repository discovery needs the hosted GitHub connector and leaves `POINTERS.md` blank otherwise | the engineer fills `POINTERS.md` from the local clones (runbook M0); upstream: discover adjacent clones |
| `marketplace/plugins/team-memory/skills/promote/SKILL.md` | `grep` invocations without `--`, a pattern starting with `-` is parsed as an option | cosmetic; upstream |

## Keeping the vendored copies honest

```
# marketplace: from the group's plugin catalog checkout
git -C <catalog> archive <ref> plugins/<name> | tar -x -C deploy/marketplace
# standard: from the group's standards checkout
git -C <standards> archive HEAD context-standard agents-core.md templates/team-context templates/claude-md references README.md | tar -x -C deploy/standard
# templates: hand-picked from the reference implementation, then the placeholders re-applied
```

After re-vendoring, `python3 -c 'import json;json.load(open("deploy/marketplace/.claude-plugin/marketplace.json"))'`
still parses, every `plugins/*/.claude-plugin/plugin.json` version matches the index, and the
pin table above names the new commit.
