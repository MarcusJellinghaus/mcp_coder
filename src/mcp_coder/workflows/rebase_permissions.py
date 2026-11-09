"""Least-privilege Claude Code settings for the automated rebase session.

``REBASE_LLM_PERMISSIONS`` holds exactly the tools the automated rebase LLM
session needs: the MCP check/file tools and the read-only git tool from
``.claude/skills/rebase/SKILL.md`` (``allowed-tools``), converted to the
``settings.local.json`` permission-string format.

Deliberately narrower than SKILL.md:
- **no ``Bash(...)`` grants in this dict** — regression-fix turns get the
  toolkit's exact ``Bash(...)`` grants via ``--allowedTools``
  (``llm_permissions``), which also applies when a ``--settings`` override
  replaces this dict; conflict turns get none. All git writes are performed by
  the surrounding Python program; the LLM reads git state via
  ``mcp__mcp-workspace__git`` only. ``REBASE_LLM_PERMISSIONS`` itself is
  unchanged (#1197).
- **no ``push``** — Python performs the final ``--force-with-lease`` push, so the
  LLM never needs a push grant (see summary.md, "Python executes the force-push").
- **no ``uv lock``** — lockfile handling is out of scope for this repo (no tracked
  lockfile exists).
- **no reference-project tools** — the rebase session works on this repo only.
- **no ``move_file``** — conflict resolution edits files in place; renames are
  not part of resolving a conflict.

``rebase_settings_file`` materializes this dict to a temp settings file for the
duration of a ``with`` block; the CLI and automated callers pass the yielded path
to the rebase workflow as ``settings_file``.

TODO: fold this into the configurable-permissions system from EPIC #1038
(sub-issue #1054, "Claude provider — static settings translation") once it lands.
"""

import json
import logging
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REBASE_LLM_PERMISSIONS: dict[str, Any] = {
    "permissions": {
        "allow": [
            "mcp__mcp-workspace__git",
            "mcp__mcp-tools-py__run_format_code",
            "mcp__mcp-tools-py__run_pylint_check",
            "mcp__mcp-tools-py__run_pytest_check",
            "mcp__mcp-tools-py__run_mypy_check",
            "mcp__mcp-workspace__get_base_branch",
            "mcp__mcp-workspace__read_file",
            "mcp__mcp-workspace__save_file",
            "mcp__mcp-workspace__edit_file",
            "mcp__mcp-workspace__append_file",
            "mcp__mcp-workspace__delete_this_file",
            "mcp__mcp-workspace__list_directory",
            "mcp__mcp-workspace__search_files",
        ]
    },
    "enableAllProjectMcpServers": True,
    "enabledMcpjsonServers": ["mcp-tools-py", "mcp-workspace"],
}


@contextmanager
def rebase_settings_file(override: str | None = None) -> Iterator[str]:
    """Yield the settings path for the rebase LLM session.

    ``override`` (an already-resolved path) is yielded unchanged. Otherwise
    ``REBASE_LLM_PERMISSIONS`` is written to a temp JSON file that exists for the
    whole ``with`` block and is deleted afterwards.

    Args:
        override: Already-resolved settings path, or None for the default.

    Yields:
        Absolute path to the settings file.
    """
    if override is not None:
        yield override
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(REBASE_LLM_PERMISSIONS, handle)
        temp_path = handle.name
    logger.debug("Materialized least-privilege rebase settings to %s", temp_path)
    try:
        yield temp_path
    finally:
        Path(temp_path).unlink(missing_ok=True)
