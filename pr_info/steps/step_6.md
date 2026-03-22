# Step 6: src/ W0603 — global-statement inline-disables (7 occurrences)

## Goal
Add inline pylint disables for intentional global statements. These are module-level
singletons where `lru_cache` would break test resets.

## WHERE — Files Modified

`src/mcp_coder/llm/mlflow_logger.py`:
- `is_mlflow_available()` line 49: `global _mlflow_available`
- `get_mlflow_logger()` line 702: `global _global_logger`

`src/mcp_coder/workflows/vscodeclaude/sessions.py`:
- `_get_vscode_processes()` line 135: `global _vscode_process_cache`
- `clear_vscode_process_cache()` line 174: `global _vscode_process_cache`
- `_get_vscode_pids()` line 192: `global _vscode_pid_cache`
- `_get_vscode_window_titles()` line 222: `global _vscode_window_cache`
- `clear_vscode_window_cache()` line 270: `global _vscode_window_cache`

## WHAT

```python
global _some_var  # pylint: disable=global-statement  # module-level singleton
```

## DATA

Pylint count reduced by: **7 warnings**.

## TDD Note

Comments only — no logic change. Run existing tests to confirm.

---

## LLM Prompt

```
Please implement Step 6: fix W0603 (global-statement) in src/.
See pr_info/steps/step_6.md for exact locations.
Rules: append `# pylint: disable=global-statement  # module-level singleton` to each global line.
No code changes. Run pylint, pytest (fast unit tests), and mypy to verify.
```
