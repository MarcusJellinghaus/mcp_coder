"""Unknown, retired, misplaced and conflicting [tool.mcp-coder] keys for verify.

Scans every file in ``MCP_CODER_CONFIG_FILES`` and reports keys the readers
ignore. The rows are warnings only: they never feed ``ok`` / ``prompts_ok``,
so ``verify``'s exit code does not change.
"""

from pathlib import Path
from typing import Any, NamedTuple

from ...config.toml_utils import MCP_CODER_CONFIG_FILES, TomlReadError, load_toml
from ...utils.config_hints import unknown_key_hint
from .verify_formatting import Row

_TOP = "tool.mcp-coder"
# Settings read from either file; defining one in both files gives the default
_SETTINGS = ("format_code", "labels-config", "prompts")
_PYTHON_ONLY = frozenset({"install", "install-from-github"})
# Legacy implement keys that have their own PROJECT rows
_LEGACY_IMPLEMENT_KEYS = frozenset({"format_code", "check_type_hints"})
# key -> known inner keys; None = scalar, or validated elsewhere (toolkit, setup)
_SCHEMA: dict[str, frozenset[str] | None] = {
    "format_code": None,
    "labels-config": None,
    "toolkit": None,
    "setup": None,
    "prompts": frozenset(
        {"system-prompt", "project-prompt", "claude-system-prompt-mode"}
    ),
    "install": frozenset({"extras", "post_install_checks"}),
    "install-from-github": frozenset({"packages", "packages-no-deps"}),
}
_UNPARSEABLE = (
    "cannot be parsed; format_code, labels-config and prompts use their defaults"
)


class KeyWarning(NamedTuple):
    """One warning about a [tool.mcp-coder] key."""

    section: str  # "PROMPTS" or "PROJECT"
    file: str  # row label, e.g. "mcp-coder.toml"
    message: str


def _with_hint(message: str, section: str, key: str, known: list[str]) -> str:
    """Return *message*, with a near-miss hint appended when there is one."""
    hint = unknown_key_hint(section, key, known)
    return f"{message} — {hint}" if hint else message


def _classify(file_name: str, key: str, value: Any) -> list[KeyWarning]:
    """Return the warnings for one key of [tool.mcp-coder] in *file_name*."""
    if key == "implement":
        if file_name != "pyproject.toml":
            return [
                KeyWarning(
                    "PROJECT", file_name, f"[{_TOP}.implement] is retired and ignored"
                )
            ]
        if not isinstance(value, dict):
            return []
        return [
            KeyWarning(
                "PROJECT", file_name, f"[{_TOP}.implement] {k} is retired and ignored"
            )
            for k in value
            if k not in _LEGACY_IMPLEMENT_KEYS
        ]
    if key in _PYTHON_ONLY and file_name != "pyproject.toml":
        return [
            KeyWarning(
                "PROJECT",
                file_name,
                f"[{_TOP}.{key}] is Python-only; ignored in {file_name}",
            )
        ]
    if key not in _SCHEMA:
        message = _with_hint(
            f"unknown key [{_TOP}] {key}", _TOP, key, [*_SCHEMA, "implement"]
        )
        return [KeyWarning("PROJECT", file_name, message)]
    known = _SCHEMA[key]
    if known is None or not isinstance(value, dict):
        return []
    section = "PROMPTS" if key == "prompts" else "PROJECT"
    return [
        KeyWarning(
            section,
            file_name,
            _with_hint(
                f"unknown key [{_TOP}.{key}] {k}", f"{_TOP}.{key}", k, sorted(known)
            ),
        )
        for k in value
        if k not in known
    ]


def scan_project_keys(project_dir: Path) -> list[KeyWarning]:
    """Scan the [tool.mcp-coder] tables of every project config file.

    Args:
        project_dir: Project root containing pyproject.toml / mcp-coder.toml.

    Returns:
        Warnings in file order, then one per setting defined in both files.
    """
    warnings: list[KeyWarning] = []
    defined: dict[str, list[str]] = {}
    for file_name in MCP_CODER_CONFIG_FILES:
        try:
            data = load_toml(project_dir / file_name, strict=True)
        except TomlReadError:
            warnings.append(KeyWarning("PROJECT", file_name, _UNPARSEABLE))
            continue
        tool: Any = data.get("tool", {})
        table = tool.get("mcp-coder", {}) if isinstance(tool, dict) else None
        if not isinstance(table, dict):
            warnings.append(KeyWarning("PROJECT", file_name, _UNPARSEABLE))
            continue
        for key, value in table.items():
            warnings.extend(_classify(file_name, key, value))
            if key in _SETTINGS:
                defined.setdefault(key, []).append(file_name)
    for setting, files in defined.items():
        if len(files) == len(MCP_CODER_CONFIG_FILES):
            warnings.append(
                KeyWarning(
                    "PROMPTS" if setting == "prompts" else "PROJECT",
                    "mcp-coder.toml",
                    f"[{_TOP}] {setting} is defined in both"
                    f" {' and '.join(MCP_CODER_CONFIG_FILES)}; default used",
                )
            )
    return warnings


def key_warning_rows(
    project_dir: Path, section: str, symbols: dict[str, str], indent: int = 2
) -> list[Row]:
    """Return the [WARN] rows of one verify section.

    Args:
        project_dir: Project root containing pyproject.toml / mcp-coder.toml.
        section: Verify section, "PROMPTS" or "PROJECT".
        symbols: Dict with 'success', 'failure', 'warning' keys.
        indent: Indent of the rows.

    Returns:
        One wrapped row per warning of *section*, labelled with its file.
    """
    return [
        Row(w.file, symbols["warning"], w.message, indent, wrap=True)
        for w in scan_project_keys(project_dir)
        if w.section == section
    ]
