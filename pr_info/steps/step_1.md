# Step 1 — Baseline + move blocked-marker tests to `test_task_processing_blocked.py`

## LLM prompt
Read `pr_info/steps/summary.md` (rules, move procedure, import fix-up, standard checks), then
implement this step exactly. This is a pure move: no logic edits. On any failed check, write one line
to `pr_info/.blocked.txt` and stop. Commit once at the end.

## WHERE
- Source: `tests/workflows/implement/test_task_processing.py`
- Destination (new): `tests/workflows/implement/test_task_processing_blocked.py`

## WHAT
Move three top-level test classes unchanged:
`TestReadAndClearBlocked` (8 tests), `TestBlockedExitInPrompts` (5), `TestProcessSingleTaskBlocked` (8).

## HOW
1. **Baseline** (before any edit). Use the collect counts from the summary, then
   `run_pytest_check(extra_args=["--collect-only", "-q"])` for the whole suite. Expected:
   `test_task_processing.py: 55`, directory 193, suite 6463.
   Then run `test_task_processing.py` with `-n auto` and the fast-unit filter: 55 passed.
   If a number differs from these, write the actual values to `pr_info/.blocked.txt` and stop.
2. `move_symbol(source_file="tests/workflows/implement/test_task_processing.py", symbol_names=["TestReadAndClearBlocked", "TestBlockedExitInPrompts"], dest_file="tests/workflows/implement/test_task_processing_blocked.py")`
   (dry run first).
3. `move_symbol(..., symbol_names=["TestProcessSingleTaskBlocked"], dest_file=<same>)` (dry run
   first). The class may land above the others. Leave it there.
4. Fix imports per the summary's import fix-up.

## ALGORITHM
```
record baseline counts; abort if they differ from 55/193/6463/55 passed
dry-run + move [TestReadAndClearBlocked, TestBlockedExitInPrompts]
dry-run + move [TestProcessSingleTaskBlocked]
verify alias import, decorators, helper import
fix module-level imports (F401/F811 only)
run standard checks + collect counts; commit
```

## DATA — expected end state
`test_task_processing_blocked.py` imports these (order is the formatter's):
`Callable` (collections.abc), `Path`, `Any`, `MagicMock, patch`, `PROMPTS_FILE_PATH`,
`LLMTimeoutError`, `McpServersUnavailableError`, `get_prompt`,
`from mcp_coder.workflow_steps.constants import BLOCKED_FILE`,
`from mcp_coder.workflows.implement.constants import BLOCKED_FILE as IMPLEMENT_BLOCKED_FILE`,
`task_processing`: `BLOCKED_REASON_FALLBACK, BLOCKED_REASON_MAX_CHARS, RETRY_REMINDER, TaskOutcome, process_single_task, process_task_with_retry, read_and_clear_blocked`,
`from tests.workflows.implement.test_task_processing import _make_llm_response`. No `import pytest`.

Checks that write blocked on failure:
- The `IMPLEMENT_BLOCKED_FILE` alias import is separate from the plain `BLOCKED_FILE` import. Fixing
  it by rewriting that one import line is allowed; anything more → blocked.
- `_write_marker` keeps `@staticmethod` and `_llm_writes_marker` keeps `@classmethod`.
- `_make_llm_response` and `_tracker_count_always_decreases` are still defined in the base file.
- Collect counts: base **34**, `_blocked` **21**, directory **193**.
- All tests pass. A `no_progress` failure means a test lost the fixture → blocked.

Commit message: `test(implement): move blocked-marker tests to test_task_processing_blocked.py (#1329)`
