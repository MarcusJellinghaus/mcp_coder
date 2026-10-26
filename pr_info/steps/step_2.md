# Step 2 — Move mypy fix-up tests to `test_task_processing_mypy.py`

## LLM prompt
Read `pr_info/steps/summary.md` (rules, move procedure, import fix-up, standard checks), then
implement this step exactly. This is a pure move: no logic edits. On any failed check, write one line
to `pr_info/.blocked.txt` and stop. Commit once at the end.

## WHERE
- Source: `tests/workflows/implement/test_task_processing.py`
- Destination (new): `tests/workflows/implement/test_task_processing_mypy.py`

## WHAT
Move `TestCheckAndFixMypy` (6 tests) unchanged.

## HOW
1. `move_symbol(source_file="tests/workflows/implement/test_task_processing.py", symbol_names=["TestCheckAndFixMypy"], dest_file="tests/workflows/implement/test_task_processing_mypy.py")`
   (dry run first).
2. Fix imports per the summary's import fix-up. Expect to remove a module-level `LLMTimeoutError` /
   `McpServersUnavailableError` if one was added to `_mypy` or left in the base and ruff flags it.

## ALGORITHM
```
dry-run + move [TestCheckAndFixMypy]
verify method-local imports still inside their methods
fix module-level imports (F401/F811 only)
run standard checks + collect counts; commit
```

## DATA — expected end state
`test_task_processing_mypy.py` imports: `Path`, `MagicMock, patch`, `pytest`,
`from mcp_coder.workflows.implement.task_processing import check_and_fix_mypy`,
`from tests.workflows.implement.test_task_processing import _make_llm_response`.
It has **no** module-level `LLMTimeoutError` / `McpServersUnavailableError`.

Checks that write blocked on failure:
- The method-local imports are unchanged inside `test_check_and_fix_mypy_timeout_propagates` and
  `test_check_and_fix_mypy_mcp_unavailable_propagates`.
- Collect counts: base **28**, `_blocked` **21**, `_mypy` **6**, directory **193**.
- All tests pass.

Commit message: `test(implement): move mypy fix-up tests to test_task_processing_mypy.py (#1329)`
