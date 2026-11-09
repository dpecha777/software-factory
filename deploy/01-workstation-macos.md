# Workstation setup, macOS

One machine, set up so that a session started in any wired repository has the whole line
available. That includes the agent runtime with its memory, the verify-gate reviewers, the four
sensors, the scanners, the plugins, and the credentials each of them needs. Apple silicon
assumed. Intel differs only in the enola archive name.

Two profiles. The **engineer** profile is everything below. The **PM** profile is section 1,
section 2, the PM lines of section 6 and section 8, and nothing else. A PM's agent reads specs
and drafts tickets. It never runs a gate. The checker knows both.
`bin/check-workstation.sh` and `bin/check-workstation.sh --pm`. Run it first on a machine you
think is done. The lines it prints are the list of what is not.

Pick the reviewer route in section 3 before you install Google tooling. The reference route is
Codex plus Gemini through Pi on Vertex. An existing local Pi provider and model is a first-class
alternative. It does not need gcloud. A team with Codex but no reachable second vendor runs the
Codex-only route and records it as a named shortcut. Order matters in two other places only. Install the memory
engine before the agent hooks that call it, and install Codex before the consort plugin that
wraps it. Everything else can be installed in any order.

`$CFG` below is the Claude Code config directory: `$CLAUDE_CONFIG_DIR` when it is set, `~/.claude`
otherwise. `claude` commands follow it on their own, and so does `memspec init` from 0.12.3. Set
it as an absolute path: Claude Code does not expand `~` in it, and memspec refuses a relative or
`~` value. Consort's Codex companion lookup follows it from 0.13.1; the pin in section 3 is older
(see the note there). On a machine that runs Claude Code from another directory, run the checker
with the same `CLAUDE_CONFIG_DIR` the sessions use; it reports which directory it read.

```
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
```

## 1. Base toolchain

```
xcode-select --install                     # once; git and the compilers
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git gh jq uv node pnpm tmux shellcheck actionlint ast-grep trivy sonar-scanner playwright-cli cmake
brew install --cask claude-code codex orbstack
```

If section 3 uses the Vertex route, also install Google Cloud:

```
brew install --cask gcloud-cli
```

`uv` runs every Python tool in its own environment (cleat's helper, the ledger
script). `node` carries memspec, the Gemini CLI and Pi. `pnpm` is the frontend package manager
the reference project uses. `ast-grep` feeds two optional cleat gates. `trivy` is the scanner
tier. `sonar-scanner` and `playwright-cli` serve the static-analysis and browser legs.
`orbstack` is the Docker daemon (Docker Desktop works identically). Python itself comes with uv.
Do not manage a system Python.

Sign in to GitHub now, because later steps assume it. Sign in to Google only for the Vertex route:

```
gh auth login                              # GitHub, the account that will own PRs and merges
gcloud auth login                          # Vertex route only (section 3)
```

## 2. Agent runtime and memory

```
claude                                     # first run logs you in; then exit
npm install -g memspec@0.12.3 --min-release-age=0
memspec init ~/.memspec --no-interactive --skip-import --skip-patch   # the store; hooks into $CFG
# init also writes a project-scope memspec entry into ~/.memspec/.mcp.json; the user-scope one
# below replaces it. Drop only that entry, and the file only when nothing else is left in it:
M=~/.memspec/.mcp.json; if jq -e '.mcpServers.memspec' "$M" >/dev/null 2>&1; then jq 'del(.mcpServers.memspec)' "$M" > "$M.new" && mv "$M.new" "$M"; jq -e '.mcpServers | length > 0' "$M" >/dev/null || rm "$M"; fi
claude mcp add --scope user memspec -e MEMSPEC_ROOT="$HOME/.memspec" -- memspec-mcp
```

`memspec init ~/.memspec` makes `~/.memspec` the store: a path that ends in `.memspec` is the
store itself, so nothing lands in the home directory. The `jq` line removes the `memspec` entry
init writes to `~/.memspec/.mcp.json`, keeps any other servers in that file, deletes it only when
nothing else is left, and does nothing when it is absent. Left in place, it is a project-scope
server, pending approval, in every session started inside the store directory.

`--min-release-age=0` drops the npm release-age gate for this install. A workstation that
carries `min-release-age=30` in `~/.npmrc` (the operator's machines do; a fresh Mac does not)
refuses a version published less than 30 days ago, and a pinned memspec release is exactly that
for its first month (0.12.3 shipped 2026-10-18). The flag applies to the whole install, not only
to memspec: memspec's dependencies are declared as ranges and resolve to their newest versions,
so packages younger than 30 days come in with it. On the reference machine 0.12.3 brought four
`[measured 2026-10-18]`. That is accepted here; the trust decision is the memspec pin. On a
machine without the setting the flag is a no-op.

`memspec init` writes `memspec-session-start.js` and `memspec-consolidate.js` (and the
`memspec-claims-check.js` helper they load) into `$CFG/hooks/` and registers them in
`$CFG/settings.json`; the MCP registration gives every session the `memspec_*` tools. Verify with
`claude mcp get memspec` (`Scope: User config`, connected) and `memspec stores` from any directory
(the global store, read-write).

Run the init line once per `CLAUDE_CONFIG_DIR` the machine uses, with that directory set, and the
`jq` line after each run. A second run leaves the store and an existing registration as they are.
On a machine set up with memspec before 0.12.3, which always wrote `~/.claude`, the same line
repairs a second directory: an entry there that is exactly `node <the ~/.claude copy>` is
repointed to the directory's own copy rather than duplicated, and any other entry (a wrapper, a
chained command) is left alone. The checker's hook lines say `OK` when the file is in
`$CFG/hooks` and `$CFG/settings.json` runs it; with `CLAUDE_CONFIG_DIR` set it also warns about a
memspec older than 0.12.3 `[measured 2026-10-18]`.

The store is personal scratch. Durable team knowledge lives in the team-context repo and
reaches it through promote PRs; the scaffold runbook binds each code repo to that store
read-only. Nothing in this section is per project.

## 3. Second and third vendor: the verify gate's reviewers

The reference gate is a two-leg panel. Both configured legs are required. The panel hard-fails
if either is unreachable ([docs/06](../docs/06-verify-gate.md)). Leg one is Codex. Leg two is
either Gemini through Pi on Vertex, or an existing local Pi provider and model. Choose one route
before you install Google tooling.

**Codex-only route.** When no second vendor is reachable from this machine (no Vertex access on
the billing project, no other non-OpenAI provider in Pi), run the panel with Codex alone:
`CONSORT_REVIEWERS=codex`. Codex is still a different vendor from the Claude author, so the
cross-vendor axis holds, and the panel still hard-fails when Codex is down. What it loses is the
second reading: on the 2026-09-07 benchmark each leg caught defects the other missed. The person
setting up the machine chooses it, names the shortcut in the team's ADR 0001, and switches to a
two-leg route when access lands (one settings key). It is a starting route, never a fallback: a
configured leg that fails is fixed or the gate stops. Skip the Pi, gcloud and Gemini installs
below. An agent-led deploy should load
[factory-reviewer-setup](../templates/skills/factory-reviewer-setup/SKILL.md) and stop for that
choice.

Install missing tools for the chosen panel. Keep an existing compatible Pi installation and
its credentials. Do not run the pinned npm install below over that installation. Check the
installed Consort backend's minimum Pi version first.

```
codex login                                # ChatGPT subscription or API key; writes ~/.codex/auth.json
codex exec 'Reply with exactly: CODEX_ALIVE' < /dev/null     # reachability, not budget
npm install -g @earendil-works/pi-coding-agent@0.84.1
git clone https://github.com/siimvene/consort ~/git/consort && git -C ~/git/consort checkout 5f68ef6
claude plugin marketplace add openai/codex-plugin-cc && claude plugin install codex@openai-codex
claude plugin marketplace add siimvene/consort   && claude plugin install consort@consort
```

For the reference Pi Vertex leg, configure ADC or a readable credentials file. Install gcloud
if you use its ADC login flow. The Gemini CLI is not required for a Pi leg. Install it only if
you choose Consort's separate native Gemini transport.

```
npm install -g @google/gemini-cli@0.58.0
gcloud auth application-default login      # ADC for the Vertex leg; or a service-account key file
```

If you use an existing local Pi provider, skip gcloud. Discover the exact provider and model ids
from that Pi install (`pi --list-models` only after you have checked that this Pi version
supports it). Write `pi:<provider-id>:<model-id>`. Do not invent `CONSORT_PI_BIN`. Consort runs
the `pi` command on PATH. A local Pi CLI still calls a remote model and can bill. Say so before
any paid probe.

Why both a plugin and a checkout of consort. The plugin provides the `/consort:*` commands and
the companion-runtime integration. The panel script and the merge tool are run from the
checkout (`~/git/consort/scripts/consort-panel.sh`, `merge-findings.mjs`), which is how the
reference machine runs the gate. `codex exec` always reads stdin. Redirect it from `/dev/null`
or it waits forever, which is the 2h08m stall in the trial report.

With `CLAUDE_CONFIG_DIR` set, the Codex plugin installs under `$CFG/plugins/cache`, but Consort
5f68ef6 looks for `codex-companion.mjs` under `~/.claude/plugins/cache` only
(`scripts/codex-backend.sh`). Its plugin transport then finds nothing and the auto mode falls
back to the CLI. Set `CONSORT_CODEX_BACKEND=exec` in the section 7 block so the transport is a
stated choice rather than a silent fallback. Consort 0.13.1 (`c26ffca`) searches
`$CLAUDE_CONFIG_DIR/plugins/cache` first; on a checkout at or after it the setting is not needed.

The panel reads process environment, not Claude settings files. For a Claude session, merge the
keys in section 7 into user-scope `$CFG/settings.json` so the session inherits them. For a
shell panel, export the same keys in that shell. A review of a multi-hundred-line diff that
returns in seconds did not run. The panel's `[label]` stderr lines and its `seconds` are the
evidence that it did.

## 4. Sensors

The four mechanical layers of [docs/05](../docs/05-sensor-stack.md). Binaries per machine, in
the user's local bin; the project-side wiring is the scaffold runbook's job.

```
mkdir -p ~/.local/bin
# sensor 3: cleat is vendored into each project by its attach script; keep the fork checked out
git clone https://github.com/siimvene/cleat ~/git/cleat && git -C ~/git/cleat checkout c2947a5
uv tool install lizard==1.23.0             # the complexity analyzer cleat calls; pin = the baselines' version
# sensor 4: enola, pinned release, checksum-verified (the darwin-arm64 archive on Apple silicon)
V=0.4.19; A=darwin-arm64
curl -fsSLO "https://github.com/enola-labs/enola/releases/download/v$V/enola-$V-$A.tar.gz"
curl -fsSLO "https://github.com/enola-labs/enola/releases/download/v$V/enola-$V-$A.sha256"
shasum -a 256 -c "enola-$V-$A.sha256" && tar -xzf "enola-$V-$A.tar.gz" && install -m 0755 "enola-$V-$A" ~/.local/bin/enola
# sensor 1: ripwire, built from source at the pinned commit the reference binary was built from (0.4.0).
# The repository-root install.sh builds the binary (CMake from section 1, Xcode's clang) and installs it
# with its skills and hooks under the prefix. It edits no agent config unless RIPWIRE_ACTIVATE_CODEX=1.
# Read it before running it: it is a script from a third-party checkout, not a signed release.
git clone https://github.com/redhat-et/ripwire /tmp/ripwire && git -C /tmp/ripwire checkout e663ca8f8
less /tmp/ripwire/install.sh && RIPWIRE_INSTALL_PREFIX="$HOME/.local" bash /tmp/ripwire/install.sh
ripwire --version                          # expect 0.4.0 ... built_from=e663ca8f8
# sensor 2: chisle is a plugin, installed at user scope in the plugins section below
```

Make sure `~/.local/bin` is on PATH in `~/.zshrc`. The reference machine keeps lizard in its own
virtualenv with a symlink; `uv tool install` is the same thing with less ceremony and is what
CI does. Why enola is pinned by checksum and not `brew`: the CI job installs the same release
the same way, so the local check and the required check agree.

`skills/install.sh` is not the installer. At `e663ca8f8` it only links ripwire's agent skills
into `~/.claude/skills` and puts no `ripwire` on PATH, so the checker keeps reporting it missing.
The root script built and installed 0.4.0 on a fresh workstation `[measured 2026-11-09]`.
`RIPWIRE_NO_ACTIVATE` belongs to the release installer (`scripts/install.sh`, which fetches the
latest release unless `RIPWIRE_VERSION` names a tag); neither script used here reads it. The prefix is `~/.local` because the root script otherwise picks
Homebrew's when `brew` is on PATH, and the sensors live in the user's local bin.

`enola install` and `ripwire wrap claude` write instructions into agent files. Run them in the
project, from the scaffold runbook, not globally: the reference implementation tracks the
resulting rule files per repo and the check in [docs/05](../docs/05-sensor-stack.md) says why
`enola install --targets=agents` pushed a shared file over its size ceiling.

## 5. Scanners and the optional static-analysis leg

Trivy came with section 1 and needs no configuration; the scan script in consort finds it. The
static-analysis leg is optional and reported loudly when absent: every SKIPPED line the scanner
tier prints goes into the gate report unchanged. To have it:

```
docker run -d --name sonarqube -p 9000:9000 --restart unless-stopped sonarqube:community
# browse http://localhost:9000, set the admin password, create a user token, then:
mkdir -p ~/.config/sonar && printf 'export SONAR_HOST_URL=http://localhost:9000\nexport SONAR_TOKEN=<token>\n' > ~/.config/sonar/env
chmod 600 ~/.config/sonar/env
grep -q 'config/sonar/env' ~/.zshenv || printf '[ -r "$HOME/.config/sonar/env" ] && . "$HOME/.config/sonar/env"\n' >> ~/.zshenv
```

`~/.zshenv` rather than `~/.zshrc` because hooks and non-interactive shells read the former. The
scan reads `sonar-project.properties` from the project; without that file the leg is SKIPPED by
design, and a worktree without the file degrades the scan to dependency scanning only, which the
report must say.

## 6. Plugins and the marketplace

User scope, once per machine:

```
claude plugin marketplace add jarrodwatts/claude-hud && claude plugin install claude-hud@claude-hud
claude plugin marketplace add "$HOME/git/software-factory/deploy/marketplace"      # this repository, cloned
```

The `software-factory` marketplace is a directory source, so it points at your clone of this
repository; `git pull` is the update. It holds the eight plugins the loop uses from the group's
catalog at pinned versions ([README.md](README.md) has the pins). Install per role:

| Role | Install | Why |
|---|---|---|
| PM | `claude plugin install pm-workspace@software-factory` | the workspace setup, ingest, ticket, readiness, improver, splitter, apply and graduate skills (pm-workspace 1.9.1: setup offers the product context repositories; apply since 1.8.0) |
| PM | `claude plugin install secret-guard@software-factory` | a pre-tool hook that refuses reads of credential files; a deterrent, not a boundary (it fails open without `jq`, and a renamed file passes) |
| Engineer | `secret-guard`, `spec-repos`, `team-memory`, `rule-packs`, `dev-hygiene` from the same marketplace | the spec chain, the promote PR, the rule packs the reviewer loads, the pre-completion pass |
| Engineer, optional | `solo-review`, `ux-qa` | the single-model fallback (never the gate) and the browser QA prompt |

`chisle` (sensor 2) is installed at user scope, switched off at user scope, and switched on per
project by the scaffold's tracked settings. The install is user scope because a project-scope
install is keyed to one exact directory, so every new worktree runs without the plugin; on the
reference implementation it stopped loading for a week that way
([evidence](../evidence/kvart-sensor-trial-2026-09-29.md)). The switch stays per project because
its output hook sees every tool result, and a repository that did not opt in should not run it.

1. Pin the marketplace: an `extraKnownMarketplaces` entry `chisle` in `$CFG/settings.json`
   with source `{"source": "github", "repo": "JayPokale/Chisle", "ref": "v3.0.0"}`.
2. `claude plugin install chisle@chisle --scope user`.
3. Set `"chisle@chisle": false` under `enabledPlugins` in `$CFG/settings.json`. The install
   writes `true`, which would switch it on in every repository.
4. Check the installed commit against the literal pin, not against the tag (a tag can move and
   the install would follow it): `gitCommitSha` in `$CFG/plugins/installed_plugins.json`
   must be `a5486fa112c961f9b25349a29ede38cc9f2a1a5c`. `check-workstation.sh` does this.

Repeat in every `CLAUDE_CONFIG_DIR` the machine uses.

The `claude plugin marketplace add` commands above track each source's default branch, and a
plugin runs code. Where the source has tags, pin it the way the scaffold pins chisle: an
`extraKnownMarketplaces` entry in `$CFG/settings.json` with a `ref` (consort tags its
releases; check the other two before pinning). An unpinned marketplace is a named shortcut.

Known trap: two config directories. A canvas or terminal-multiplexer runtime may start Claude
Code with its own `CLAUDE_CONFIG_DIR`; a marketplace, plugin or MCP server registered in one
directory is absent in the other, silently. Register in both, or run the checker under each.

## 7. Settings that every session inherits

Merge the block for your chosen route into user-scope `$CFG/settings.json` (the memspec
hooks are already there after section 2). Values in angle brackets are yours. Nothing here is a
secret. Do not put executable paths, `PI_CODING_AGENT_DIR`, credentials, or reviewer keys into
tracked project `.claude/settings.json`.

A direct shell run of `consort-panel.sh` does not read this file. Export the same keys in the
shell that will invoke the panel, or run the panel from a Claude session that inherited them.
The workstation checker also reads process environment only. Settings that are not in the
process are reported as inactive.

Reference Vertex route:

```json
{
  "env": {
    "CONSORT_REVIEWERS": "codex,pi:google-vertex",
    "CONSORT_GCP_PROJECT": "<gcp project the Vertex calls bill to>",
    "CONSORT_GEMINI_LOCATION": "global",
    "CONSORT_GCP_CREDENTIALS": "<path to a service-account key, only if ADC is not used>",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5"
  },
  "modelOverrides": { "claude-opus-5": "claude-opus-5-5" },
  "statusLine": { "type": "command", "command": "<what claude-hud:setup wrote>" }
}
```

Existing local Pi route. Provider and model are discovered ids, not display names. Paths and
auth stay in the user environment:

```json
{
  "env": {
    "CONSORT_REVIEWERS": "codex,pi:<provider-id>:<model-id>",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5"
  },
  "modelOverrides": { "claude-opus-5": "claude-opus-5-5" },
  "statusLine": { "type": "command", "command": "<what claude-hud:setup wrote>" }
}
```

Codex-only route (no Pi, no Google keys):

```json
{
  "env": {
    "CONSORT_REVIEWERS": "codex",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5"
  },
  "modelOverrides": { "claude-opus-5": "claude-opus-5-5" },
  "statusLine": { "type": "command", "command": "<what claude-hud:setup wrote>" }
}
```

With `CLAUDE_CONFIG_DIR` set, add `"CONSORT_CODEX_BACKEND": "exec"` to any of these blocks (section 3
says why).

`CONSORT_REVIEWERS` fixes the panel instead of leaving it to whichever backend is reachable; the
workstation checker prints `OPTIONAL reviewer panel` for the Codex-only route.
The model pin is the routing decision in
[adr/0015](../adr/0015-every-agent-station-runs-the-top-tier.md): every station runs the top
tier, and both knobs map the bare alias to the pinned release so an earlier one is never served.
Set both in every Claude Code config directory on the machine; a directory without them is the
leak [docs/13](../docs/13-failure-catalogue.md) records. The
status line shows the served model, context and cost. Run `/claude-hud:setup` once and let it
write the status line entry. The reference machine also sets
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. It is not required by anything in this directory.

## 8. Credentials and identities

None of these go into a repo, a settings file or a memory record.

| What | Where it lives | Set with |
|---|---|---|
| GitHub, your own account | `gh` keyring | `gh auth login` (section 1) |
| Codex | `~/.codex/auth.json` | `codex login` |
| Google ADC, or a key file (Vertex route) | `~/.config/gcloud/` | `gcloud auth application-default login`, or `CONSORT_GCP_CREDENTIALS` |
| Jira API token (engineer and PM) | login keychain, service `factory-jira-api-token` | `security add-generic-password -s factory-jira-api-token -a <email> -w '<token>'` |
| Jira site, email, project key, code repo | `~/.config/factory/jira.env` | four lines, see `templates/bin/jira` header |
| Sonar token | `~/.config/sonar/env`, mode 600 | section 5 |
| The bot identity's private key (GitHub App) | `~/.config/github-apps/`, mode 600 | created in the scaffold runbook, leg G6; only the engineer who administers the repo holds it |

The ledger wrapper reads the keychain so the token is never typed into a shell history:

```
install -m 0755 "$HOME/git/software-factory/deploy/templates/bin/jira" ~/.local/bin/jira
jira whoami                                # prints your display name and account id
```

## 9. The PM profile, in one block

A PM's machine gets sections 1 (without the scanners and casks other than `claude-code`), 2, the
PM rows of 6, and the Jira rows of 8. Concretely:

```
brew install git gh jq node && brew install --cask claude-code
claude; gh auth login
npm install -g memspec@0.12.3 --min-release-age=0
memspec init ~/.memspec --no-interactive --skip-import --skip-patch
M=~/.memspec/.mcp.json; if jq -e '.mcpServers.memspec' "$M" >/dev/null 2>&1; then jq 'del(.mcpServers.memspec)' "$M" > "$M.new" && mv "$M.new" "$M"; jq -e '.mcpServers | length > 0' "$M" >/dev/null || rm "$M"; fi   # section 2
claude mcp add --scope user memspec -e MEMSPEC_ROOT="$HOME/.memspec" -- memspec-mcp
claude plugin marketplace add "$HOME/git/software-factory/deploy/marketplace"
claude plugin install pm-workspace@software-factory && claude plugin install secret-guard@software-factory
bash "$HOME/git/software-factory/deploy/bin/check-workstation.sh" --pm
```

The PM never runs git themselves ([docs/14](../docs/14-pm-surface.md) says why); the engineer
who sets the machine up also clones the specs repo and the code repos read-only next to the
workspace and fills `POINTERS.md`, which is leg M0 of the scaffold runbook. Since 2026-09-15 the
PM reads repositories through those local clones, not through a hosted connector.

### 9.1 What the first external PM run met, and the answer to each

Measured on a group PM's machine, 16 to 17 Sep 2026, one small admin feature from intake to a
merge request in about a day `[measured 2026-09-17]`. Three things the profile above did not
cover.

**The PM workstation is CI-first.** It has no compiler or build toolchain for the product's
stack (no JVM for a Kotlin service, for instance), so nothing staged or pushed from it is
verified locally. That is the profile, not a gap: the pipeline verifies, and a merge request
opened from a PM machine says so in its description ("not verified locally; CI is the check").
A team that wants local verification on a PM machine gives it the engineer profile and its
devcontainer, not a partial toolchain.

**SSH key, by hand, two minutes.** `secret-guard` refuses the agent any read under the SSH key
directory, by design, so the agent cannot create or inspect a key for the PM. The PM does it in
the terminal (the `!` prefix runs a line in the agent session; a separate Terminal window works
the same):

```
ssh-keygen -t ed25519 -C "<work email>" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub        # paste into the git host: Settings, SSH keys
ssh -T git@<git host>            # expect a greeting with the account name
```

The private key is never pasted anywhere, never read by the agent, and never lands in the
workspace. Needed only when the PM has been granted an owner-authorised write remote
(pm-workspace conventions, section 13); a read-only PM needs no key.

**Company admin interfaces are blocked for the agent's browser.** UI verification comes from the
PM's own screenshots. Those stay out of the workspace under `SENSITIVITY.md`; the PM describes
what the screenshot shows, the agent does not store it.

**Hosted mirrors lag.** Where the hosted repository is a read-only mirror of a GitLab (or other)
development remote, the engineer setting up the machine clones the development remote, not the
mirror, and records it as the `development remote:` line of the `POINTERS.md` entry. The mirror
was five commits behind on the measured run.

## 10. Check, and what the checker cannot see

```
bash ~/git/software-factory/deploy/bin/check-workstation.sh          # engineer
bash ~/git/software-factory/deploy/bin/check-workstation.sh --pm     # PM
```

Pass `--consort-root` when the caller invokes a Consort tree other than `~/git/consort`. The
checker is route-aware. A Vertex panel still requires a project and a local credential route. A
non-Vertex Pi panel does not require gcloud, ADC, or a GCP project. Mixed panels are checked per
leg. `--pm` skips reviewer parsing even when reviewer env is present or malformed.

It proves local presence and cheap status. It does not send a model request. Exit 0 means the
checked prerequisites passed, not that reviewers authenticated or answered. Treat `OPTIONAL`
lines that say `UNVERIFIED` as limits, not success. Prove these separately, once:

- **Budget, not reachability.** `CODEX_ALIVE` proves the CLI answers. The first real panel run
  on a real diff, with its wall-clock in the report, proves the account can pay for one.
- **The served model is the one you named.** Consort attests this at probe and panel time. The
  checker does not.
- **The Vertex leg bills to the project you named.** The first run of the panel logs to that
  project. Look once.
- **Isolation.** Consort read-only Pi keeps `--no-extensions` and loads `pi-fence.mjs`. That
  fence is a tool hook, not an OS sandbox. Do not disable the isolation flags.
- **The two config directories** (section 6). Run the checker under the second directory if a
  canvas runtime is in use. Run the panel in the same process environment you just checked.

## Known traps, from the reference machine

- `npm install -g memspec@<pin>` fails with `No matching version found` although the version
  is on npm: `~/.npmrc` has `min-release-age=30` and the pin is younger than that. Add
  `--min-release-age=0` to that one install (already in sections 2 and 9); the checker prints
  an OPTIONAL line when the setting is present.
- memspec 0.11.0 refuses `memspec init ~/.memspec` (`too many arguments for 'init'`) and
  installs its hooks into `~/.claude` whatever `CLAUDE_CONFIG_DIR` says, so sessions run from
  another directory never load them `[measured 2026-10-15]`. Both are fixed in 0.12.3, which
  section 2 pins. The reference machine's two canvas config directories had no memspec hooks at
  all until 0.12.3 wired them `[measured 2026-10-18]`.
- Consort before 0.13.1 finds the Codex plugin only under `~/.claude`; section 3 says what to
  set while the pin is older. The checker's hook lines say `not registered in $CFG/settings.json`
  when hooks sit in the wrong directory.
- No `timeout` on macOS without coreutils. A delegation's wall-clock cap is
  `perl -e 'alarm N; exec @ARGV' <cmd...>`; a bare `timeout` exits 127 before the child starts
  and reads as an instant success.
- `codex exec` without `< /dev/null` hangs on stdin.
- macOS `ls` has no `--time-style`; `stat -f` instead.
- The Stop hooks run in every wired repo. A session in a repo with a red ratchet is handed the
  failure once; a gate you cannot fix is not a reason to edit the baseline (the guard refuses it
  anyway).
- The frontend test runner and the PDF library on the reference stack need Homebrew's
  libraries on the loader path (`DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`); the repo's
  hooks set it, a bare shell does not.
