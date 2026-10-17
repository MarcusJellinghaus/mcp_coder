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
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, cast

import yaml

from ...mcp_workspace_github import CheckResult, verify_github_security
from ...utils.pyproject_config import get_implement_config
from .verify_formatting import (
    _VALUE_COLUMN_INDENT,
    STATUS_SYMBOLS,
    _format_row,
    _format_section,
    _pad,
)

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
) -> tuple[bool | None, str, list[tuple[str, str]]]:
    """Validate ``.mcp.json`` and collect ``${...}`` placeholder findings in one parse.

    Args:
        mcp_json_path: Path to ``.mcp.json``.

    Returns:
        ``(ok, message, warnings)`` where:
          - ``ok=True``  -> well-formed, non-empty ``mcpServers``.
          - ``ok=None``  -> WARN: parseable but ``mcpServers`` is empty (``{}``).
          - ``ok=False`` -> hard fail: unparseable JSON, top-level JSON not an
            object, or ``mcpServers`` missing / not an object.
          - ``message``  -> human-readable status for the validity row.
          - ``warnings`` -> list of ``(f"{server} / {env_var}", value)`` pairs
            for unresolved ``${...}`` templates (always ``[]`` on hard fail).
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
    warnings: list[tuple[str, str]] = [
        (f"{name} / {var}", val)
        for name, srv in servers.items()
        if isinstance(srv, dict)
        for var, val in srv.get("env", {}).items()
        if isinstance(val, str) and re.search(r"\$\{[^}]+\}", val)
    ]
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


def _derive_code_scanning_alerts(codeql_result: CheckResult) -> CheckResult:
    """Derive the Code scanning alerts row from CodeQL presence only (no real counts).

    Args:
        codeql_result: The ``_check_codeql_workflow`` result.

    Returns:
        A ``CheckResult``-shaped dict with ``ok=None`` always — it reflects
        whether CodeQL is configured, never a verified alert count. Always
        ``severity="warning"``.
    """
    # CheckResult.ok is typed as bool upstream, but this row is always
    # unverified (ok=None) per the tri-state convention — cast past the
    # mismatch rather than widening the shared upstream type.
    if codeql_result["ok"] is True:
        return cast(
            CheckResult,
            {
                "ok": None,
                "value": "configured (alert counts not checked)",
                "severity": "warning",
            },
        )
    return cast(
        CheckResult,
        {
            "ok": None,
            "value": "not configured (no CodeQL workflow)",
            "severity": "warning",
        },
    )


def _print_github_security_section(project_dir: Path, symbols: dict[str, str]) -> None:
    """Merge local-file and API-backed security rows, print GITHUB SECURITY.

    Calls `_check_codeql_workflow` once and reuses the result for both the
    `codeql_workflow` row and the `_derive_code_scanning_alerts` input.
    """
    security_api_result = verify_github_security(project_dir)
    codeql_result = _check_codeql_workflow(project_dir)
    github_security_result: dict[str, Any] = {
        "dependabot_config": _check_dependabot_config(project_dir),
        "dependabot_alerts": security_api_result["dependabot_alerts"],
        "dependabot_security_updates": security_api_result[
            "dependabot_security_updates"
        ],
        "secret_scanning": security_api_result["secret_scanning"],
        "secret_scanning_push_protection": security_api_result[
            "secret_scanning_push_protection"
        ],
        "codeql_workflow": codeql_result,
        "code_scanning_alerts": _derive_code_scanning_alerts(codeql_result),
    }
    print(_format_section("GITHUB SECURITY", github_security_result, symbols))


def _print_environment_section() -> None:
    """Print the ENVIRONMENT section (Python info, TLS/proxy, 4 package versions).

    Uses ``sys``, ``os.environ``, ``importlib.metadata``. Writes directly to
    stdout via ``print`` to match the style of inline sections in
    ``execute_verify``.
    """
    # Lazy, like the test-prompt failure branch in verify.py: _exceptions keeps
    # its httpx / openai / anthropic / google.genai imports behind try/except
    # ImportError, so this is safe without the langchain extras installed.
    from ...llm.providers.langchain._exceptions import (  # pylint: disable=import-outside-toplevel
        _proxy_configured,
        _truststore_available,
    )

    print(_pad("ENVIRONMENT"))
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    print(_format_row("Python version", "", python_version, indent=2))
    print(_format_row("Executable", "", sys.executable, indent=2))
    virtualenv = sys.prefix if sys.prefix != sys.base_prefix else "(none)"
    print(_format_row("Virtualenv", "", virtualenv, indent=2))
    pythonpath = os.environ.get("PYTHONPATH") or "(not set)"
    print(_format_row("PYTHONPATH", "", pythonpath, indent=2))
    # _truststore_available() is exactly what create_ssl_context branches on,
    # so the source reported here is the one the HTTP client will really use.
    ssl_source = (
        "truststore (OS certificate store)"
        if _truststore_available()
        else "default (certifi/system)"
    )
    # Boolean only: the proxy URL may embed credentials.
    proxy = "configured (HTTPS_PROXY/HTTP_PROXY)" if _proxy_configured() else "none"
    print(
        _format_row(
            "TLS / proxy", "", f"SSL context: {ssl_source}; proxy: {proxy}", indent=2
        )
    )
    print()
    for pkg in _ENVIRONMENT_PACKAGES:
        try:
            value = version(pkg)
            print(_format_row(pkg, "", value, indent=2))
        except PackageNotFoundError:
            print(
                _format_row(pkg, STATUS_SYMBOLS["failure"], "not installed", indent=2)
            )


def _print_project_section(project_dir: Path, symbols: dict[str, str]) -> None:
    """Print the PROJECT section showing language detection and tool config.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
    """
    print(_pad("PROJECT"))
    pyproject_exists = (project_dir / "pyproject.toml").exists()
    if pyproject_exists:
        print(_format_row("pyproject.toml", symbols["success"], "found", indent=2))
        print(
            _format_row("Language", symbols["success"], "Python (detected)", indent=2)
        )
        config = get_implement_config(project_dir)
        print()
        print("  [Python]")
        if config.format_code:
            print(_format_row("format_code", symbols["success"], "enabled", indent=4))
        else:
            print(
                _format_row(
                    "format_code",
                    symbols["warning"],
                    "not configured (default: disabled)",
                    indent=4,
                )
            )
        if config.check_type_hints:
            print(
                _format_row("check_type_hints", symbols["success"], "enabled", indent=4)
            )
        else:
            print(
                _format_row(
                    "check_type_hints",
                    symbols["warning"],
                    "not configured (default: disabled)",
                    indent=4,
                )
            )
    else:
        print(_format_row("pyproject.toml", symbols["warning"], "not found", indent=2))
        print(_format_row("Language", symbols["success"], "(none detected)", indent=2))


def _prompt_source(configured: str | None, default_label: str) -> str:
    """Format a prompt source for display.

    Args:
        configured: Configured prompt path, or None if not set.
        default_label: Label shown in parentheses when ``configured`` is None.

    Returns:
        The configured path, or the default_label in parentheses.
    """
    return configured if configured else f"({default_label})"


def _print_retired_env_var_warning(symbols: dict[str, str]) -> None:
    """Warn (exit-neutral) when a retired MCP_CODER_* env var is still exported.

    Called unconditionally — outside both provider gates — because a retired
    variable is equally ignored whatever the active provider is. Builds no
    result dict, so it can never affect the exit code.

    Args:
        symbols: Status-symbol map (e.g. ``STATUS_SYMBOLS``) supplying the
            ``"warning"`` marker for the emitted rows.
    """
    for old, new in _RETIRED_ENV_VARS.items():
        if not os.environ.get(old):
            continue
        print(
            _format_row(
                old,
                symbols["warning"],
                f"retired env var is set and ignored — use {new}",
                indent=2,
                label_width=len(old),
            )
        )


def _print_langchain_readiness_warning(symbols: dict[str, str]) -> None:
    """Warn (exit-neutral) when the configured langchain backend module is missing.

    Runs for non-langchain providers only — its single call site is the
    else-branch of the langchain gate in ``execute_verify``, where
    ``verify_langchain`` would otherwise report nothing. Prints nothing when
    langchain is not configured, or when a known backend's module is
    installed. Builds no result dict — it only prints, so it can never affect
    the exit code.

    Args:
        symbols: Status-symbol map (e.g. ``STATUS_SYMBOLS``) supplying the
            ``"warning"`` marker for the emitted row.
    """
    from ...llm.providers.langchain import _load_langchain_config
    from ...llm.providers.langchain.verification import (
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
    print(_format_row("Langchain backend", symbols["warning"], msg, indent=2))
    if hint:
        print(f"{' ' * _VALUE_COLUMN_INDENT}-> {hint}")
