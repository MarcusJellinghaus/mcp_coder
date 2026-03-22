# Step 1: Fix `src/` removals — W0611, W0612, W0613, W1309

## Goal
Remove unused imports, unused variables, rename unused arguments, and remove bare f-prefix.
Pure deletions and one-character renames — zero logic change, zero risk.

## WHERE — Files Modified

**W0611 — Remove unused imports (36 total):**
- `src/mcp_coder/cli/commands/create_pr.py` — remove `from pathlib import Path`
- `src/mcp_coder/cli/commands/implement.py` — remove `from pathlib import Path`
- `src/mcp_coder/cli/commands/prompt.py` — remove `import os`
- `src/mcp_coder/cli/commands/coordinator/commands.py` — remove `get_folder_git_status` from import
- `src/mcp_coder/cli/commands/coordinator/core.py` — remove `Path` from pathlib import; remove `CacheData` from issues import
- `src/mcp_coder/llm/mlflow_logger.py` — remove `Path` from pathlib import; remove inline `import mlflow` inside `is_mlflow_available` (the function already works without it — the `mlflow` name is unused after the try block)
- `src/mcp_coder/llm/providers/claude/claude_code_api.py` — remove `import json`, `import os`, `find_claude_executable` import
- `src/mcp_coder/llm/providers/langchain/agent.py` — remove inline `import langchain_mcp_adapters` and `import langgraph` inside `_check_agent_dependencies`
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

**W0612 — Fix unused variables (5 total):**
- `src/mcp_coder/prompt_manager.py` line 565 — change `except Exception as e:` → `except Exception:`  (variable `e` unused in that handler)
- `src/mcp_coder/checks/branch_status.py` line 192 — remove local `logger = ...` reassignment (shadows module logger)
- `src/mcp_coder/cli/commands/check_branch_status.py` line 347 — change `ci_status = ...` → `_ = ...` or just call without assigning
- `src/mcp_coder/llm/providers/claude/claude_cli_verification.py` line 45 — change `claude_path, ...` unpack to `_, ...`
- `src/mcp_coder/utils/git_operations/readers.py` line 117 — change `index_status = ...` → `_ = ...`

**W0613 — Rename unused arguments (8 total):**
- `src/mcp_coder/cli/main.py` — `handle_no_command(args)` → `handle_no_command(_args)`
- `src/mcp_coder/cli/commands/help.py` — `execute_help(args)` → `execute_help(_args)`
- `src/mcp_coder/cli/commands/coordinator/core.py` — `get_eligible_issues(..., log_level)` → `..., _log_level`; `dispatch_workflow(workflow_name, ...)` → `_workflow_name, ...`
- `src/mcp_coder/llm/providers/langchain/agent.py` — `run_agent(..., execution_dir)` → `..., _execution_dir`
- `src/mcp_coder/utils/folder_deletion.py` — `_rmtree_remove_readonly(..., exc)` → `..., _exc`
- `src/mcp_coder/workflows/create_plan.py` — `manage_branch(..., issue_title)` → `..., _issue_title`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — `launch_vscode(workspace_file, session_working_dir)` → `launch_vscode(workspace_file, _session_working_dir=None)`

**W1309 — Remove bare f-prefix (1 total):**
- `src/mcp_coder/cli/commands/verify.py` line 131 — change `f"some literal string"` → `"some literal string"`

## WHAT

No new functions. All changes are:
- Delete import lines
- `except Exception as e:` → `except Exception:` (when `e` is unused)
- `varname = expr` → `_ = expr` (when result is discarded)
- `def foo(param)` → `def foo(_param)` (when param is unused)
- `f"literal"` → `"literal"` (when no `{}` interpolation)

## HOW

No integration points change. All callers of renamed `_args` / `_log_level` etc. parameters
pass positional values — renaming only the parameter name, not the call sites.

For `launch_vscode`, the parameter `session_working_dir` becomes `_session_working_dir`;
all existing callers pass it positionally or by keyword — no call-site change needed.

## ALGORITHM

```
For each file in the W0611 list:
    Open file, find the exact import line(s) reported by pylint
    Delete just the unused name(s) from the import line (or whole line if only name)

For each W0612 location:
    If `except Exception as e:` with unused `e` → remove `as e`
    If `varname = result` where result unused → `_ = result`

For each W0613 location:
    Rename parameter in function signature to `_original_name`
    Do NOT rename any call sites

For W1309:
    Remove `f` prefix from string literal
```

## DATA

No return value changes. No type changes. Pylint count reduced by: 36 + 5 + 8 + 1 = **50 warnings**.

## TDD Note

These are purely structural removals with no logic change. No new tests needed.
Run existing tests after changes to confirm nothing broken.

---

## LLM Prompt

```
Please implement Step 1 of the pylint warning cleanup described in
`pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.

This step fixes W0611 (unused imports), W0612 (unused variables),
W0613 (unused arguments), and W1309 (f-string without interpolation)
in `src/` only.

Rules:
- Remove unused import lines (or just the unused names from multi-name imports)
- For `except Exception as e:` where `e` is unused: remove `as e`
- For unused assigned variables: replace `varname` with `_`
- For unused function parameters: rename to `_original_name` in the signature only
- For bare f-strings: remove the `f` prefix
- Do NOT change any logic, do NOT rename call sites
- Run pylint (src/ only, with --disable=C,R,W1203 --enable=W) to verify
  W0611/W0612/W0613/W1309 are gone
- Run pytest (fast unit tests, -m "not git_integration and not ...") to confirm
  no regressions
- Run mypy to confirm type safety

The exact files and line numbers are listed in step_1.md under each warning code.
```
