"""Least-privilege Claude Code settings for the automated rebase session.

``rebase_settings`` generates the allowlist for a rebase binding entry: a fixed
set of ``mcp-workspace`` tools (the read-only git tool and the file tools) plus
the non-Bash grants of the toolkit's ``llm_permissions`` for that entry, e.g. a
Python toolkit's MCP check tools. ``enabledMcpjsonServers`` is derived from the
``mcp__<server>__`` prefixes of those grants.

Deliberately narrow:
- **no ``Bash(...)`` grants in the settings** — regression-fix turns get the
  toolkit's exact ``Bash(...)`` grants via ``--allowedTools``
  (``llm_permissions``), which also applies when a ``--settings`` override
  replaces the generated settings; conflict turns get none. All git writes are
  performed by the surrounding Python program; the LLM reads git state via
  ``mcp__mcp-workspace__git`` only.
- **no ``run_format_code``** — ``run_formatters`` runs after each fix turn, so
  the LLM never formats.
- **no ``push``** — Python performs the final ``--force-with-lease`` push, so the
  LLM never needs a push grant (see summary.md, "Python executes the force-push").
- **no ``uv lock``** — lockfile handling is out of scope for this repo (no tracked
  lockfile exists).
- **no reference-project tools** — the rebase session works on this repo only.
- **no ``move_file``** — conflict resolution edits files in place; renames are
  not part of resolving a conflict.

``rebase_settings_file`` materializes the generated settings to a temp file for
the duration of a ``with`` block; the CLI and automated callers pass the yielded
path to the rebase workflow as ``settings_file``.

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

from mcp_coder.utils.toolkit_runner import bash_grants_of, llm_permissions

logger = logging.getLogger(__name__)

_WORKSPACE_SERVER = "mcp-workspace"
_WORKSPACE_TOOLS: tuple[str, ...] = (
    "mcp__mcp-workspace__git",
    "mcp__mcp-workspace__get_base_branch",
    "mcp__mcp-workspace__read_file",
    "mcp__mcp-workspace__save_file",
    "mcp__mcp-workspace__edit_file",
    "mcp__mcp-workspace__append_file",
    "mcp__mcp-workspace__delete_this_file",
    "mcp__mcp-workspace__list_directory",
    "mcp__mcp-workspace__search_files",
)


def rebase_settings(project_dir: Path, entry: str) -> dict[str, Any]:
    """Build the Claude Code settings for a rebase LLM session.

    The provider is fixed to ``"claude"``: only Claude reads a settings file.

    Args:
        project_dir: Project root containing the toolkit config.
        entry: Binding entry, ``"rebase"`` or ``"rebase_automated"``.

    Returns:
        Settings dict with ``permissions.allow``, ``enableAllProjectMcpServers``
        and ``enabledMcpjsonServers``.
    """
    perms = llm_permissions(project_dir, "claude", entry)
    bash = bash_grants_of(perms)
    extra = [p for p in perms if p not in bash]
    allow = list(_WORKSPACE_TOOLS) + [p for p in extra if p not in _WORKSPACE_TOOLS]
    other_servers = {p.split("__")[1] for p in extra if p.startswith("mcp__")}
    servers = [_WORKSPACE_SERVER] + sorted(other_servers - {_WORKSPACE_SERVER})
    return {
        "permissions": {"allow": allow},
        "enableAllProjectMcpServers": True,
        "enabledMcpjsonServers": servers,
    }


@contextmanager
def rebase_settings_file(
    project_dir: Path, entry: str, override: str | None = None
) -> Iterator[str]:
    """Yield the settings path for the rebase LLM session.

    ``override`` (an already-resolved path) is yielded unchanged. Otherwise
    ``rebase_settings(project_dir, entry)`` is written to a temp JSON file that
    exists for the whole ``with`` block and is deleted afterwards.

    Args:
        project_dir: Project root containing the toolkit config.
        entry: Binding entry, ``"rebase"`` or ``"rebase_automated"``.
        override: Already-resolved settings path, or None for the default.

    Yields:
        Absolute path to the settings file.
    """
    if override is not None:
        yield override
        return

    settings = rebase_settings(project_dir, entry)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(settings, handle)
        temp_path = handle.name
    logger.debug("Materialized least-privilege rebase settings to %s", temp_path)
    try:
        yield temp_path
    finally:
        Path(temp_path).unlink(missing_ok=True)
