"""Least-privilege Claude Code settings for the automated rebase session.

``REBASE_LLM_PERMISSIONS`` holds exactly the write operations the automated
rebase LLM session needs: the git-write ops and MCP check/file tools from
``.claude/skills/rebase/SKILL.md`` (``allowed-tools``), converted to the
``settings.local.json`` permission-string format.

Deliberately narrower than SKILL.md:
- **no ``push``** — Python performs the final ``--force-with-lease`` push, so the
  LLM never needs a push grant (see summary.md, "Python executes the force-push").
- **no ``uv lock``** — lockfile handling is out of scope for this repo (no tracked
  lockfile exists).

The CLI (Step 7) materializes this dict to a runtime temp settings file and passes
its path to ``prompt_llm`` as ``settings_file``.

TODO: fold this into the configurable-permissions system from EPIC #1038
(sub-issue #1054, "Claude provider — static settings translation") once it lands.
"""

from typing import Any

REBASE_LLM_PERMISSIONS: dict[str, Any] = {
    "permissions": {
        "allow": [
            "mcp__mcp-workspace__git",
            "Bash(git rebase:*)",
            "Bash(git add:*)",
            "Bash(git rm:*)",
            "Bash(git commit:*)",
            "Bash(git checkout --ours:*)",
            "Bash(git checkout --theirs:*)",
            "Bash(git restore:*)",
            "Bash(git remote get-url:*)",
            "Bash(git status:*)",
            "Bash(git diff:*)",
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
            "mcp__mcp-workspace__move_file",
            "mcp__mcp-workspace__list_directory",
            "mcp__mcp-workspace__search_files",
        ]
    },
    "enableAllProjectMcpServers": True,
    "enabledMcpjsonServers": ["mcp-tools-py", "mcp-workspace"],
}
