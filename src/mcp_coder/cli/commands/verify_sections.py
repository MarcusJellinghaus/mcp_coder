"""Section printers and lookup tables for the verify command.

Everything ``execute_verify`` delegates a whole printed section (or a
standalone advisory row) to lives here, together with the constant tables
those printers are driven by. Same one-directional shape as
``verify_formatting`` / ``verify_exit_code``: nothing here reaches back into
``verify.py``.
"""

import json
import logging
import os
import sys
from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import yaml

from ...mcp_tools_py import resolve_steps
from ...mcp_workspace_github import CheckResult, verify_github_security
from ...utils.env_placeholders import resolve_placeholders
from ...utils.pyproject_config import (
    get_format_code,
    get_implement_config,
    has_legacy_format_code_key,
)
from ...utils.toolkit_runner import (
    DEFAULT_TOOLKIT,
    load_toolkit,
    load_toolkit_config,
    verify_toolkit,
)
from .verify_formatting import (
    STATUS_SYMBOLS,
    Row,
    _format_section,
    _hint,
)
from .verify_render import SectionBuilder
from .verify_setup import setup_rows

_ENVIRONMENT_PACKAGES: tuple[str, ...] = (
    "mcp-coder",
    "mcp-coder-utils",
    "mcp-tools-py",
    "mcp-workspace",
)

# Retired MCP_CODER_* environment variables mapped to their replacement.
# Unknown-key detection scans config *sections*, so a still-exported retired
# variable produces no signal anywhere else. Add a row here whenever a
# variable stops being read.
_RETIRED_ENV_VARS: dict[str, str] = {
    "MCP_CODER_LLM_LANGCHAIN_ENDPOINT": "MCP_CODER_LLM_LANGCHAIN_BASE_URL",
}

# Provider-selection env var, and the exact ``source`` string resolve_llm_method
# reports when it is the one that won.
_PROVIDER_ENV_VAR: str = "MCP_CODER_LLM_PROVIDER"
_PROVIDER_ENV_SOURCE: str = f"env {_PROVIDER_ENV_VAR}"

_CODEQL_ACTION_PREFIX = "github/codeql-action"


class _DropUnexpandedWarnings(logging.Filter):
    """Scoped filter that drops langchain-mcp-adapters unresolved-var warnings."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "unexpanded variable" not in record.getMessage()


def _validate_mcp_config(
    mcp_json_path: str,
    env_vars: dict[str, str] | None = None,
) -> tuple[bool | None, str, list[tuple[str, str]]]:
    """Validate ``.mcp.json`` and collect unresolved ``env`` placeholders in one parse.

    Args:
        mcp_json_path: Path to ``.mcp.json``.
        env_vars: Extra variables used to resolve placeholders; they take
            precedence over ``os.environ``.

    Returns:
        ``(ok, message, warnings)`` where:
          - ``ok=True``  -> well-formed, non-empty ``mcpServers``.
          - ``ok=None``  -> WARN: parseable but ``mcpServers`` is empty (``{}``).
          - ``ok=False`` -> hard fail: unparseable JSON, top-level JSON not an
            object, or ``mcpServers`` missing / not an object.
          - ``message``  -> human-readable status for the validity row.
          - ``warnings`` -> list of ``(f"{server} / {env_var}", "${A}, ${B} not set")``
            pairs for placeholders unresolved via ``os.environ`` and
            ``env_vars``; a ``${VAR:-default}`` counts as resolved. A server
            whose ``env`` is not an object is skipped. Always ``[]`` on hard
            fail.
    """
    try:
        data = json.loads(Path(mcp_json_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (False, f"invalid JSON ({exc})", [])
    # A valid JSON document whose top level is NOT an object (e.g. [], "foo",
    # 42) would make data.get(...) raise AttributeError, which is not caught
    # above and would crash execute_verify. Hard-fail here before calling .get.
    if not isinstance(data, dict):
        return (False, "mcpServers missing or not an object", [])
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return (False, "mcpServers missing or not an object", [])
    warnings: list[tuple[str, str]] = []
    for name, srv in servers.items():
        env = srv.get("env") if isinstance(srv, dict) else None
        if not isinstance(env, dict):
            continue
        for var, val in env.items():
            if isinstance(val, str) and (
                missing := resolve_placeholders(val, env_vars)[1]
            ):
                warnings.append(
                    (
                        f"{name} / {var}",
                        ", ".join(f"${{{m}}}" for m in missing) + " not set",
                    )
                )
    if not servers:
        return (None, "config present but no servers defined", warnings)
    return (True, "well-formed", warnings)


def _schedule_interval(entry: dict[str, Any]) -> Any:
    """Return a dependabot entry's ``schedule.interval``, or ``"?"`` if absent."""
    schedule = entry.get("schedule")
    if isinstance(schedule, dict):
        return schedule.get("interval", "?")
    return "?"


def _workflow_uses_codeql(path: Path) -> bool:
    """Return True if any job step in the workflow uses github/codeql-action.

    Unreadable, unparseable, or oddly shaped files count as False.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return False
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, dict):
        return False
    for job in jobs.values():
        steps = job.get("steps") if isinstance(job, dict) else None
        if not isinstance(steps, list):
            continue
        for step in steps:
            uses = step.get("uses") if isinstance(step, dict) else None
            if isinstance(uses, str) and uses.startswith(_CODEQL_ACTION_PREFIX):
                return True
    return False


def _check_dependabot_config(project_dir: Path) -> CheckResult:
    """Check .github/dependabot.yml (or .yaml) for configured ecosystems and schedules.

    Args:
        project_dir: Path to the project directory.

    Returns:
        ``CheckResult`` with ``ok=True`` when at least one ecosystem is
        configured, ``ok=False`` otherwise (missing file, invalid YAML, or no
        ecosystems). Always uses warning severity — this section is
        exit-neutral regardless of what any row reports.
    """
    path = next(
        (
            p
            for p in (
                project_dir / ".github" / "dependabot.yml",
                project_dir / ".github" / "dependabot.yaml",
            )
            if p.exists()
        ),
        None,
    )
    if path is None:
        return CheckResult(ok=False, value="not present", severity="warning")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return CheckResult(ok=False, value=f"invalid YAML ({exc})", severity="warning")
    except (OSError, UnicodeDecodeError):
        return CheckResult(ok=False, value="unreadable", severity="warning")
    updates = data.get("updates") if isinstance(data, dict) else None
    if not isinstance(updates, list) or not updates:
        return CheckResult(
            ok=False, value="no ecosystems configured", severity="warning"
        )
    pairs = [
        (
            entry.get("package-ecosystem", "?"),
            _schedule_interval(entry),
        )
        for entry in updates
        if isinstance(entry, dict)
    ]
    if not pairs:
        return CheckResult(
            ok=False, value="no ecosystems configured", severity="warning"
        )
    intervals = {interval for _, interval in pairs}
    if len(intervals) == 1:
        ecosystems = ", ".join(eco for eco, _ in pairs)
        value = f".github/{path.name} ({ecosystems}: {intervals.pop()})"
    else:
        parts = ", ".join(f"{eco}: {interval}" for eco, interval in pairs)
        value = f".github/{path.name} ({parts})"
    return CheckResult(ok=True, value=value, severity="warning")


def _check_codeql_workflow(project_dir: Path) -> CheckResult:
    """Scan .github/workflows/*.yml|*.yaml for a step using github/codeql-action.

    Args:
        project_dir: Path to the project directory.

    Returns:
        ``CheckResult`` with ``ok=True`` when a workflow step's ``uses:``
        value references ``github/codeql-action``, ``ok=False`` otherwise.
        Detection is content-based, not filename-based. Always
        ``severity="warning"``.
    """
    workflows_dir = project_dir / ".github" / "workflows"
    if workflows_dir.is_dir():
        filenames = sorted(
            p.name for p in workflows_dir.iterdir() if p.suffix in (".yml", ".yaml")
        )
        for filename in filenames:
            if _workflow_uses_codeql(workflows_dir / filename):
                return CheckResult(
                    ok=True, value=f"found in {filename}", severity="warning"
                )
    return CheckResult(
        ok=False,
        value="no workflow step uses github/codeql-action",
        severity="warning",
    )


_NOT_ACCESSIBLE: dict[str, Any] = {
    "ok": None,
    "value": "not accessible",
    "severity": "warning",
}


# Known false positive, accepted: the mcp-workspace probe returns normally on a
# 3xx redirect, so it is reported like a 200 ("scope present").
def _map_security_row(key: str, row: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map one probe result to its GITHUB SECURITY row (pass-through + 4 rules).

    Rules: a missing row becomes ``ok=None`` / ``"not accessible"``; an
    ``ok=None`` ``"not checked"`` value reads ``"not accessible"``; the code
    scanning 404 (``"scope missing or not configured"``) is demoted from
    ``ok=False`` to ``ok=None``; an ``ok=None`` row with an ``error`` gets it
    appended to the value. Anything else passes through unchanged.

    Args:
        key: Probe result key (e.g. ``"code_scanning_alerts"``).
        row: The probe's result for ``key``, or None if the key is absent.

    Returns:
        A plain dict with ``ok``, ``value``, ``severity`` and optionally ``error``.
    """
    entry = dict(row) if row is not None else dict(_NOT_ACCESSIBLE)
    if entry["ok"] is None and entry["value"] == "not checked":
        entry["value"] = "not accessible"
    if (
        key == "code_scanning_alerts"
        and entry["ok"] is False
        and entry["value"] == "scope missing or not configured"
    ):
        entry["ok"] = None
    if entry["ok"] is None and entry.get("error"):
        entry["value"] = f"{entry['value']} ({entry['error']})"
    return entry


def _print_github_security_section(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder
) -> None:
    """Merge local-file and API-backed security rows, print GITHUB SECURITY.

    The five API-backed rows come from ``verify_github_security``, each
    mapped through ``_map_security_row``.
    """
    api = verify_github_security(project_dir)
    github_security_result: dict[str, Any] = {
        "dependabot_config": _check_dependabot_config(project_dir),
        "dependabot_alerts": _map_security_row(
            "dependabot_alerts", api.get("dependabot_alerts")
        ),
        "dependabot_security_updates": _map_security_row(
            "dependabot_security_updates", api.get("dependabot_security_updates")
        ),
        "secret_scanning": _map_security_row(
            "secret_scanning", api.get("secret_scanning")
        ),
        "secret_scanning_push_protection": _map_security_row(
            "secret_scanning_push_protection",
            api.get("secret_scanning_push_protection"),
        ),
        "codeql_workflow": _check_codeql_workflow(project_dir),
        "code_scanning_alerts": _map_security_row(
            "code_scanning_alerts", api.get("code_scanning_alerts")
        ),
    }
    out.section("GITHUB SECURITY", _format_section(github_security_result, symbols))


def _print_environment_section(out: SectionBuilder) -> None:
    """Print the ENVIRONMENT section (Python info, TLS/proxy, 4 package versions).

    Uses ``sys``, ``os.environ``, ``importlib.metadata``. Opens and closes the
    section on *out*.
    """
    # Lazy, like the test-prompt failure branch in verify.py: _exceptions keeps
    # its httpx / openai / anthropic / google.genai imports behind try/except
    # ImportError, so this is safe without the langchain extras installed.
    from ...llm.providers.langchain._exceptions import (  # pylint: disable=import-outside-toplevel
        _proxy_configured,
        _truststore_available,
    )

    out.open("ENVIRONMENT")
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    out.add(Row("Python version", "", python_version))
    out.add(Row("Executable", "", sys.executable))
    virtualenv = sys.prefix if sys.prefix != sys.base_prefix else "(none)"
    out.add(Row("Virtualenv", "", virtualenv))
    pythonpath = os.environ.get("PYTHONPATH") or "(not set)"
    out.add(Row("PYTHONPATH", "", pythonpath))
    # _truststore_available() is exactly what create_ssl_context branches on,
    # so the source reported here is the one the HTTP client will really use.
    ssl_source = (
        "truststore (OS certificate store)"
        if _truststore_available()
        else "default (certifi/system)"
    )
    # Boolean only: the proxy URL may embed credentials.
    proxy = "configured (HTTPS_PROXY/HTTP_PROXY)" if _proxy_configured() else "none"
    out.add(Row("TLS / proxy", "", f"SSL context: {ssl_source}; proxy: {proxy}"))
    out.add("")
    for pkg in _ENVIRONMENT_PACKAGES:
        try:
            value = version(pkg)
            out.add(Row(pkg, "", value))
        except PackageNotFoundError:
            out.add(Row(pkg, STATUS_SYMBOLS["failure"], "not installed"))
    out.close()


def _format_code_row(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder
) -> bool:
    """Add the ``[tool.mcp-coder] format_code`` row to *out*.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the row is added to.

    Returns:
        False if the value is invalid (row added as [ERR]).
    """
    try:
        setting = get_format_code(project_dir)
    except ValueError as exc:
        out.add(Row("format_code", symbols["failure"], str(exc), 4))
        return False
    if not setting.enabled:
        value = "disabled"
    elif setting.explicit:
        value = "enabled"
    else:
        value = "enabled (default)"
    out.add(Row("format_code", symbols["success"], value, 4))
    return True


def _formatter_row(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4
) -> bool:
    """Add the Formatter row with the steps mcp-tools-py resolves to *out*.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the row is added to.
        indent: Number of leading spaces.

    Returns:
        False if no formatter can be resolved (row added as [ERR]).
    """
    try:
        steps = resolve_steps(project_dir)
    except ValueError as exc:
        out.add(Row("Formatter", symbols["failure"], str(exc), indent))
        return False
    out.add(Row("Formatter", symbols["success"], " → ".join(steps), indent))
    return True


# VerifyItem.status mapped to the symbols-dict key it prints with
_VERIFY_STATUS_SYMBOL: dict[str, str] = {
    "ok": "success",
    "warning": "warning",
    "error": "failure",
}


def _uses_mcp_tools_py(project_dir: Path) -> bool:
    """Return True if the project's toolkit is mcp-tools-py.

    An invalid config counts as False: the Toolkit row already reports it.
    """
    try:
        return load_toolkit_config(project_dir).toolkit == DEFAULT_TOOLKIT
    except ValueError:
        return False


def _formatting_enabled(project_dir: Path) -> bool:
    """Return ``format_code``; an invalid value counts as enabled.

    The format_code row already reports the invalid value.
    """
    try:
        return get_format_code(project_dir).enabled
    except ValueError:
        return True


def _toolkit_rows(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4
) -> bool:
    """Add the Toolkit row and one row per toolkit verify item for ``format``.

    The ``format`` items are only checked when formatting is on and the
    ``commit`` binding is non-empty. The toolkit's ``formatter`` item is
    skipped: the Formatter row covers it.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the rows are added to.
        indent: Number of leading spaces of the Toolkit row.

    Returns:
        False if the toolkit fails to load or verify, or any added item is
        an error.
    """
    try:
        loaded = load_toolkit(project_dir)
        items = (
            verify_toolkit(loaded, project_dir, "format")
            if _formatting_enabled(project_dir) and loaded.config.bindings["commit"]
            else []
        )
    except ValueError as exc:
        out.add(Row("Toolkit", symbols["failure"], str(exc), indent))
        return False
    out.add(Row("Toolkit", symbols["success"], loaded.name, indent))
    shown = [item for item in items if item.name != "formatter"]
    for item in shown:
        out.add(
            Row(
                item.name,
                symbols[_VERIFY_STATUS_SYMBOL[item.status]],
                item.message or item.status,
                indent + 2,
            )
        )
    return all(item.status != "error" for item in shown)


def _print_project_section(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder
) -> bool:
    """Print the PROJECT section showing language detection and tool config.

    Opens and closes the section on *out*.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the section is rendered through.

    Returns:
        False if any row is [ERR].
    """
    out.open("PROJECT")
    pyproject_exists = (project_dir / "pyproject.toml").exists()
    if not pyproject_exists:
        out.add(Row("pyproject.toml", symbols["warning"], "not found"))
        out.add(Row("Language", symbols["success"], "(none detected)"))
        ok = not _uses_mcp_tools_py(project_dir) or _formatter_row(
            project_dir, symbols, out, indent=2
        )
        ok = _toolkit_rows(project_dir, symbols, out, indent=2) and ok
        ok = setup_rows(project_dir, symbols, out, indent=2) and ok
        out.close()
        return ok
    out.add(Row("pyproject.toml", symbols["success"], "found"))
    out.add(Row("Language", symbols["success"], "Python (detected)"))
    out.add("")
    out.add("  [Python]")
    ok = _format_code_row(project_dir, symbols, out)
    if _uses_mcp_tools_py(project_dir):
        ok = _formatter_row(project_dir, symbols, out) and ok
    ok = _toolkit_rows(project_dir, symbols, out) and ok
    ok = setup_rows(project_dir, symbols, out) and ok
    if has_legacy_format_code_key(project_dir):
        out.add(
            Row(
                "legacy format_code",
                symbols["failure"],
                "[tool.mcp-coder.implement] format_code ignored"
                " — use [tool.mcp-coder] format_code",
                4,
            )
        )
        ok = False
    config = get_implement_config(project_dir)
    if config.check_type_hints:
        out.add(Row("check_type_hints", symbols["success"], "enabled", 4))
    else:
        out.add(
            Row(
                "check_type_hints",
                symbols["warning"],
                "disabled (set in pyproject.toml)",
                4,
            )
        )
    out.close()
    return ok


def _prompt_source(configured: str | None, default_label: str) -> str:
    """Format a prompt source for display.

    Args:
        configured: Configured prompt path, or None if not set.
        default_label: Label shown in parentheses when ``configured`` is None.

    Returns:
        The configured path, or the default_label in parentheses.
    """
    return configured if configured else f"({default_label})"


def _print_retired_env_var_warning(
    symbols: dict[str, str], out: SectionBuilder
) -> None:
    """Warn (exit-neutral) when a retired MCP_CODER_* env var is still exported.

    Called unconditionally — outside both provider gates — because a retired
    variable is equally ignored whatever the active provider is. Builds no
    result dict, so it can never affect the exit code.

    Args:
        symbols: Status-symbol map (e.g. ``STATUS_SYMBOLS``) supplying the
            ``"warning"`` marker for the emitted rows.
        out: Builder the rows are added to; the section widens to fit them.
    """
    for old, new in _RETIRED_ENV_VARS.items():
        if not os.environ.get(old):
            continue
        out.add(
            Row(
                old,
                symbols["warning"],
                f"retired env var is set and ignored — use {new}",
            )
        )


def _print_langchain_readiness_warning(
    symbols: dict[str, str], out: SectionBuilder
) -> None:
    """Warn (exit-neutral) when the configured langchain backend module is missing.

    Runs for non-langchain providers only — its single call site is the
    else-branch of the langchain gate in ``execute_verify``, where
    ``verify_langchain`` would otherwise report nothing. Prints nothing when
    langchain is not configured, or when a known backend's module is
    installed. Builds no result dict — it only adds rows, so it can never
    affect the exit code.

    Args:
        symbols: Status-symbol map (e.g. ``STATUS_SYMBOLS``) supplying the
            ``"warning"`` marker for the emitted row.
        out: Builder the row and its hint are added to.
    """
    from ...llm.providers.langchain import _load_langchain_config
    from ...llm.providers.langchain._provider_checks import (
        _BACKEND_PACKAGES,
        _check_package_installed,
    )

    backend = _load_langchain_config().get("backend")
    if not backend:
        return  # not configured → note only
    pkg = _BACKEND_PACKAGES.get(backend)
    hint: str | None
    if pkg is None:  # unrecognized backend name
        msg = f"backend '{backend}' is not a recognized langchain backend"
        hint = None
    elif _check_package_installed(pkg):
        return  # installed → emit nothing new
    else:  # known backend, module missing
        display = pkg.replace("_", "-")
        msg = f"backend '{backend}' configured but {display} not installed"
        hint = f"pip install {display} (needed for --llm-method langchain)"
    out.add(Row("Langchain backend", symbols["warning"], msg))
    if hint:
        out.add(_hint(f"-> {hint}"))
