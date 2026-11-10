# Step 4: Both callers on the new loop; delete the old one

`process_single_task` and `core.py`'s final check switch to `check_loop.check_and_fix_mypy` and its `CheckOutcome`. The old `check_and_fix_mypy`, `_run_check`, `_fix_check_text` and the identical-output counter are deleted. Rescue commits come in step 5; in this step check-stage aborts fail directly.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement step 4 only. Add the autouse fixture to `tests/workflows/implement/conftest.py` and write the tests in `test_task_processing_checks.py` and `test_core_final_check.py` first, then update `task_processing.py`, `core.py` and `__init__.py`, delete the old fix loop and `tests/workflows/implement/test_task_processing_mypy.py`, and update the existing tests listed below. Keep every file under 750 lines. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- Modify `task_processing.py`, `core.py`, `__init__.py` in `src/mcp_coder/workflows/implement/`.
- Tests (all in `tests/workflows/implement/`): modify `conftest.py`; create `test_task_processing_checks.py`, `test_core_final_check.py`; delete `test_task_processing_mypy.py`; update `test_task_processing.py`, `test_task_processing_bash_grants.py`, `test_task_processing_branch_name.py`, `test_core.py`, `test_core_failure_categories.py`, `test_core_failure_routing.py`, `test_core_workflow.py`.

## HOW
- Delete `_run_check`, `_fix_check_text` and the old `check_and_fix_mypy` from `task_processing.py`; import `check_and_fix_mypy` and `CheckOutcome` from `.check_loop`. Remove now-unused imports (`get_binding`, `load_toolkit`, `run_binding`, `toolkit_declares_bash_grants`, `_build_fix_prompt`, etc. — keep what `process_single_task` still uses).
- `__init__.py` re-exports `check_and_fix_mypy` from `.check_loop`; also export `CheckOutcome`.
- `core.py` imports `check_and_fix_mypy`, `CheckOutcome` and `MAX_FIX_TURNS` from `.check_loop`.

### `process_single_task` (replace Step 7)
Remove the `if not check_type_hints` / `get_binding` block. Then:
```python
try:
    checks = check_and_fix_mypy(project_dir, step_num, provider, env_vars, mcp_config,
                                settings_file, entry="implement_task",
                                check_type_hints=check_type_hints)
finally:
    marker = read_and_clear_blocked(project_dir)   # safety net
if checks.status in ("clean", "cap") and marker:
    checks = CheckOutcome("blocked", marker)
if checks.status == "cap":
    logger.warning("Per-task checks still report findings - committing and continuing")
elif checks.status != "clean":
    return TaskOutcome(False, checks.status, checks.detail)
```
`error` maps to the existing `"error"` reason (core routes it to `general` with `outcome.detail`); `blocked`, `timeout`, `mcp_unavailable` are existing reasons. Update the docstring's reason list.

### `core.py` final check (Step 5 block)
- Remove the `get_binding` try block and `final_binding`; the gate becomes `if progress.completed > 0:` (step 6 removes that too). Drop the `get_binding` import.
- Call `check_and_fix_mypy(..., entry="implement_final", check_type_hints=implement_config.check_type_hints)` inside the existing `try/finally: read_and_clear_blocked`, capturing the marker; promote `clean` + marker to `blocked`.
- Map a non-clean outcome to `fail` with stage `"Final mypy check"`:

| status | reason | message |
|---|---|---|
| `cap` | `checks_exhausted` | `f"Checks still report findings after {MAX_FIX_TURNS} fix turns"` + `: detail` if any |
| `error` | `general` | `detail` |
| `blocked` | `blocked` | `detail` (log at ERROR like the task path) |
| `timeout` / `mcp_unavailable` | same | `append_detail("LLM failure during final mypy check", detail)` |

- Delete the inner `try/except (LLMTimeoutError, McpServersUnavailableError)` and the "continuing anyway" warning. Formatting, commit and push of a clean run stay as they are.

## DATA
- `TaskOutcome` unchanged in this step.

## Tests (write first)

`conftest.py` — add an autouse fixture that patches `mcp_coder.workflows.implement.task_processing.check_and_fix_mypy` with `return_value=CheckOutcome("clean")`. Without it, every `process_single_task` test that never patched the check (default `check_type_hints=False` used to skip it) reaches the real loop and `load_toolkit` on `/test/project` or `tmp_path`. This covers `test_task_processing_blocked.py`, `test_task_progress_gate.py`, `test_task_processing_branch_name.py`, `test_task_processing_bash_grants.py` and `test_task_processing.py`, and adds no lines to `test_task_processing.py` (747 lines).
Opting out: a test that needs another result patches the same target itself (`@patch(".../task_processing.check_and_fix_mypy", ...)` or `with patch(...)`); the innermost patch wins over the fixture. The `check_loop` unit tests (step 3) call `check_loop` directly, so the fixture never touches them. Tests that need the real `task_processing.check_and_fix_mypy` mark themselves `@pytest.mark.real_check_loop` (register the marker in `pyproject.toml`'s pytest markers); the fixture yields without patching when `request.node.get_closest_marker("real_check_loop")` is set, as `_tracker_count_always_decreases` does in `test_task_progress_gate.py`.

`test_task_processing_checks.py` — `process_single_task` with `check_and_fix_mypy` patched:
- `clean` and `cap` → commit, push, `completed`.
- `error` → `TaskOutcome(False, "error", detail)`; no commit.
- `blocked` → `blocked` outcome; no commit.
- `timeout` / `mcp_unavailable` → same reason, detail kept; no commit.
- a marker found in the `finally` after a `clean` result → `blocked`.
- `check_type_hints` is forwarded and `entry="implement_task"`.

`test_core_final_check.py` — `run_implement_workflow` with one completed task and `check_and_fix_mypy` patched:
- `cap` → `_fail` reason `checks_exhausted`, stage "Final mypy check".
- `error` → `general` with the detail as message.
- `blocked` → `blocked`; a marker read in the `finally` after `clean` → `blocked`.
- `timeout` / `mcp_unavailable` → their reasons, message includes the appended marker text.
- `check_type_hints` from `ImplementConfig` is forwarded.

Existing tests:
- `test_task_processing.py`: delete the four check-gate tests (the `check_type_hints` / binding-empty / binding-error tests around lines 431–620) — they test removed behaviour. Drop every `task_processing.get_binding` patch. Tests that patch `check_and_fix_mypy` themselves return `CheckOutcome("clean")`; update `TestIntegration` to assert the new call (`check_type_hints=True`, no `get_binding` patch).
- `test_task_processing_bash_grants.py`: drop the `task_processing.get_binding` patch (the attribute no longer exists) and the matching mock parameter; the conftest fixture covers the check.
- `test_task_processing_branch_name.py`: drop the old `check_and_fix_mypy` / `_run_check` / `_fix_check_text` test (step 3 covers branch forwarding in `test_check_loop_fix_turns.py`).
- `test_core_workflow.py`: `core.get_binding` no longer exists, so the `@patch("mcp_coder.workflows.implement.core.get_binding", ...)` decorators at ~line 51 and ~line 174 raise `AttributeError`. At ~51 (`test_full_workflow_success`, `return_value=()` used to skip the final check) replace it with `@patch("mcp_coder.workflows.implement.core.check_and_fix_mypy", return_value=CheckOutcome("clean"))` and rename the mock parameter. Move the config-`ValueError` test (~174, asserting `"Final mypy check failed: bad toolkit config"` at ~222) into `test_core_final_check.py`, rewritten as: `check_and_fix_mypy` returns `CheckOutcome("error", "bad toolkit config")` → `_fail` reason `general`, stage "Final mypy check", message `"bad toolkit config"`. Delete it from `test_core_workflow.py` (715 lines, near the limit).
- Core tests: replace `return_value=True` with `return_value=CheckOutcome("clean")`; tests that set `side_effect=LLMTimeoutError(...)` become `return_value=CheckOutcome("timeout")`; tests asserting the final check is skipped when `check_type_hints=False` now assert it is called with `check_type_hints=False`.
- Delete `test_task_processing_mypy.py`; its useful cases are covered by `test_check_loop*.py`.
