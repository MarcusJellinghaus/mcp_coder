# Step 6 — Annotate `_RaisingAsyncIter.__init__`

Read `pr_info/steps/summary.md` first for overall context.

Part of issue #1171. Last of the 64 findings: 2 copies of the same
`__init__` missing `-> None`.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["ANN204"]`,
`max_issues=10`. If it does not report
`tests/llm/providers/langchain/test_langchain_agent_streaming.py:19` and
`tests/llm/providers/langchain/test_langchain_streaming.py:18`, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tests/llm/providers/langchain/test_langchain_agent_streaming.py`
- `tests/llm/providers/langchain/test_langchain_streaming.py`

## WHAT

In both files, change:

```python
def __init__(self, exc: BaseException):
```
to
```python
def __init__(self, exc: BaseException) -> None:
```

on the `_RaisingAsyncIter` class.

## HOW

Plain signature edit, no new imports.

## ALGORITHM

N/A.

## DATA

N/A.

## TDD

Not applicable: no new behavior.

## Verification

- `mcp__mcp-tools-py__run_pytest_check` targeting
  `tests/llm/providers/langchain/`, then the full fast suite.
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_format_code`, then commit.

## Commit

One commit: `fix(tests): annotate _RaisingAsyncIter.__init__ return type`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement
> step 6 exactly as specified: add `-> None` to `_RaisingAsyncIter.__init__`
> in both named files. Run the verification commands listed in the step, fix
> anything they report, then run `run_format_code` and commit with the given
> message. If the precondition check fails, write one line to
> `pr_info/.blocked.txt` and stop.
