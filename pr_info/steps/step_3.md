# Step 3 — Move retry-wrapper tests to `test_task_processing_retry.py`

## LLM prompt
Read `pr_info/steps/summary.md` (rules, move procedure, import fix-up, standard checks), then
implement this step exactly. This is a pure move: no logic edits. On any failed check, write one line
to `pr_info/.blocked.txt` and stop. Commit once at the end.

## WHERE
- Source: `tests/workflows/implement/test_task_processing.py`
- Destination (new): `tests/workflows/implement/test_task_processing_retry.py`

## WHAT
Move `TestProcessTaskWithRetry` (8 tests) unchanged.

## HOW
1. `move_symbol(source_file="tests/workflows/implement/test_task_processing.py", symbol_names=["TestProcessTaskWithRetry"], dest_file="tests/workflows/implement/test_task_processing_retry.py")`
   (dry run first).
2. Fix imports per the summary's import fix-up.

## ALGORITHM
```
dry-run + move [TestProcessTaskWithRetry]
verify method-local McpServersUnavailableError import still inside its method
fix module-level imports (F401/F811 only)
run standard checks + collect counts; commit
```

## DATA — expected end state
`test_task_processing_retry.py` imports: `Path`, `MagicMock, patch`,
`from mcp_coder.workflows.implement.task_processing import TaskOutcome, process_task_with_retry`.
It has no `_make_llm_response`, no `pytest`, and no module-level `McpServersUnavailableError`.

Checks that write blocked on failure:
- The method-local import in `test_mcp_unavailable_categorized_as_reason` is unchanged.
- Collect counts: base **20**, `_blocked` **21**, `_mypy` **6**, `_retry` **8**, directory **193**.
- All tests pass.

`check_file_size` is not part of this step. The base file may now be under 750 lines, and step 4
removes its allowlist entry.

Commit message: `test(implement): move retry tests to test_task_processing_retry.py (#1329)`
