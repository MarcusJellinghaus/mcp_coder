"""Setup row of the verify command's PROJECT section.

Loads ``[tool.mcp-coder.setup]`` strictly and resolves every step's
``argv[0]``; no step is run. Steps after the ``python`` built-in are looked up
venv-first. While the project has no venv interpreter yet, an unresolvable
``argv[0]`` there is only a warning: the built-in may install it.
"""

from pathlib import Path

from ...utils.executable import resolve_executable, venv_python, venv_search_path
from ...utils.setup_config import load_setup_config
from .verify_formatting import Row
from .verify_render import SectionBuilder

# Problem status mapped to the symbols-dict key it prints with
_STATUS_SYMBOL: dict[str, str] = {
    "ok": "success",
    "warning": "warning",
    "error": "failure",
}


def setup_rows(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4
) -> bool:
    """Add the Setup row and one sub-row per unresolvable ``argv[0]``.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the rows are added to.
        indent: Number of leading spaces of the Setup row.

    Returns:
        False if the config is invalid or any added row is an error.
    """
    try:
        config = load_setup_config(project_dir)
    except ValueError as exc:
        out.add(Row("Setup", symbols["failure"], str(exc), indent))
        return False

    has_venv = venv_python(project_dir / ".venv") is not None
    after_python = False
    problems: list[tuple[str, str]] = []
    for step in config.steps:
        if step.argv is None:
            after_python = after_python or step.builtin == "python"
            continue
        path = venv_search_path(project_dir) if after_python else None
        if resolve_executable(step.argv[0], project_dir, path=path) is None:
            status = "warning" if after_python and not has_venv else "error"
            problems.append((status, f"{step.label}: {step.argv[0]!r} not found"))

    statuses = {status for status, _ in problems}
    worst = next((s for s in ("error", "warning") if s in statuses), "ok")
    if not config.steps:
        summary = "nothing to do"
    elif config.source is None:
        summary = "default: python built-in"
    else:
        summary = f"{len(config.steps)} step(s) from {config.source}"
    out.add(Row("Setup", symbols[_STATUS_SYMBOL[worst]], summary, indent))
    for status, message in problems:
        out.add(Row("", symbols[_STATUS_SYMBOL[status]], message, indent + 2))
    return "error" not in statuses
