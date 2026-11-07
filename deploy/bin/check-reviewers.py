#!/usr/bin/env python3
"""Route-aware Consort reviewer prerequisite checks. Stdlib only. Read-only."""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple

OK = "OK"
MISSING = "MISSING"
OPTIONAL = "OPTIONAL"
SKIP = "SKIP"
PI_MIN = (0, 84, 0)
RESOLVE_TIMEOUT_S = 8
VERSION_TIMEOUT_S = 5
MAX_RESOLVE_BYTES = 4096
USAGE = "usage: check-reviewers.py [--consort-root PATH]"
_RESOLVE = r"""
set -e
root=$1
action=$2
. "$root/scripts/consort-backend.sh"
case $action in
  model) consort_impl_model ;;
  codex-transport) consort_codex_backend ;;
  gemini-transport) consort_gemini_transport ;;
  codex-companion) _consort_companion_path ;;
  *) exit 2 ;;
esac
"""
_CONTROL = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")
_LABEL_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


class ConfigError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Leg:
    index: int
    spec: str
    label: str
    backend: str
    provider: Optional[str]
    explicit_model: Optional[str]
    overrides: Mapping[str, str]
    unsets: FrozenSet[str]


@dataclass(frozen=True)
class Requirement:
    subject: str
    state: str
    detail: str
    legs: Tuple[int, ...] = ()


class Report:
    def __init__(self) -> None:
        self.rows: List[Requirement] = []
        self._index: Dict[str, int] = {}

    def add(
        self,
        subject: str,
        state: str,
        detail: str,
        legs: Iterable[int] = (),
    ) -> None:
        legs_t = tuple(legs)
        if subject in self._index:
            i = self._index[subject]
            prev = self.rows[i]
            if prev.state == MISSING:
                return
            if state == MISSING:
                self.rows[i] = Requirement(subject, state, detail, legs_t)
            return
        self._index[subject] = len(self.rows)
        self.rows.append(Requirement(subject, state, detail, legs_t))


def format_line(req: Requirement) -> str:
    return f"{req.state:<8} {req.subject:<28} {req.detail}".rstrip()


def sanitize_label(spec: str) -> str:
    return _LABEL_UNSAFE.sub("_", spec.replace(":", "-"))


def parse_legs(raw: Optional[str], present: bool) -> List[Leg]:
    if not present:
        return [_parse_spec("codex", 0)]
    if raw is None:
        raise ConfigError("CONSORT_REVIEWERS is empty")
    if _CONTROL.search(raw):
        raise ConfigError("CONSORT_REVIEWERS contains control characters")
    if raw.strip() == "":
        raise ConfigError("CONSORT_REVIEWERS is empty")
    parts = raw.split(",")
    specs: List[str] = []
    for part in parts:
        spec = part.replace(" ", "").replace("\t", "")
        if spec == "":
            raise ConfigError("CONSORT_REVIEWERS contains an empty leg")
        specs.append(spec)
    legs: List[Leg] = []
    labels = set()
    for i, spec in enumerate(specs):
        leg = _parse_spec(spec, i)
        if leg.label in labels:
            raise ConfigError(f"duplicate leg '{spec}'")
        labels.add(leg.label)
        legs.append(leg)
    if not legs:
        raise ConfigError("CONSORT_REVIEWERS names no leg")
    return legs


def _parse_spec(spec: str, index: int) -> Leg:
    if "::" in spec or spec.endswith(":"):
        raise ConfigError(f"bad leg '{spec}' (empty field)")
    bits = spec.split(":")
    if len(bits) > 3:
        raise ConfigError(f"bad leg '{spec}' (too many ':' fields)")
    backend = bits[0]
    a = bits[1] if len(bits) > 1 else ""
    b = bits[2] if len(bits) > 2 else ""
    overrides: Dict[str, str] = {"CONSORT_BACKEND": backend}
    unsets: FrozenSet[str] = frozenset()
    provider: Optional[str] = None
    explicit_model: Optional[str] = None
    if backend == "codex":
        if b:
            raise ConfigError(f"bad leg '{spec}' (codex takes at most one field: codex[:model])")
        if a:
            overrides["CONSORT_IMPL_MODEL"] = a
            explicit_model = a
    elif backend == "gemini":
        if b:
            raise ConfigError(f"bad leg '{spec}' (gemini takes at most one field: gemini[:model])")
        if a:
            overrides["CONSORT_GEMINI_MODEL"] = a
            explicit_model = a
    elif backend == "pi":
        if a:
            provider = a
            overrides["CONSORT_PI_PROVIDER"] = a
            if b:
                overrides["CONSORT_PI_MODEL"] = b
                explicit_model = b
            else:
                unsets = frozenset({"CONSORT_PI_MODEL"})
        elif b:
            raise ConfigError(
                f"bad leg '{spec}' (a pi model needs a provider: pi:<provider>:<model>)"
            )
    else:
        raise ConfigError(f"unknown backend in leg '{spec}' (expected codex|gemini|pi)")
    return Leg(
        index=index,
        spec=spec,
        label=sanitize_label(spec),
        backend=backend,
        provider=provider,
        explicit_model=explicit_model,
        overrides=overrides,
        unsets=unsets,
    )


def which(name: str, env: Mapping[str, str]) -> Optional[str]:
    return shutil.which(name, path=env.get("PATH", ""))


def run_cmd(
    argv: Sequence[str],
    env: Mapping[str, str],
    timeout: float,
) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            list(argv),
            env=dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    blob = (proc.stdout or b"") + b"\n" + (proc.stderr or b"")
    text = blob.decode("utf-8", "replace")
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    return proc.returncode, first[:200]


def version_ok(name: str, argv: Sequence[str], env: Mapping[str, str]) -> Tuple[bool, str]:
    if which(name, env) is None:
        return False, "not on PATH"
    code, line = run_cmd(argv, env, VERSION_TIMEOUT_S)
    if code != 0:
        return False, "version command failed"
    return True, line or "ok"


def parse_pi_version(text: str) -> Optional[Tuple[int, int, int]]:
    token = re.split(r"[^\d.]", text.strip(), maxsplit=1)[0]
    core = token.split("-")[0]
    bits = core.split(".")
    try:
        nums = tuple(int(x) for x in bits[:3])
    except ValueError:
        return None
    if len(nums) < 3:
        nums = nums + (0,) * (3 - len(nums))
    return nums[0], nums[1], nums[2]


def is_regular_readable(path: str) -> bool:
    try:
        st = os.stat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return False
    if not stat.S_ISREG(st.st_mode):
        return False
    return os.access(path, os.R_OK)


def resolve_rel(path: str, cwd: str) -> str:
    if path.startswith("/"):
        return path
    return os.path.join(cwd, path)


def cfg_dir(env: Mapping[str, str]) -> str:
    home = env.get("HOME", "")
    return env.get("CLAUDE_CONFIG_DIR") or os.path.join(home, ".claude")


def load_settings_env(path: str) -> Dict[str, str]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    block = data.get("env")
    if not isinstance(block, dict):
        return {}
    out: Dict[str, str] = {}
    for key, val in block.items():
        if isinstance(key, str) and isinstance(val, str):
            out[key] = val
    return out


def plugin_enabled(env: Mapping[str, str], name: str) -> bool:
    path = os.path.join(cfg_dir(env), "settings.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, ValueError):
        return False
    plugins = data.get("enabledPlugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return False
    return bool(plugins.get(name))


def consort_files(root: str) -> List[str]:
    return [
        os.path.join(root, "scripts", "consort-panel.sh"),
        os.path.join(root, "scripts", "consort-backend.sh"),
        os.path.join(root, "scripts", "pi-backend.sh"),
        os.path.join(root, "scripts", "pi-fence.mjs"),
    ]


def consort_root_ok(root: str) -> Tuple[bool, str]:
    if not root or not os.path.isdir(root):
        return False, "not a directory"
    missing = [p for p in consort_files(root) if not os.path.isfile(p)]
    if missing:
        return False, "missing required scripts"
    return True, "ok"


def resolve_consort(
    root: str,
    action: str,
    env: Mapping[str, str],
) -> Tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["bash", "-c", _RESOLVE, "consort-resolve", root, action],
            env=dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=RESOLVE_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    out = (proc.stdout or b"")[:MAX_RESOLVE_BYTES].decode("utf-8", "replace").strip()
    line = out.splitlines()[0].strip() if out else ""
    if proc.returncode != 0:
        return False, line
    return True, line


def leg_env(base: Mapping[str, str], leg: Leg) -> Dict[str, str]:
    env = dict(base)
    for key in leg.unsets:
        env.pop(key, None)
    env.update(leg.overrides)
    return env


def effective_model(text: str, backend: str) -> Optional[str]:
    value = text.strip()
    if not value:
        return None
    if backend != "pi":
        return value
    provider, sep, model = value.partition("/")
    if sep == "" or provider == "" or model == "":
        return None
    return value


def effective_pi_provider(base: Mapping[str, str], leg: Leg) -> str:
    merged = leg_env(base, leg)
    return nonempty(merged, "CONSORT_PI_PROVIDER") or "openai-codex"


def selected_google_credential(env: Mapping[str, str], cwd: str) -> Tuple[str, str]:
    consort = nonempty(env, "CONSORT_GCP_CREDENTIALS")
    if consort:
        return "consort", resolve_rel(consort, cwd)
    gac = nonempty(env, "GOOGLE_APPLICATION_CREDENTIALS")
    if gac:
        return "gac", resolve_rel(gac, cwd)
    home = env.get("HOME", "")
    cloudsdk = env.get("CLOUDSDK_CONFIG") or os.path.join(home, ".config", "gcloud")
    return "adc", os.path.join(cloudsdk, "application_default_credentials.json")


def pi_tool_dir(env: Mapping[str, str]) -> str:
    home = env.get("HOME", "")
    return env.get("PI_CODING_AGENT_DIR") or os.path.join(home, ".pi", "agent")


def has_tool(name: str, env: Mapping[str, str]) -> bool:
    if which(name, env) is not None:
        return True
    alt = "fdfind" if name == "fd" else None
    if alt and which(alt, env) is not None:
        return True
    pidir = pi_tool_dir(env)
    return os.path.isfile(os.path.join(pidir, "bin", name)) and os.access(
        os.path.join(pidir, "bin", name), os.X_OK
    )


def nonempty(env: Mapping[str, str], key: str) -> str:
    val = env.get(key)
    if val:
        return val
    return ""


def diagnose_settings(report: Report, env: Mapping[str, str], defaulting: bool) -> None:
    cfg = os.path.join(cfg_dir(env), "settings.json")
    settings = load_settings_env(cfg)
    process_set = "CONSORT_REVIEWERS" in env
    settings_val = settings.get("CONSORT_REVIEWERS")
    if process_set and settings_val is not None and settings_val != env.get("CONSORT_REVIEWERS"):
        report.add(
            "settings CONSORT_REVIEWERS",
            OPTIONAL,
            "process value used; settings differ and are not active here",
        )
    elif (not process_set) and settings_val:
        detail = "settings value is not active in this process"
        if defaulting:
            detail += "; using Consort default codex"
        report.add("settings CONSORT_REVIEWERS", OPTIONAL, detail)
    project = os.path.join(os.getcwd(), ".claude", "settings.json")
    leaked = load_settings_env(project)
    if any(k.startswith("CONSORT_") for k in leaked):
        report.add(
            "tracked project CONSORT_*",
            OPTIONAL,
            "ignored (user or process config only)",
        )


def check_codex(report: Report, env: Mapping[str, str], root: str, legs: Sequence[Leg]) -> None:
    idxs = [leg.index for leg in legs]
    ok, transport = resolve_consort(root, "codex-transport", env)
    if not ok or transport not in ("exec", "plugin"):
        report.add("codex transport", MISSING, "Consort could not resolve exec or plugin", idxs)
        return
    report.add("codex transport", OK, transport, idxs)
    if transport == "exec":
        good, detail = version_ok("codex", ["codex", "--version"], env)
        report.add("codex", OK if good else MISSING, detail if good else "working CLI required", idxs)
    else:
        ok_c, companion = resolve_consort(root, "codex-companion", env)
        if not ok_c or not companion:
            report.add("codex companion", MISSING, "codex-companion.mjs not found under ~/.claude", idxs)
        else:
            report.add("codex companion", OK, "present", idxs)
        node_ok, node_detail = version_ok("node", ["node", "--version"], env)
        report.add(
            "node",
            OK if node_ok else MISSING,
            node_detail if node_ok else "plugin transport needs node",
            idxs,
        )
        if plugin_enabled(env, "codex@openai-codex"):
            report.add("plugin codex@openai-codex", OK, "enabled", idxs)
        else:
            report.add(
                "plugin codex@openai-codex",
                MISSING,
                "claude plugin install codex@openai-codex",
                idxs,
            )
    report.add("codex auth", OPTIONAL, "UNVERIFIED; no login or request was sent", idxs)


def check_gemini(report: Report, env: Mapping[str, str], root: str, legs: Sequence[Leg]) -> None:
    idxs = [leg.index for leg in legs]
    ok, transport = resolve_consort(root, "gemini-transport", env)
    if not ok or transport not in ("cli", "api"):
        report.add("gemini transport", MISSING, "Consort could not resolve cli or api", idxs)
        return
    report.add("gemini transport", OK, transport, idxs)
    token = nonempty(env, "CONSORT_GEMINI_TOKEN")
    if transport == "cli":
        good, detail = version_ok("gemini", ["gemini", "--version"], env)
        report.add("gemini", OK if good else MISSING, detail if good else "CLI transport needs gemini", idxs)
        g_ok, g_detail = version_ok("gcloud", ["gcloud", "--version"], env)
        report.add("gcloud", OK if g_ok else MISSING, g_detail if g_ok else "CLI transport needs gcloud", idxs)
    else:
        py_ok, py_detail = version_ok("python3", ["python3", "--version"], env)
        report.add("python3", OK if py_ok else MISSING, py_detail if py_ok else "API transport needs python3", idxs)
        if token:
            report.add("gemini token", OPTIONAL, "UNVERIFIED; token presence is not reachability", idxs)
        else:
            g_ok, g_detail = version_ok("gcloud", ["gcloud", "--version"], env)
            report.add(
                "gcloud",
                OK if g_ok else MISSING,
                g_detail if g_ok else "API transport needs gcloud or CONSORT_GEMINI_TOKEN",
                idxs,
            )
    project = nonempty(env, "CONSORT_GCP_PROJECT")
    if not project:
        code, line = run_cmd(["gcloud", "config", "get-value", "project"], env, VERSION_TIMEOUT_S)
        if code == 0 and line and line != "(unset)":
            project = line
    if project:
        report.add("env CONSORT_GCP_PROJECT", OK, "present", idxs)
    else:
        report.add(
            "env CONSORT_GCP_PROJECT",
            MISSING,
            "set CONSORT_GCP_PROJECT or gcloud config project",
            idxs,
        )
    report.add("gemini auth", OPTIONAL, "UNVERIFIED; no model request was sent", idxs)


def check_pi_google_vertex(
    report: Report,
    env: Mapping[str, str],
    cwd: str,
    legs: Sequence[Leg],
) -> None:
    idxs = [leg.index for leg in legs]
    project = nonempty(env, "CONSORT_GCP_PROJECT") or nonempty(env, "GOOGLE_CLOUD_PROJECT")
    if project:
        report.add("env CONSORT_GCP_PROJECT", OK, "present", idxs)
    else:
        report.add("env CONSORT_GCP_PROJECT", MISSING, "Vertex needs a billing project", idxs)
    kind, path = selected_google_credential(env, cwd)
    if kind == "consort":
        if is_regular_readable(path):
            report.add("env CONSORT_GCP_CREDENTIALS", OK, "readable file", idxs)
        else:
            report.add(
                "env CONSORT_GCP_CREDENTIALS",
                MISSING,
                "set but not a readable regular file",
                idxs,
            )
        return
    if kind == "gac":
        if is_regular_readable(path):
            report.add("gcloud ADC", OK, "GOOGLE_APPLICATION_CREDENTIALS file present (not probed)", idxs)
        else:
            report.add(
                "gcloud ADC",
                MISSING,
                "GOOGLE_APPLICATION_CREDENTIALS is set but not a readable regular file",
                idxs,
            )
        return
    g_ok, g_detail = version_ok("gcloud", ["gcloud", "--version"], env)
    report.add("gcloud", OK if g_ok else MISSING, g_detail if g_ok else "Vertex needs gcloud or a credentials file", idxs)
    if is_regular_readable(path):
        report.add("gcloud ADC", OK, "credentials file present (not probed)", idxs)
    else:
        report.add("gcloud ADC", MISSING, "ADC file missing (or set CONSORT_GCP_CREDENTIALS)", idxs)


def check_google_star_credentials(
    report: Report,
    env: Mapping[str, str],
    cwd: str,
    legs: Sequence[Leg],
) -> None:
    idxs = [leg.index for leg in legs]
    creds = nonempty(env, "CONSORT_GCP_CREDENTIALS")
    if not creds:
        return
    path = resolve_rel(creds, cwd)
    if is_regular_readable(path):
        report.add("env CONSORT_GCP_CREDENTIALS", OK, "readable file", idxs)
    else:
        report.add(
            "env CONSORT_GCP_CREDENTIALS",
            MISSING,
            "set but not a readable regular file",
            idxs,
        )


def check_pi(report: Report, env: Mapping[str, str], root: str, cwd: str, legs: Sequence[Leg]) -> None:
    idxs = [leg.index for leg in legs]
    good, detail = version_ok("pi", ["pi", "--version"], env)
    if not good:
        report.add("pi", MISSING, detail if detail == "not on PATH" else "version command failed", idxs)
    else:
        parsed = parse_pi_version(detail)
        if parsed is None:
            report.add("pi", MISSING, "could not parse version", idxs)
        elif parsed < PI_MIN:
            report.add("pi", MISSING, f"needs >= 0.84.0 (found {detail})", idxs)
        else:
            report.add("pi", OK, detail, idxs)
    py_ok, py_detail = version_ok("python3", ["python3", "--version"], env)
    report.add("python3", OK if py_ok else MISSING, py_detail if py_ok else "pi backend needs python3", idxs)
    fence = os.path.join(root, "scripts", "pi-fence.mjs")
    if os.path.isfile(fence):
        report.add("pi fence", OK, "present", idxs)
    else:
        report.add("pi fence", MISSING, "pi-fence.mjs missing from Consort root", idxs)
    report.add("rg", OK if has_tool("rg", env) else MISSING, "ok" if has_tool("rg", env) else "pi backend needs rg", idxs)
    report.add("fd", OK if has_tool("fd", env) else MISSING, "ok" if has_tool("fd", env) else "pi backend needs fd or fdfind", idxs)
    profile = env.get("PI_CODING_AGENT_DIR")
    if profile is not None:
        if profile == "" or not os.path.isdir(profile):
            report.add("PI_CODING_AGENT_DIR", MISSING, "explicit profile is not a directory", idxs)
        else:
            report.add("PI_CODING_AGENT_DIR", OK, "directory present", idxs)
    vertex_legs: List[Leg] = []
    other_google: List[Leg] = []
    anthropic_legs: List[Leg] = []
    for leg in legs:
        provider = effective_pi_provider(env, leg)
        if provider == "anthropic":
            anthropic_legs.append(leg)
        if provider == "google-vertex":
            vertex_legs.append(leg)
        elif provider.startswith("google"):
            other_google.append(leg)
    if anthropic_legs and env.get("CONSORT_PI_SAME_VENDOR_OK") != "1":
        report.add(
            "pi provider anthropic",
            MISSING,
            "same-vendor for a Claude principal; set CONSORT_PI_SAME_VENDOR_OK=1 only if it is not",
            [leg.index for leg in anthropic_legs],
        )
    if vertex_legs:
        check_pi_google_vertex(report, env, cwd, vertex_legs)
    if other_google:
        check_google_star_credentials(report, env, cwd, other_google)
    report.add("pi auth", OPTIONAL, "UNVERIFIED; no auth or model command was sent", idxs)


def reviewer_contract_line(env: Mapping[str, str], defaulting: bool) -> Requirement:
    if "CONSORT_REVIEWERS" in env:
        detail = "process"
    elif defaulting:
        detail = "Consort default codex (unset in process)"
    else:
        detail = "process"
    return Requirement("env CONSORT_REVIEWERS", OK, detail)


def check_reviewers(environment: Mapping[str, str], consort_root: str) -> List[Requirement]:
    env = dict(environment)
    cwd = env.get("PWD") or os.getcwd()
    report = Report()
    present = "CONSORT_REVIEWERS" in env
    defaulting = not present
    diagnose_settings(report, env, defaulting)
    try:
        legs = parse_legs(env.get("CONSORT_REVIEWERS"), present)
    except ConfigError as exc:
        report.add("CONSORT_REVIEWERS", MISSING, exc.message)
        return report.rows
    report.add(
        reviewer_contract_line(env, defaulting).subject,
        OK,
        reviewer_contract_line(env, defaulting).detail,
    )
    if all(leg.backend == "codex" for leg in legs):
        # A legitimate route (still a second vendor to the Claude author), but one reading, not two.
        report.add(
            "reviewer panel",
            OPTIONAL,
            "Codex-only route: one vendor; name it in the team's ADR 0001 and add a second leg when one is reachable",
        )
    root_ok, root_detail = consort_root_ok(consort_root)
    if root_ok:
        report.add("consort checkout", OK, os.path.basename(os.path.abspath(consort_root)))
    else:
        report.add("consort checkout", MISSING, "git clone https://github.com/siimvene/consort and pass --consort-root")
    models: List[str] = []
    if root_ok:
        for leg in legs:
            ok, text = resolve_consort(consort_root, "model", leg_env(env, leg))
            model = effective_model(text, leg.backend) if ok else None
            subject = f"model {leg.spec}"
            if model is None:
                report.add(subject, MISSING, "no nonempty provider/model", (leg.index,))
                models.append("")
            else:
                report.add(subject, OK, model, (leg.index,))
                models.append(f"{leg.backend}|{model}")
        for i, ident in enumerate(models):
            if not ident:
                continue
            for j in range(i):
                if models[j] == ident:
                    report.add(
                        "CONSORT_REVIEWERS",
                        MISSING,
                        f"legs '{legs[j].spec}' and '{legs[i].spec}' resolve to the same reviewer",
                    )
                    break
    by_backend: Dict[str, List[Leg]] = {"codex": [], "gemini": [], "pi": []}
    for leg in legs:
        by_backend[leg.backend].append(leg)
    if root_ok and by_backend["codex"]:
        check_codex(report, env, consort_root, by_backend["codex"])
    if root_ok and by_backend["gemini"]:
        check_gemini(report, env, consort_root, by_backend["gemini"])
    if root_ok and by_backend["pi"]:
        check_pi(report, env, consort_root, cwd, by_backend["pi"])
    needs_gcloud = any(r.subject == "gcloud" and r.state != SKIP for r in report.rows)
    needs_project = any(r.subject == "env CONSORT_GCP_PROJECT" and r.state != SKIP for r in report.rows)
    if not needs_gcloud:
        report.add("gcloud", SKIP, "no Vertex or Gemini ADC/CLI route")
    if not needs_project:
        report.add("env CONSORT_GCP_PROJECT", SKIP, "no Vertex or native Gemini leg")
    report.add(
        "reviewer reachability",
        OPTIONAL,
        "UNVERIFIED; no model request was sent",
    )
    return report.rows


def parse_cli(argv: Sequence[str]) -> Tuple[Optional[str], Optional[str]]:
    consort_root: Optional[str] = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--consort-root":
            if i + 1 >= len(argv):
                return None, "--consort-root needs a path"
            consort_root = argv[i + 1]
            i += 2
            continue
        if arg in ("-h", "--help"):
            return None, "help"
        return None, f"unknown argument: {arg}"
    return consort_root, None


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root, err = parse_cli(args)
    if err == "help":
        print(USAGE)
        return 0
    if err is not None:
        print(f"check-reviewers: {err}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 1
    if root is None:
        root = os.path.join(os.environ.get("HOME", ""), "git", "consort")
    rows = check_reviewers(os.environ, root)
    for row in rows:
        print(format_line(row))
    return 1 if any(r.state == MISSING for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
