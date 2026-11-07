---
name: factory-reviewer-setup
description: Configure software-factory Consort reviewers during an agent-led factory deploy. Offer the reference Vertex route, an existing local Pi provider and model, or the Codex-only route when no second vendor is reachable. Use when setting up workstation reviewers, routing CONSORT_REVIEWERS, or choosing GCP Vertex versus local Pi. Do not use for ordinary product code review.
---

# Factory reviewer setup

Configure the factory verify-gate reviewers. Do not replace the gate. Offer a real choice between reference Vertex, an existing local Pi install, and the Codex-only route. Do not assume Vertex, a provider id, a standard Pi profile, or that a local CLI is offline.

A local Pi process still calls a remote model and can bill. Say that before any paid probe.

## Procedure

1. **Discover the caller and Consort root.** Record the factory clone, the Consort plugin path, and the Consort checkout. Record which path the deploy will invoke. Pass that path to `bash deploy/bin/check-workstation.sh --consort-root <path>`. Do not auto-run an unreviewed tree.

2. **Discover Pi without starting a session.** Run `type -a pi`. Record the executable the calling runtime will see. A terminal PATH is not proof of a plugin PATH. Read that Pi version's help before using metadata commands. Do not guess `pi models`. Inspect whether `pi --list-models` and `pi auth check --provider <id> --no-refresh` exist on this version. Never pass `--credentials`.

3. **Discover ids, not labels.** Match exact provider and model columns. A display name is not an id. Record `PI_CODING_AGENT_DIR` only if the caller already uses it. Do not print secrets or copy an auth tree.

4. **Get one grouped decision.** Present discovered options.

   - Reference Vertex. Billing project plus ADC or a scoped credentials file.
   - Existing local Pi. Exact executable, profile directory if used, `pi:<provider-id>:<model-id>`.
   - Codex-only. When the operator has no access on a Vertex billing project and no non-OpenAI Pi provider. One vendor, one reading; it goes into the team's ADR 0001 as a named shortcut.
   - Which other reviewer remains. Codex plus Pi on OpenAI is not two vendors.
   - Permission for a small paid probe and a non-private synthetic diff.

   If the operator already chose, confirm the discovered mapping. Do not ask again.

5. **Configure user-scope env only.** Back up privately the files you will change. Merge owned keys only. Preserve hooks, plugins, and unrelated env.

   Vertex:

   ```text
   CONSORT_REVIEWERS=codex,pi:google-vertex
   CONSORT_GCP_PROJECT=<billing-project>
   CONSORT_GEMINI_LOCATION=global
   ```

   Local Pi:

   ```text
   CONSORT_REVIEWERS=codex,pi:<provider-id>:<model-id>
   ```

   Codex-only:

   ```text
   CONSORT_REVIEWERS=codex
   ```

   Do not write these keys into tracked project settings. Do not invent `CONSORT_PI_BIN`. Consort runs `pi` on PATH. Prefer the existing compatible executable. If two installs require selection, describe a private scoped `pi` shim that execs the absolute binary and forwards `"$@"`. Verify the same PATH and profile in the real caller. Do not claim a panel-only launcher configures plugin calls.

6. **Keep isolation.** Consort read-only Pi passes `--no-extensions --no-skills --no-prompt-templates --no-themes --no-context-files --no-approve` and loads `pi-fence.mjs` with `-e`. If the provider disappears under that isolation, stop. Do not remove those flags. Inspect an extension before proposing to load that one file next to the fence. That loading is a separate reviewed change unless the installed caller already does it safely. The fence is a tool hook, not an OS sandbox.

7. **Prove the route in the same environment the panel will inherit.** Settings edits are not completion. Ask before any paid call.

   - Run the workstation checker in that process. A Codex pass is not a two-leg gate; it counts only when the operator chose the Codex-only route and the checker prints `OPTIONAL reviewer panel`.
   - Probe each selected transport with the matching Consort command. `consort_impl_probe` uses the Codex CLI even when Consort selected the plugin companion. That probe is not proof of the plugin route. Use the panel, or an inspected command for the selected transport.
   - Run the panel on a tiny non-private synthetic bug diff. Require every configured leg, Consort attestation, and findings files.
   - Prove an inside read works, an outside harmless canary is refused, and read-only write/bash tools are refused. Do not use a credential file as the canary.
   - Force a syntactically valid leg to fail at runtime and require panel exit 3. Exit 2 for malformed config is not that test. Restore the good route and rerun it.

8. **Handoff.** Return the chosen route, executable, profile, provider/model ids, Consort root, files changed, private backup locations, checker result, probe/panel evidence, isolation result, fail-closed exit, rollback steps, and what was not tested. Do not call the factory ready while a configured reviewer is unreachable, a Codex-only route is unrecorded in ADR 0001, isolation was disabled, served models mismatch, or same-vendor legs are presented as cross-vendor.

## Refusals

- Do not install a replacement harness.
- Do not copy an auth tree or print secrets into the repo.
- Do not put reviewer env, paths, or profile selection in tracked project settings.
- Do not disable Consort isolation flags.
- Do not treat checker exit 0 as proof that a model answered.
