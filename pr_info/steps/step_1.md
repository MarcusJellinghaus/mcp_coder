# Step 1: src/ W0611 — unused imports (36 occurrences)

## Goal
Remove unused imports from `src/`. Pure deletions — zero logic change, zero risk.

## VERIFY BEFORE REMOVING

The following imports may be intentional try/except availability checks. Verify before removing — if they are intentional, use `# pylint: disable=unused-import` instead:

- `import langchain_mcp_adapters` and `import langgraph` in `agent.py`'s `_check_agent_dependencies` — these may be checking package availability
- `import mlflow` in `mlflow_logger.py`'s `is_mlflow_available()` — this may be an availability probe

## WHERE — Files Modified

- `src/mcp_coder/cli/commands/create_pr.py` — remove `from pathlib import Path`
- `src/mcp_coder/cli/commands/implement.py` — remove `from pathlib import Path`
- `src/mcp_coder/cli/commands/prompt.py` — remove `import os`
- `src/mcp_coder/cli/commands/coordinator/commands.py` — remove `get_folder_git_status` from import
- `src/mcp_coder/cli/commands/coordinator/core.py` — remove `Path` from pathlib import; remove `CacheData` from issues import
- `src/mcp_coder/llm/mlflow_logger.py` — remove `Path` from pathlib import; **verify** inline `import mlflow` inside `is_mlflow_available` (see note above)
- `src/mcp_coder/llm/providers/claude/claude_code_api.py` — remove `import json`, `import os`, `find_claude_executable` import
- `src/mcp_coder/llm/providers/langchain/agent.py` — **verify** inline `import langchain_mcp_adapters` and `import langgraph` inside `_check_agent_dependencies` (see note above)
- `src/mcp_coder/utils/mlflow_config_loader.py` — remove `Optional` from typing import
- `src/mcp_coder/utils/github_operations/pr_manager.py` — remove `Any`, `Dict` from typing; remove `Repository` from `github.Repository`; remove `parse_github_url` import
- `src/mcp_coder/utils/git_operations/branches.py` — remove `get_current_branch_name`, `get_default_branch_name` from readers import
- `src/mcp_coder/utils/git_operations/commits.py` — remove `import logging`
- `src/mcp_coder/utils/git_operations/core.py` — remove `Any` from typing; remove `GitCommandError`, `InvalidGitRepositoryError` from `git.exc`
- `src/mcp_coder/utils/git_operations/diffs.py` — remove `import logging`; remove `GIT_SHORT_HASH_LENGTH` from core import
- `src/mcp_coder/utils/git_operations/file_tracking.py` — remove `import logging`
- `src/mcp_coder/utils/git_operations/staging.py` — remove `import logging`
- `src/mcp_coder/workflows/implement/core.py` — remove `truncate_ci_details` import; remove `JobData` import
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py` — remove `DeletionResult` import
- `src/mcp_coder/workflows/vscodeclaude/issues.py` — remove `load_vscodeclaude_config` import
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — remove `get_stage_display_name`, `truncate_title` from helpers import; remove `is_status_eligible_for_session` from issues import
- `src/mcp_coder/workflows/vscodeclaude/status.py` — remove `load_sessions` import

## WHAT

Delete import lines or remove unused names from multi-name imports. If an import is an intentional availability check, add `# pylint: disable=unused-import` instead.

## ALGORITHM

```
For each file in the list:
    Open file, find the exact import line(s) reported by pylint
    Delete just the unused name(s) from the import line (or whole line if only name)
    For intentional availability checks: add # pylint: disable=unused-import
```

## DATA

Pylint count reduced by: **36 warnings**.

## TDD Note

Run existing tests after changes to confirm nothing broken.

---

## LLM Prompt

```
Please implement Step 1 of the pylint warning cleanup described in
`pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.

This step fixes W0611 (unused imports) in `src/` only.

IMPORTANT — verify before removing these imports (they may be intentional):
- `import langchain_mcp_adapters` and `import langgraph` in agent.py _check_agent_dependencies
- `import mlflow` in mlflow_logger.py is_mlflow_available()
If they are intentional availability checks, use # pylint: disable=unused-import instead.

Rules:
- Remove unused import lines (or just the unused names from multi-name imports)
- Do NOT change any logic
- Run pylint, pytest (fast unit tests), and mypy to verify
```
