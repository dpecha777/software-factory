#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check-workstation.sh"
UNIX_NAMES = (
    "bash",
    "python3",
    "git",
    "head",
    "tr",
    "ls",
    "wc",
    "grep",
    "cat",
    "sed",
    "uname",
    "basename",
    "dirname",
    "env",
    "true",
    "false",
    "chmod",
    "ln",
    "mkdir",
    "rm",
    "cp",
    "mv",
    "cut",
    "sort",
    "awk",
    "date",
    "id",
    "mktemp",
    "touch",
    "printf",
    "tail",
)
BASE_STUBS = (
    "claude",
    "gh",
    "jq",
    "node",
    "uv",
    "pnpm",
    "memspec",
    "memspec-mcp",
    "enola",
    "ripwire",
    "lizard",
    "trivy",
    "docker",
)
FORBIDDEN_FRAGMENTS = (
    "print-access-token",
    "--list-models",
    "print-api-key",
    "--credentials",
    "generateContent",
    "consort_impl_probe",
    "consort_pi_probe",
)
BAD_SPECS = (
    "codex,bogus",
    "codex,codex",
    "gemini:a:b",
    "pi::m",
    "codex:a:b",
    ", ,",
    "codex:",
    "pi:xai:m:extra",
)
CONSORT_BACKEND = r"""
consort_impl_model() {
  case "${CONSORT_BACKEND:-codex}" in
    gemini)
      printf '%s\n' "${CONSORT_GEMINI_MODEL:-gemini-3.1-pro-preview}"
      ;;
    pi)
      p="${CONSORT_PI_PROVIDER:-openai-codex}"
      if [ -n "${CONSORT_PI_MODEL:-}" ]; then
        printf '%s\n' "$p/$CONSORT_PI_MODEL"
        return 0
      fi
      case "$p" in
        openai|openai-codex)
          printf '%s\n' "$p/${CONSORT_IMPL_MODEL:-gpt-5.6-sol}"
          ;;
        google*)
          printf '%s\n' "$p/${CONSORT_GEMINI_MODEL:-gemini-3.1-pro-preview}"
          ;;
        anthropic)
          printf '%s\n' "$p/claude-opus-4-8"
          ;;
        *)
          printf '%s/\n' "$p"
          ;;
      esac
      ;;
    *)
      printf '%s\n' "${CONSORT_IMPL_MODEL:-gpt-5.6-sol}"
      ;;
  esac
}

consort_codex_backend() {
  case "${CONSORT_CODEX_BACKEND:-auto}" in
    exec) printf '%s\n' exec; return 0 ;;
    plugin)
      printf '%s\n' plugin
      return 0
      ;;
    *)
      if command -v codex >/dev/null 2>&1; then
        printf '%s\n' exec
        return 0
      fi
      echo "neither Codex plugin nor CLI" >&2
      return 1
      ;;
  esac
}

_consort_companion_path() {
  ls -d "$HOME"/.claude/plugins/cache/*/codex/*/scripts/codex-companion.mjs 2>/dev/null \
    | sort -V | tail -1
}

consort_gemini_transport() {
  case "${CONSORT_GEMINI_TRANSPORT:-auto}" in
    cli) printf '%s\n' cli; return 0 ;;
    api) printf '%s\n' api; return 0 ;;
    *)
      if command -v gemini >/dev/null 2>&1; then
        printf '%s\n' cli
      else
        printf '%s\n' api
      fi
      ;;
  esac
}
"""


def _hash_file(path: Path) -> bytes:
    if not path.is_file():
        return b""
    return hashlib.sha256(path.read_bytes()).digest()


CHISLE_SHA = "a5486fa112c961f9b25349a29ede38cc9f2a1a5c"

class Fixture:
    def __init__(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="sf-ws-"))
        self.home = self.tmp / "home"
        self.cfg = self.tmp / "App Support" / "claude"
        self.stub = self.tmp / "stub"
        self.unix = self.tmp / "unix"
        self.cwd = self.tmp / "work"
        self.consort = self.tmp / "consort"
        self.log = self.tmp / "stub.log"
        self.path = f"{self.stub}:{self.unix}"
        for d in (self.home, self.cfg, self.stub, self.unix, self.cwd, self.consort / "scripts"):
            d.mkdir(parents=True)
        (self.tmp / "tmp").mkdir()
        self.log.write_text("")
        self._unix()
        self._consort()
        self._user_tree()

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _unix(self) -> None:
        for name in UNIX_NAMES:
            real = shutil.which(name)
            if real is None:
                continue
            dest = self.unix / name
            if dest.exists():
                continue
            dest.symlink_to(real)

    def _consort(self) -> None:
        scripts = self.consort / "scripts"
        (scripts / "consort-backend.sh").write_text(CONSORT_BACKEND)
        (scripts / "consort-panel.sh").write_text("#!/bin/bash\n")
        (scripts / "pi-backend.sh").write_text("# fixture\n")
        (scripts / "pi-fence.mjs").write_text("export default {}\n")

    def _user_tree(self) -> None:
        (self.home / ".memspec" / "memory").mkdir(parents=True)
        (self.home / ".memspec" / "memory" / "keep").write_text("x")
        hooks = self.cfg / "hooks"
        hooks.mkdir()
        (hooks / "memspec-session-start.js").write_text("")
        (hooks / "memspec-consolidate.js").write_text("")
        (self.home / "git" / "cleat" / "quality" / "bin").mkdir(parents=True)
        (self.home / "git" / "cleat" / "quality" / "bin" / "keep").write_text("")
        (self.cfg / "plugins").mkdir()
        self.chisle_install()
        self.write_settings(
            {
                "enabledPlugins": {
                    "claude-hud@claude-hud": True,
                    "secret-guard@software-factory": True,
                    "consort@consort": True,
                }
            }
        )

    def chisle_install(
        self,
        sha: str = CHISLE_SHA,
        ref: str | None = "v3.0.0",
        scope: str = "user",
        kind: str = "github",
        loadable: bool = True,
    ) -> None:
        source = {"source": kind, "repo": "JayPokale/Chisle"}
        if ref is not None:
            source["ref"] = ref
        (self.cfg / "plugins" / "known_marketplaces.json").write_text(
            json.dumps({"software-factory": {}, "chisle": {"source": source}})
        )
        install = self.cfg / "plugins" / "cache" / "chisle" / "chisle" / "3.0.0"
        (install / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        (install / ".claude-plugin" / "plugin.json").write_text('{"name": "chisle"}')
        if not loadable:
            (install / ".claude-plugin" / "plugin.json").unlink()
        entry = {"scope": scope, "version": "3.0.0", "gitCommitSha": sha, "installPath": str(install)}
        (self.cfg / "plugins" / "installed_plugins.json").write_text(
            json.dumps({"version": 2, "plugins": {"chisle@chisle": [entry]}})
        )

    def write_settings(self, data: dict) -> None:
        data.setdefault("hooks", self.memspec_hooks(str(self.cfg / "hooks")))
        (self.cfg / "settings.json").write_text(json.dumps(data))

    @staticmethod
    def memspec_hooks(hooks_dir: str) -> dict:
        def entry(name: str) -> dict:
            return {"hooks": [{"type": "command", "command": f'node "{hooks_dir}/{name}"', "timeout": 5}]}

        return {
            "SessionStart": [entry("memspec-session-start.js")],
            "PostToolUse": [{**entry("memspec-consolidate.js"), "matcher": "Bash"}],
        }

    def write_stub(self, name: str, body: str) -> None:
        path = self.stub / name
        path.write_text(body)
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def version_stub(self, name: str, version: str = "stub-1", extra: str = "") -> None:
        self.write_stub(
            name,
            f"""#!/usr/bin/env bash
echo "$(basename "$0") $*" >> "${{STUB_LOG:-/dev/null}}"
{extra}
if [ "${{1:-}}" = "--version" ] || [ "${{1:-}}" = "-v" ] || [ "${{1:-}}" = "-V" ]; then
  printf '%s\\n' {version!r}
  exit 0
fi
printf '%s stub\\n' {name!r}
exit 0
""",
        )

    def base_stubs(self, pm: bool = False) -> None:
        for name in BASE_STUBS:
            extra = ""
            if name == "claude":
                extra = """
if [ "${1:-}" = "auth" ]; then exit 0; fi
if [ "${1:-}" = "mcp" ]; then printf 'memspec:\\n  Scope: %s\\n' "${STUB_MCP_SCOPE:-User config (available in all your projects)}"; exit 0; fi
"""
            elif name == "gh":
                extra = """
if [ "${1:-}" = "auth" ]; then exit 0; fi
"""
            elif name == "docker":
                extra = """
if [ "${1:-}" = "info" ]; then exit 0; fi
if [ "${1:-}" = "ps" ]; then printf 'sonarqube\\n'; exit 0; fi
"""
            self.version_stub(name, extra=extra)
        if not pm:
            self.version_stub("uv")
            self.version_stub("pnpm")

    def reviewer_stubs(self, *names: str, pi_version: str = "0.84.1") -> None:
        for name in names:
            if name == "pi":
                self.write_stub(
                    "pi",
                    f"""#!/usr/bin/env bash
echo "pi $*" >> "${{STUB_LOG:-/dev/null}}"
if [ "${{1:-}}" = "--version" ]; then printf '%s\\n' {pi_version!r}; exit 0; fi
echo "pi stub unexpected: $*" >> "${{STUB_LOG:-/dev/null}}"
exit 99
""",
                )
            elif name == "gcloud":
                self.write_stub(
                    "gcloud",
                    """#!/usr/bin/env bash
echo "gcloud $*" >> "${STUB_LOG:-/dev/null}"
if [ "${1:-}" = "--version" ]; then printf 'Google Cloud SDK 000\\n'; exit 0; fi
if [ "${1:-}" = "config" ] && [ "${2:-}" = "get-value" ]; then
  printf '%s\\n' "${GCLOUD_PROJECT:-}"
  exit 0
fi
exit 0
""",
                )
            elif name == "codex":
                self.version_stub("codex", "codex-stub")
            elif name == "gemini":
                self.version_stub("gemini", "gemini-stub")
            elif name in ("rg", "fd", "fdfind"):
                self.version_stub(name, "1")
            else:
                self.version_stub(name)

    def adc(self) -> Path:
        path = self.home / ".config" / "gcloud" / "application_default_credentials.json"
        path.parent.mkdir(parents=True)
        path.write_text('{"type":"authorized_user"}')
        return path

    def creds_file(self, name: str = "sa.json") -> Path:
        path = self.home / name
        path.write_text('{"type":"service_account"}')
        return path

    def companion(self) -> Path:
        path = (
            self.home
            / ".claude"
            / "plugins"
            / "cache"
            / "openai"
            / "codex"
            / "1.0.0"
            / "scripts"
            / "codex-companion.mjs"
        )
        path.parent.mkdir(parents=True)
        path.write_text("export {}\n")
        return path

    def env(self, extra: dict | None = None) -> dict:
        out = {
            "HOME": str(self.home),
            "PATH": self.path,
            "CLAUDE_CONFIG_DIR": str(self.cfg),
            "PWD": str(self.cwd),
            "STUB_LOG": str(self.log),
            "LANG": "C",
            "LC_ALL": "C",
            "TMPDIR": str(self.tmp / "tmp"),
        }
        if extra:
            out.update(extra)
        return out

    def run(
        self,
        extra: dict | None = None,
        args: list[str] | None = None,
        consort: Path | None = None,
    ) -> subprocess.CompletedProcess:
        argv = ["bash", str(CHECKER)]
        if args is None:
            argv += ["--consort-root", str(consort or self.consort)]
        else:
            argv += args
        return subprocess.run(
            argv,
            env=self.env(extra),
            cwd=str(self.cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def snapshot(self, paths: list[Path]) -> dict:
        return {str(p): _hash_file(p) for p in paths}


class CheckWorkstationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.fx.base_stubs()

    def tearDown(self) -> None:
        self.fx.close()

    def _out(self, proc: subprocess.CompletedProcess) -> str:
        return proc.stdout + "\n" + proc.stderr

    def _assert_no_forbidden(self) -> None:
        log = self.fx.log.read_text() if self.fx.log.exists() else ""
        for frag in FORBIDDEN_FRAGMENTS:
            self.assertNotIn(frag, log)

    def _reference_run(self) -> tuple[str, int]:
        self.fx.reviewer_stubs("codex", "pi", "gcloud", "rg", "fd")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "CONSORT_CODEX_BACKEND": "exec",
            }
        )
        return self._out(proc), proc.returncode

    def test_memspec_user_scope_and_hooks_ok(self) -> None:
        out, code = self._reference_run()
        self.assertEqual(code, 0, out)
        self.assertIn("OK       memspec MCP (user scope)", out)
        self.assertIn("OK       hook memspec-session-start.js", out)
        self.assertIn("OK       hook memspec-consolidate.js", out)

    def test_memspec_project_scope_only_missing(self) -> None:
        self.fx.reviewer_stubs("codex", "pi", "gcloud", "rg", "fd")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "CONSORT_CODEX_BACKEND": "exec",
                "STUB_MCP_SCOPE": "Project config (shared via .mcp.json)",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  memspec MCP (user scope)", out)
        self.assertIn("Project config", out)

    def test_memspec_hooks_registered_in_other_config_dir(self) -> None:
        settings = json.loads((self.fx.cfg / "settings.json").read_text())
        settings["hooks"] = self.fx.memspec_hooks("$HOME/.claude/hooks")
        self.fx.write_settings(settings)
        out, code = self._reference_run()
        self.assertEqual(code, 0, out)
        self.assertIn("OPTIONAL hook memspec-session-start.js", out)
        self.assertIn("not registered in", out)
        self.assertIn("with this CLAUDE_CONFIG_DIR: memspec init ~/.memspec", out)

    def test_memspec_hooks_single_quoted_as_memspec_writes_them(self) -> None:
        # memspec 0.12.3 registers `node '<abs path>'`; the config dir path has a space.
        settings = json.loads((self.fx.cfg / "settings.json").read_text())
        hooks = self.fx.cfg / "hooks"
        settings["hooks"] = {
            "SessionStart": [{"hooks": [{"type": "command", "command": f"node '{hooks}/memspec-session-start.js'"}]}],
            "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": f"node '{hooks}/memspec-consolidate.js'"}]}],
        }
        self.fx.write_settings(settings)
        out, code = self._reference_run()
        self.assertEqual(code, 0, out)
        self.assertIn("OK       hook memspec-session-start.js", out)
        self.assertIn("OK       hook memspec-consolidate.js", out)

    def test_memspec_hooks_exec_form_ok(self) -> None:
        settings = json.loads((self.fx.cfg / "settings.json").read_text())
        hooks = self.fx.cfg / "hooks"
        settings["hooks"] = {
            "SessionStart": [{"hooks": [{"type": "command", "command": "node", "args": [f"{hooks}/memspec-session-start.js"]}]}],
            "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "node", "args": [f"{hooks}/memspec-consolidate.js"]}]}],
        }
        self.fx.write_settings(settings)
        out, code = self._reference_run()
        self.assertEqual(code, 0, out)
        self.assertIn("OK       hook memspec-session-start.js", out)
        self.assertIn("OK       hook memspec-consolidate.js", out)

    def test_memspec_hooks_exec_form_args_are_not_expanded(self) -> None:
        # Exec form spawns without a shell, so "$HOME/..." reaches node literally and fails.
        settings = json.loads((self.fx.cfg / "settings.json").read_text())
        rel = os.path.relpath(self.fx.cfg / "hooks", self.fx.home)
        settings["hooks"] = {
            "SessionStart": [{"hooks": [{"type": "command", "command": "node", "args": [f"$HOME/{rel}/memspec-session-start.js"]}]}],
        }
        self.fx.write_settings(settings)
        out, code = self._reference_run()
        self.assertEqual(code, 0, out)
        self.assertIn("OPTIONAL hook memspec-session-start.js", out)
        self.assertIn("not registered in", out)

    def test_memspec_older_than_0_12_3_warns_under_a_config_dir(self) -> None:
        self.fx.version_stub("memspec", version="0.11.0")
        out, code = self._reference_run()
        self.assertEqual(code, 0, out)
        self.assertIn("OPTIONAL memspec 0.11.0", out)
        self.assertIn("ignores CLAUDE_CONFIG_DIR", out)
        self.fx.version_stub("memspec", version="0.12.3")
        out = self._out(
            self.fx.run(
                {
                    "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                    "CONSORT_GCP_PROJECT": "example-project",
                    "CONSORT_CODEX_BACKEND": "exec",
                }
            )
        )
        self.assertIn("OK       memspec", out)
        self.assertNotIn("ignores CLAUDE_CONFIG_DIR", out)

    def test_chisle_pinned_user_install_ok(self) -> None:
        out, code = self._reference_run()
        self.assertEqual(code, 0, out)
        self.assertIn("OK       plugin chisle@chisle (user scope, pinned commit", out)
        self.assertNotIn("chisle off at user scope", out)

    def test_chisle_other_commit_missing(self) -> None:
        self.fx.chisle_install(sha="0" * 40)
        out, code = self._reference_run()
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING  plugin chisle@chisle", out)

    def test_chisle_unpinned_marketplace_missing(self) -> None:
        self.fx.chisle_install(ref=None)
        out, code = self._reference_run()
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING  plugin chisle@chisle", out)

    def test_chisle_project_scope_only_missing(self) -> None:
        self.fx.chisle_install(scope="project")
        out, code = self._reference_run()
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING  plugin chisle@chisle", out)

    def test_chisle_missing_install_path_missing(self) -> None:
        self.fx.chisle_install(loadable=False)
        out, code = self._reference_run()
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING  plugin chisle@chisle", out)

    def test_chisle_non_github_source_missing(self) -> None:
        self.fx.chisle_install(kind="directory")
        out, code = self._reference_run()
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING  plugin chisle@chisle", out)

    def test_chisle_on_for_every_repository_fails(self) -> None:
        self.fx.write_settings(
            {
                "enabledPlugins": {
                    "claude-hud@claude-hud": True,
                    "secret-guard@software-factory": True,
                    "consort@consort": True,
                    "chisle@chisle": True,
                }
            }
        )
        out, code = self._reference_run()
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING  chisle off at user scope", out)

    def test_vertex_reference_success(self) -> None:
        self.fx.reviewer_stubs("codex", "pi", "gcloud", "rg", "fd")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "CONSORT_CODEX_BACKEND": "exec",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("OK       env CONSORT_GCP_PROJECT", out)
        self.assertIn("OK       gcloud", out)
        self.assertNotIn("MISSING  gcloud ADC", out)
        self._assert_no_forbidden()

    def test_vertex_missing_project(self) -> None:
        self.fx.reviewer_stubs("codex", "pi", "gcloud", "rg", "fd")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_CODEX_BACKEND": "exec",
                "GCLOUD_PROJECT": "",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_PROJECT", out)

    def test_vertex_missing_credentials(self) -> None:
        self.fx.reviewer_stubs("codex", "pi", "gcloud", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "CONSORT_CODEX_BACKEND": "exec",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  gcloud ADC", out)

    def test_vertex_credentials_file_without_gcloud(self) -> None:
        self.fx.reviewer_stubs("codex", "pi", "rg", "fd")
        creds = self.fx.creds_file()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "CONSORT_GCP_CREDENTIALS": str(creds),
                "CONSORT_CODEX_BACKEND": "exec",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertNotIn("MISSING  gcloud", out)
        self.assertIn("SKIP     gcloud", out)
        self.assertIn("OK       env CONSORT_GCP_CREDENTIALS", out)

    def test_vertex_invalid_credentials_despite_adc(self) -> None:
        self.fx.reviewer_stubs("codex", "pi", "gcloud", "rg", "fd")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "CONSORT_GCP_CREDENTIALS": str(self.fx.home / "missing-sa.json"),
                "CONSORT_CODEX_BACKEND": "exec",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_CREDENTIALS", out)

    def test_local_pi_skips_gcp(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        settings = json.loads((self.fx.cfg / "settings.json").read_text())
        settings["env"] = {"CONSORT_REVIEWERS": "codex,pi:google-vertex"}
        self.fx.write_settings(settings)
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:xai:example-model"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("SKIP     gcloud", out)
        self.assertIn("SKIP     env CONSORT_GCP_PROJECT", out)
        self.assertNotIn("MISSING  gcloud", out)
        self.assertNotIn("MISSING  gemini", out)
        self.assertNotIn("MISSING  codex", out)
        self.assertIn("process value used", out)
        self.assertIn("UNVERIFIED; no model request was sent", out)
        self._assert_no_forbidden()

    def test_local_pi_missing_binary(self) -> None:
        self.fx.reviewer_stubs("rg", "fd")
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:xai:example-model"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  pi", out)

    def test_local_pi_failed_version(self) -> None:
        self.fx.reviewer_stubs("rg", "fd")
        self.fx.write_stub(
            "pi",
            """#!/usr/bin/env bash
echo "pi $*" >> "${STUB_LOG:-/dev/null}"
printf '0.84.1\\n'
exit 1
""",
        )
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:xai:example-model"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  pi", out)
        self.assertIn("version command failed", out)

    def test_local_pi_old_version(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd", pi_version="0.83.0")
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:xai:example-model"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  pi", out)
        self.assertIn("0.84.0", out)

    def test_local_pi_missing_model(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:xai"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  model pi:xai", out)
        self.assertIn("no nonempty provider/model", out)

    def test_local_pi_missing_profile(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi:xai:example-model",
                "PI_CODING_AGENT_DIR": str(self.fx.home / "no-profile"),
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  PI_CODING_AGENT_DIR", out)

    def test_local_pi_missing_rg(self) -> None:
        self.fx.reviewer_stubs("pi", "fd")
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:xai:example-model"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  rg", out)

    def test_non_vertex_google_invalid_credentials(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi:google:example-model",
                "CONSORT_GCP_CREDENTIALS": str(self.fx.home / "missing-sa.json"),
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_CREDENTIALS", out)
        self.assertNotIn("MISSING  env CONSORT_GCP_PROJECT", out)

    def test_non_vertex_google_provider(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:google:example-model"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("SKIP     gcloud", out)
        self.assertIn("SKIP     env CONSORT_GCP_PROJECT", out)

    def test_two_generic_providers(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:alpha:model-a,pi:beta:model-b"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("OK       pi", out)
        self.assertIn("model pi:alpha:model-a", out)
        self.assertIn("alpha/model-a", out)
        self.assertIn("model pi:beta:model-b", out)
        self.assertIn("beta/model-b", out)

    def test_mixed_panel_vertex_failure(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi:google-vertex,pi:xai:example-model",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_PROJECT", out)

    def test_malformed_specs(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        for spec in BAD_SPECS:
            with self.subTest(spec=spec):
                self.fx.log.write_text("")
                proc = self.fx.run({"CONSORT_REVIEWERS": spec})
                out = self._out(proc)
                self.assertEqual(proc.returncode, 1, out)
                self.assertIn("MISSING  CONSORT_REVIEWERS", out)
                log = self.fx.log.read_text()
                self.assertNotIn("\npi ", "\n" + log)
                self.assertNotIn("pi --", log)

        self.fx.log.write_text("")
        proc = self.fx.run({"CONSORT_REVIEWERS": "codex:" + "x\033[2J"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("control characters", out)

    def test_empty_string_is_not_default(self) -> None:
        self.fx.reviewer_stubs("codex")
        proc = self.fx.run({"CONSORT_REVIEWERS": ""})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  CONSORT_REVIEWERS", out)
        self.assertIn("empty", out)

    def test_unset_defaults_to_codex(self) -> None:
        self.fx.reviewer_stubs("codex")
        proc = self.fx.run({"CONSORT_CODEX_BACKEND": "exec"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("Consort default codex", out)
        self.assertIn("SKIP     gcloud", out)
        self.assertIn("SKIP     env CONSORT_GCP_PROJECT", out)

    def test_codex_only_route_is_flagged_not_failed(self) -> None:
        self.fx.reviewer_stubs("codex")
        proc = self.fx.run({"CONSORT_REVIEWERS": "codex", "CONSORT_CODEX_BACKEND": "exec"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("OPTIONAL reviewer panel", out)
        self.assertIn("Codex-only route", out)
        self.assertIn("SKIP     gcloud", out)

    def test_two_vendor_panel_has_no_codex_only_line(self) -> None:
        self.fx.reviewer_stubs("codex", "pi", "gcloud", "rg", "fd")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "CONSORT_CODEX_BACKEND": "exec",
            }
        )
        self.assertNotIn("Codex-only route", self._out(proc))

    def test_settings_only_is_inactive(self) -> None:
        self.fx.reviewer_stubs("codex")
        settings = json.loads((self.fx.cfg / "settings.json").read_text())
        settings["env"] = {
            "CONSORT_REVIEWERS": "codex,pi:google-vertex",
            "CONSORT_GCP_PROJECT": "example-project",
        }
        self.fx.write_settings(settings)
        proc = self.fx.run({"CONSORT_CODEX_BACKEND": "exec"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("settings value is not active in this process", out)
        self.assertIn("SKIP     env CONSORT_GCP_PROJECT", out)
        self.assertNotIn("MISSING  env CONSORT_GCP_PROJECT", out)

    def test_pm_bypasses_reviewers(self) -> None:
        self.fx.close()
        self.fx = Fixture()
        self.fx.base_stubs(pm=True)
        self.fx.write_settings(
            {
                "enabledPlugins": {
                    "pm-workspace@software-factory": True,
                    "secret-guard@software-factory": True,
                }
            }
        )
        proc = self.fx.run(
            {"CONSORT_REVIEWERS": "pi::bad"},
            args=["--pm"],
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("PM profile", out)
        self.assertNotIn("MISSING  CONSORT_REVIEWERS", out)
        self.assertNotIn("MISSING  pi", out)
        self.assertNotIn("== second vendor", out)
        log = self.fx.log.read_text()
        self.assertNotIn("\npi ", "\n" + log)

    def test_unknown_argument(self) -> None:
        self.fx.reviewer_stubs("pi")
        proc = self.fx.run(args=["--probe"])
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("unknown argument", out)
        self.assertEqual(self.fx.log.read_text(), "")

    def test_missing_consort_root_value(self) -> None:
        self.fx.reviewer_stubs("pi")
        proc = self.fx.run(args=["--consort-root"])
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("--consort-root needs a path", out)
        self.assertEqual(self.fx.log.read_text(), "")

    def test_duplicate_identity(self) -> None:
        self.fx.reviewer_stubs("codex")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex,codex:gpt-5.6-sol",
                "CONSORT_CODEX_BACKEND": "exec",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("same reviewer", out)

    def test_bare_pi_inherits_ambient(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi",
                "CONSORT_PI_PROVIDER": "alpha",
                "CONSORT_PI_MODEL": "ambient-model",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("alpha/ambient-model", out)

    def test_provider_only_unsets_ambient_model(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd", "gcloud")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi:google-vertex",
                "CONSORT_PI_MODEL": "gpt-ambient",
                "CONSORT_GCP_PROJECT": "example-project",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("google-vertex/gemini-3.1-pro-preview", out)
        self.assertNotIn("gpt-ambient", out)

    def test_gemini_cli_versus_token_api(self) -> None:
        self.fx.reviewer_stubs("gemini", "gcloud")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "gemini",
                "CONSORT_GEMINI_TRANSPORT": "cli",
                "CONSORT_GCP_PROJECT": "example-project",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("OK       gemini", out)
        self.assertIn("OK       gcloud", out)

        self.fx.close()
        self.fx = Fixture()
        self.fx.base_stubs()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "gemini",
                "CONSORT_GEMINI_TRANSPORT": "api",
                "CONSORT_GEMINI_TOKEN": "dummy-token",
                "CONSORT_GCP_PROJECT": "example-project",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("SKIP     gcloud", out)
        self.assertNotIn("MISSING  gemini", out)
        self.assertNotIn("dummy-token", out)

    def test_codex_plugin_transport(self) -> None:
        self.fx.companion()
        settings = json.loads((self.fx.cfg / "settings.json").read_text())
        settings["enabledPlugins"]["codex@openai-codex"] = True
        self.fx.write_settings(settings)
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "codex",
                "CONSORT_CODEX_BACKEND": "plugin",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("OK       plugin codex@openai-codex", out)
        self.assertIn("OK       codex companion", out)
        self.assertNotIn("MISSING  codex ", out)

    def test_project_settings_ignored(self) -> None:
        self.fx.reviewer_stubs("codex")
        proj = self.fx.cwd / ".claude"
        proj.mkdir()
        (proj / "settings.json").write_text(
            json.dumps({"env": {"CONSORT_REVIEWERS": "codex,pi:google-vertex"}})
        )
        proc = self.fx.run({"CONSORT_CODEX_BACKEND": "exec"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("OPTIONAL tracked project CONSORT_*", out)
        self.assertIn("SKIP     env CONSORT_GCP_PROJECT", out)

    def test_anthropic_same_vendor(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:anthropic"})
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  pi provider anthropic", out)

    def test_bare_pi_ambient_vertex_requires_project(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi",
                "CONSORT_PI_PROVIDER": "google-vertex",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_PROJECT", out)
        self.assertNotIn("SKIP     env CONSORT_GCP_PROJECT", out)

    def test_bare_pi_ambient_anthropic_refused(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi",
                "CONSORT_PI_PROVIDER": "anthropic",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  pi provider anthropic", out)

    def test_bare_pi_ambient_google_invalid_credentials(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi",
                "CONSORT_PI_PROVIDER": "google",
                "CONSORT_GCP_CREDENTIALS": "no-such-file.json",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_CREDENTIALS", out)

    def test_mixed_bare_pi_ambient_vertex(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi,pi:xai:example-model",
                "CONSORT_PI_PROVIDER": "google-vertex",
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_PROJECT", out)
        self.assertIn("model pi", out)
        self.assertIn("model pi:xai:example-model", out)
        self.assertIn("xai/example-model", out)

    def test_explicit_gac_does_not_fallback_to_adc(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd", "gcloud")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "GOOGLE_APPLICATION_CREDENTIALS": str(self.fx.home / "missing.json"),
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  gcloud ADC", out)
        self.assertIn("GOOGLE_APPLICATION_CREDENTIALS is set but not a readable regular file", out)

    def test_explicit_gac_valid_without_gcloud(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        creds = self.fx.creds_file("gac.json")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "GOOGLE_APPLICATION_CREDENTIALS": str(creds),
            }
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertNotIn("MISSING  gcloud", out)
        self.assertIn("SKIP     gcloud", out)
        self.assertIn("GOOGLE_APPLICATION_CREDENTIALS file present", out)

    def test_fixtures_unchanged_and_no_forbidden_calls(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        creds = self.fx.creds_file()
        settings = self.fx.cfg / "settings.json"
        before = self.fx.snapshot([settings, creds])
        proc = self.fx.run({"CONSORT_REVIEWERS": "pi:xai:example-model"})
        self.assertEqual(proc.returncode, 0, self._out(proc))
        after = self.fx.snapshot([settings, creds])
        self.assertEqual(before, after)
        self._assert_no_forbidden()


def _real_consort() -> Path:
    raw = os.environ.get("SOFTWARE_FACTORY_CONSORT_ROOT", "")
    if not raw:
        raise unittest.SkipTest("SOFTWARE_FACTORY_CONSORT_ROOT unset")
    root = Path(raw)
    if not (root / "scripts" / "consort-backend.sh").is_file():
        raise unittest.SkipTest("SOFTWARE_FACTORY_CONSORT_ROOT missing consort-backend.sh")
    return root


class RealConsortBlockers(unittest.TestCase):
    def setUp(self) -> None:
        self.root = _real_consort()
        self.fx = Fixture()
        self.fx.base_stubs()

    def tearDown(self) -> None:
        self.fx.close()

    def _out(self, proc: subprocess.CompletedProcess) -> str:
        return proc.stdout + "\n" + proc.stderr

    def test_ambient_vertex_against_real_resolver(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi",
                "CONSORT_PI_PROVIDER": "google-vertex",
            },
            consort=self.root,
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  env CONSORT_GCP_PROJECT", out)

    def test_ambient_anthropic_against_real_resolver(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi",
                "CONSORT_PI_PROVIDER": "anthropic",
            },
            consort=self.root,
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  pi provider anthropic", out)

    def test_explicit_gac_against_real_resolver(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd", "gcloud")
        self.fx.adc()
        proc = self.fx.run(
            {
                "CONSORT_REVIEWERS": "pi:google-vertex",
                "CONSORT_GCP_PROJECT": "example-project",
                "GOOGLE_APPLICATION_CREDENTIALS": str(self.fx.home / "missing.json"),
            },
            consort=self.root,
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("MISSING  gcloud ADC", out)

    def test_two_models_against_real_resolver(self) -> None:
        self.fx.reviewer_stubs("pi", "rg", "fd")
        proc = self.fx.run(
            {"CONSORT_REVIEWERS": "pi:alpha:model-a,pi:beta:model-b"},
            consort=self.root,
        )
        out = self._out(proc)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("alpha/model-a", out)
        self.assertIn("beta/model-b", out)


if __name__ == "__main__":
    unittest.main()
