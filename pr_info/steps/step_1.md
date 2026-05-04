# Step 1: Suppress `openai._base_client` and reorganize suppression block

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context, then execute Step 1 (`pr_info/steps/step_1.md`).
>
> Implement the change in TDD order: first add the failing test in `tests/utils/test_log_utils_shim.py`, confirm it fails, then add the production line in `src/mcp_coder/utils/log_utils.py`, then complete the cosmetic reorganization (comment headers, level grouping, blank-line separator, test reordering). Finish with all three MCP quality checks (`run_pylint_check`, `run_pytest_check` with `-n auto` and the unit-test marker exclusions, `run_mypy_check`). Do not introduce data structures, helpers, or any abstraction beyond a single new `getLogger().setLevel()` call.

## WHERE

Modified files (no new files, no new folders):

- `src/mcp_coder/utils/log_utils.py`
- `tests/utils/test_log_utils_shim.py`

## WHAT

### Production: `src/mcp_coder/utils/log_utils.py`

Inside the existing `setup_logging()` function — no signature change:

```python
def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
```

Replace the current four-line suppression block with the following body (after the existing `_upstream_setup_logging(log_level, log_file)` call):

```python
# App-specific third-party suppression, grouped by level
# INFO level
logging.getLogger("github.Requester").setLevel(logging.INFO)
logging.getLogger("openai._base_client").setLevel(logging.INFO)
logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

# WARNING level
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
```

### Test: `tests/utils/test_log_utils_shim.py`

Add new test method:

```python
def test_openai_base_client_suppressed_after_setup(self) -> None:
    """openai._base_client should be at INFO after setup_logging()."""
    setup_logging("DEBUG")
    assert logging.getLogger("openai._base_client").level == logging.INFO
```

Reorder all per-logger tests inside `TestLogSuppressionShim` to match production grouping:

1. `test_github_suppressed_after_setup`
2. `test_openai_base_client_suppressed_after_setup` *(new)*
3. `test_urllib3_suppressed_after_setup`
4. `test_httpcore_suppressed_after_setup`
5. `test_httpx_suppressed_after_setup`

## HOW

- **Imports:** No new imports needed in either file — `logging` and `setup_logging` are already imported in both.
- **Decorators:** None.
- **Integration:** The new line piggybacks on the existing post-`_upstream_setup_logging()` suppression block; no new call sites or wiring.
- **No upstream `mcp-coder-utils` change.** Keep the change inside the local shim.

## ALGORITHM

```
setup_logging(log_level, log_file):
    call upstream setup_logging(log_level, log_file)        # unchanged
    # raise INFO threshold for chatty per-call HTTP loggers
    set "github.Requester"        -> INFO
    set "openai._base_client"     -> INFO   # NEW
    set "urllib3.connectionpool"  -> INFO
    # raise WARNING threshold for transport-layer noise
    set "httpcore" -> WARNING
    set "httpx"    -> WARNING
```

## DATA

- Return value: `None` (unchanged).
- Side effect: five named loggers retrieved via `logging.getLogger()` have their `.level` attribute raised. The new logger added is `"openai._base_client"` at `logging.INFO` (numeric 20).
- No new data structures, no new types, no new constants.

## Acceptance Criteria

- [ ] `tests/utils/test_log_utils_shim.py` contains five per-logger tests in the order: `github → openai → urllib3 → httpcore → httpx`.
- [ ] `test_openai_base_client_suppressed_after_setup` passes.
- [ ] `src/mcp_coder/utils/log_utils.py` suppression block has the combined header `# App-specific third-party suppression, grouped by level`, with `# INFO level` and `# WARNING level` sub-markers, alphabetical within each group, single blank line between groups.
- [ ] `mcp__tools-py__run_pylint_check` passes.
- [ ] `mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])` passes.
- [ ] `mcp__tools-py__run_mypy_check` passes.
- [ ] Single commit covering both files.
