"""Regression-fix prompt rendering for the ``mcp-coder rebase`` workflow.

The "Rebase Regression Fix" prompt's check-tool sentence and shell ban are
filled from the loaded toolkit's ``llm_permissions`` for the active rebase
binding, so a ``command`` project sees its granted commands and a Python
project its MCP check tools — no switch on the toolkit name.
"""

import re
from collections.abc import Sequence
from pathlib import Path

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.toolkit_runner import (
    bash_grants_of,
    get_fragment,
    llm_permissions,
    load_toolkit,
)

_REGRESSION_PROMPT_HEADER = "Rebase Regression Fix"
_REGRESSION_PLACEHOLDERS = re.compile(
    r"\[(check_tools|pytest_marker_filter|regression_output|fix_text|shell_ban)\]"
)


def _marker_filter_text(
    project_dir: Path, automated: bool, permissions: Sequence[str]
) -> str:
    """Return the toolkit's unattended test-filter instruction for the fix prompt.

    ``permissions`` are the fix session's permissions for the
    ``rebase_automated`` binding. When the toolkit declares ``Bash(`` grants
    for it but ``permissions`` has none, the provider dropped them and the
    LLM cannot run the filtered commands, so no instruction is given.

    Returns:
        ``""`` when not automated or when the Bash grants were dropped;
        otherwise the toolkit's ``check_instructions.unattended`` fragment
        (``""`` if it has none).
    """
    if not automated:
        return ""
    if not bash_grants_of(permissions) and bash_grants_of(
        llm_permissions(project_dir, "claude", "rebase_automated")
    ):
        return ""
    return get_fragment(load_toolkit(project_dir), "check_instructions.unattended")


def _check_tool_texts(permissions: Sequence[str]) -> tuple[str, str]:
    """Render the check-tool sentence and the shell ban from the permissions.

    Returns:
        ``(check sentence, shell ban)``; the ban is ``""`` when Bash grants
        are present, else ``"no shell commands of any kind; "``.
    """
    bash = bash_grants_of(permissions)
    mcp = [p for p in permissions if p not in bash]
    parts: list[str] = []
    if mcp:
        tools = ", ".join(f"`{p}`" for p in mcp)
        parts.append(
            f"Before editing anything, re-run the granted MCP check tools ({tools}) "
            "to get the full failure detail."
        )
    if bash:
        commands = ", ".join(f"`{g[len('Bash(') : -1]}`" for g in bash)
        parts.append(
            "Before editing anything, re-run the granted check commands, exactly "
            f"as written: {commands}."
        )
    if not parts:
        parts.append("You cannot re-run the checks; use the output below.")
    ban = "" if bash else "no shell commands of any kind; "
    return " ".join(parts), ban


def _build_regression_fix_prompt(replacements: dict[str, str]) -> str:
    """Build the regression-fix prompt by filling its placeholders.

    ``replacements`` maps placeholder names without brackets (e.g.
    ``"regression_output"``) to their text; a missing name renders as ``""``.
    One pass, so inlined check output is never substituted again.

    Returns:
        The assembled regression-fix prompt string.
    """
    template = get_prompt(str(PROMPTS_FILE_PATH), _REGRESSION_PROMPT_HEADER)
    return _REGRESSION_PLACEHOLDERS.sub(
        lambda match: replacements.get(match.group(1), ""), template
    )
