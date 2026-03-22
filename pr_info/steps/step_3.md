# Step 3: src/ W0613 + W1309 — unused arguments + bare f-string (9 occurrences)

## Goal
Rename unused function arguments to `_name` and remove bare f-prefix. Both trivial fixes.

## WHERE — Files Modified

**W0613 — Rename unused arguments (8 total):**
- `src/mcp_coder/cli/main.py` — `handle_no_command(args)` to `handle_no_command(_args)`
- `src/mcp_coder/cli/commands/help.py` — `execute_help(args)` to `execute_help(_args)`
- `src/mcp_coder/cli/commands/coordinator/core.py` — `get_eligible_issues(..., log_level)` to `..., _log_level`; `dispatch_workflow(workflow_name, ...)` to `_workflow_name, ...`
- `src/mcp_coder/llm/providers/langchain/agent.py` — `run_agent(..., execution_dir)` to `..., _execution_dir`
- `src/mcp_coder/utils/folder_deletion.py` — `_rmtree_remove_readonly(..., exc)` to `..., _exc`
- `src/mcp_coder/workflows/create_plan.py` — `manage_branch(..., issue_title)` to `..., _issue_title`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — `launch_vscode(workspace_file, session_working_dir)` to `launch_vscode(workspace_file, _session_working_dir)`

**W1309 — Remove bare f-prefix (1 total):**
- `src/mcp_coder/cli/commands/verify.py` line 131 — change `f"some literal string"` to `"some literal string"`

## WHAT

- `def foo(param)` to `def foo(_param)` (when param is unused)
- `f"literal"` to `"literal"` (when no `{}` interpolation)

## ALGORITHM

```
For each W0613: rename parameter in function signature to _original_name (NOT call sites)
For W1309: remove f prefix from string literal
```

## DATA

Pylint count reduced by: **9 warnings**.

## TDD Note

Run existing tests after changes to confirm nothing broken.

---

## LLM Prompt

```
Please implement Step 3: fix W0613 (unused arguments) and W1309 (bare f-string) in src/.
See pr_info/steps/step_3.md for exact locations.
Rules: rename unused params to _name in signature only. Remove f prefix from bare f-strings.
No logic changes. Run pylint, pytest (fast unit tests), and mypy to verify.
```
