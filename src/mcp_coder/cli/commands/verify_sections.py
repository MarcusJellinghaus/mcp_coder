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
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from ...config.toml_utils import MCP_CODER_CONFIG_FILES
from ...mcp_workspace import FILE_ACCESS_SUPPORTED, validate_access_rules
from ...utils.env_placeholders import resolve_placeholders
from ...utils.pyproject_config import get_format_code, has_legacy_format_code_key
from ...utils.verify_render import STATUS_SYMBOLS, Row, SectionBuilder, hint_row
from .verify_project_keys import key_warning_rows
from .verify_setup import setup_rows
from .verify_toolkit_rows import check_type_hints_row, toolkit_rows

_ENVIRONMENT_PACKAGES: tuple[str, ...] = (
    "mcp-coder",
    "mcp-coder-utils",
    "mcp-tools-py",
    "mcp-workspace",
)
# Packages behind an extra: missing is a warning, not an error
_OPTIONAL_PACKAGES: frozenset[str] = frozenset({"mcp-tools-py"})

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
            if pkg in _OPTIONAL_PACKAGES:
                out.add(Row(pkg, STATUS_SYMBOLS["warning"], "not installed (optional)"))
            else:
                out.add(Row(pkg, STATUS_SYMBOLS["failure"], "not installed"))
    out.close()


def _file_access_row(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder
) -> bool:
    """Add the ``.mcp-file-access`` row (indent 2) to *out*.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the row is added to.

    Returns:
        False if the rules file is invalid (row added as [ERR]).
    """
    ok = True
    if not (project_dir / ".mcp-file-access").exists():
        marker, value = symbols["success"], "not present (gitignore defaults)"
    elif not FILE_ACCESS_SUPPORTED:
        # The old-version stand-in for validate_access_rules always returns [].
        marker = symbols["warning"]
        value = (
            "not checked (mcp-workspace in this environment"
            " does not support .mcp-file-access)"
        )
    elif problems := validate_access_rules(project_dir):
        marker, value = symbols["failure"], f"invalid ({'; '.join(problems)})"
        ok = False
    else:
        marker, value = symbols["success"], "valid"
    out.add(Row(".mcp-file-access", marker, value, wrap=True))
    return ok


def _format_code_row(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder, indent: int = 4
) -> bool:
    """Add the ``[tool.mcp-coder] format_code`` row to *out*, naming its source.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the row is added to.
        indent: Indent of the row.

    Returns:
        False if the value is invalid (row added as [ERR]).
    """
    try:
        setting = get_format_code(project_dir)
    except ValueError as exc:
        out.add(Row("format_code", symbols["failure"], str(exc), indent))
        return False
    if setting.source is None:
        value = "enabled (default)"
    else:
        state = "enabled" if setting.enabled else "disabled"
        value = f"{state} ({setting.source})"
    out.add(Row("format_code", symbols["success"], value, indent))
    return True


def _print_project_section(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder
) -> bool:
    """Print the PROJECT section: the project config files, ``.mcp-file-access`` and tool config.

    One flat layout for every repo. Opens and closes the section on *out*.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the section is rendered through.

    Returns:
        False if any row is [ERR]. The ``Project config`` row never fails:
        without a config file the ``Toolkit`` row already reports [ERR].
    """
    out.open("PROJECT")
    found = [n for n in MCP_CODER_CONFIG_FILES if (project_dir / n).is_file()]
    if found:
        out.add(Row("Project config", symbols["success"], ", ".join(found)))
    else:
        out.add(Row("Project config", symbols["warning"], "none"))
    file_access_ok = _file_access_row(project_dir, symbols, out)
    ok = _format_code_row(project_dir, symbols, out, indent=2)
    ok = toolkit_rows(project_dir, symbols, out, indent=2) and ok
    ok = setup_rows(project_dir, symbols, out, indent=2) and ok
    if has_legacy_format_code_key(project_dir):
        out.add(
            Row(
                "legacy format_code",
                symbols["failure"],
                "[tool.mcp-coder.implement] format_code ignored"
                " — use [tool.mcp-coder] format_code",
            )
        )
        ok = False
    ok = check_type_hints_row(project_dir, symbols, out) and ok
    out.add(*key_warning_rows(project_dir, "PROJECT", symbols))
    out.close()
    return ok and file_access_ok


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
        out.add(hint_row(f"-> {hint}"))
