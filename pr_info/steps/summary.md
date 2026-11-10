# Summary: Make the implement checks a gate (#1389)

Part of epic #1192. #1195–#1197 rewired the checks to the toolkit with unchanged behaviour. This issue changes the behaviour on purpose: the final check goes from advisory ("continuing anyway") to a **gate**, with a capped fix loop and a rescue commit on every abort.

## Behaviour change at a glance

| Entry | Before | After |
|---|---|---|
| `implement_task` | none | `check@quick` |
| `implement_final` | `check@quick` | `check@standard`, `test@quick` |
| `commit`, `rebase`, `rebase_automated` | unchanged | unchanged |

- Both implement entries accept `check` and `test`; `format` is a config error in both.
- Fix loop: all `check` requests run first; their combined findings get one `fix.check` LLM turn. `test` requests run only when every check is clean; their findings get one `fix.test` turn. Any fix restarts from the checks.
- Cap: 3 fix turns per binding run, shared by checks and tests. After the third turn one last pass runs; only its findings count as the cap.
- At the cap: `implement_task` commits and continues; `implement_final` fails as `checks_exhausted` (label `implementing_failed`).
- `error` result, config `ValueError`, typed LLM failure or blocked marker from the check stage → abort. Every check-stage abort first makes a **rescue commit** (fixed message, formatted, pushed). The original failure reason always wins.
- `check_type_hints = false` drops `check@*` requests from the binding and runs the rest (so `implement_final` still runs `test@quick`).
- The final check also runs on a re-run where all tasks are already ticked.

## Architectural / design changes

1. **New module `workflows/implement/check_loop.py`** owns the fix loop and the rescue commit.
   - `check_and_fix_mypy(...)` moves here (name kept; #1199 renames) and returns `CheckOutcome` instead of `bool`.
   - `CheckOutcome(status, detail)` with `status` in `clean | cap | error | blocked | timeout | mcp_unavailable`. The non-clean statuses equal the workflow reason strings, so callers map them with almost no code (`cap → checks_exhausted`, `error → general`).
   - Typed LLM failures (`LLMTimeoutError`, `McpServersUnavailableError`) are **returned**, not raised. Their `detail` carries the blocked-marker text, if any, matching how `process_single_task` reports them today.
   - Requests run one by one through `run_request` (not `run_binding`), grouped by action. `load_toolkit` is called once per pass; the binding and fragments come from that same load. Raw fragments come from `get_fragment` (already returns `""` for missing / raising).
   - Private `_CheckAbort` exception: raised for a config `ValueError` or an `error` result, caught once in the loop → `CheckOutcome("error", detail)`.
   - `rescue_commit(project_dir, reason) -> str`: clears the blocked marker and stale commit-message file, formats (failures logged), commits via `commit_all_changes` with `wip(implement): checks failed (<reason>)`, pushes, and returns a one-line outcome (pushed with sha / push failed / nothing to commit / commit failed). Never raises.
   - The old `_run_check`, `_fix_check_text` and the identical-output counter are deleted.
2. **New module `workflows/implement/blocked.py`** holds `read_and_clear_blocked` and its constants (moved out of `task_processing.py`) so `check_loop.py` can use it without a circular import.
3. **One rescue call site, in `core.py`.** `process_single_task` does not commit on a check abort; it returns its usual reason with `TaskOutcome.checks_failed=True`. `core.py` routes such outcomes, and every final-check abort, through a nested `abort_checks(reason, *, stage, message)` that calls `rescue_commit` and appends `— rescue commit: <outcome>` to the failure message before calling `fail`. Exits from the main implementation LLM call never set the flag, so they still commit nothing.
4. **`check_type_hints` gates removed** from `process_single_task` and `core.py`; the filter lives in the loop. The `get_binding` log-and-skip blocks at both call sites are gone (config errors now abort).
5. **New failure reason `checks_exhausted`** in `failure_reporting.py`, mapped to the existing `implementing_failed` label. No new GitHub label.
6. **Repo / runner config:** `pytest-timeout = 1800` in `[tool.mcp-tools-py]`; the Linux `IMPLEMENT_COMMAND_TEMPLATE` exports `VIRTUAL_ENV` when `.venv/bin/python` exists.
7. Stage names ("Final mypy check") and log wording stay; #1199 renames them.

## Files

### Created
- `src/mcp_coder/workflows/implement/blocked.py`
- `src/mcp_coder/workflows/implement/check_loop.py`
- `tests/workflows/implement/test_check_loop.py`
- `tests/workflows/implement/test_check_loop_fix_turns.py`
- `tests/workflows/implement/test_check_loop_rescue.py`
- `tests/workflows/implement/test_task_processing_checks.py`
- `tests/workflows/implement/test_core_final_check.py`
- `tests/workflows/implement/test_core_check_abort.py`
- `docs/migration/multi-language.md`

### Modified
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/failure_reporting.py`
- `src/mcp_coder/workflows/implement/finalisation.py` (import of `read_and_clear_blocked`)
- `src/mcp_coder/workflows/implement/__init__.py`
- `src/mcp_coder/utils/toolkit_runner.py`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `pyproject.toml`
- `tests/workflows/implement/test_task_processing.py`, `test_task_processing_branch_name.py`, `test_task_processing_blocked.py`, `test_core.py`, `test_core_failure_categories.py`, `test_core_failure_routing.py`, `test_core_workflow.py`, `test_failure_reporting.py`
- `tests/utils/test_toolkit_config.py`, `tests/utils/test_toolkit_permissions.py`, `tests/utils/test_toolkit_runner.py`, `tests/workflows/rebase/test_command_toolkit_binding.py`
- `tests/cli/commands/coordinator/test_command_templates.py`
- `docs/repository-setup/python.md`, `docs/processes-prompts/processes/05-implementation.md`, `docs/architecture/architecture.md`, `docs/repository-setup/quality-and-security-checks.md`

### Deleted
- `tests/workflows/implement/test_task_processing_mypy.py` (replaced by the `test_check_loop*.py` files)

## Constraints

- 750-line file limit: `task_processing.py` (696) and `test_task_processing.py` (747), `test_core_workflow.py` (715) get no new code; new tests go in new files.
- Import git operations only through `mcp_coder.mcp_workspace_git`.
- Each step: tests first, then code; pylint, mypy and pytest pass; one commit.

## Steps

1. Move `read_and_clear_blocked` to `blocked.py` (pure refactor).
2. Add the `checks_exhausted` failure reason.
3. New fix loop (`check_loop.py`, `CheckOutcome`) and both callers on the new result type.
4. Rescue commit and the abort rule.
5. Final check runs on a re-run with all tasks ticked.
6. New default bindings, binding validation, `pytest-timeout = 1800`.
7. Linux implement template exports `VIRTUAL_ENV`.
8. Migration note and doc updates.
