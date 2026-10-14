# Step 1 — Annotate `MLflowLogger.__init__` return type

Read `pr_info/steps/summary.md` first for overall context.

Part of issue #1171 (enable ruff `ANN`). This is the one `src/` fix out of 64
total findings; everything else is in `tests/`.

## Precondition check

Open `src/mcp_coder/llm/mlflow_logger.py`. If the `MLflowLogger.__init__`
signature is not exactly `def __init__(self, config: Optional[MLflowConfig] = None):`
(no return annotation), write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`src/mcp_coder/llm/mlflow_logger.py`

## WHAT

Change the `__init__` signature to:

```python
def __init__(self, config: Optional[MLflowConfig] = None) -> None:
```

No other change — the method body already returns nothing.

## HOW

Plain signature edit, no new imports needed (`Optional` already imported).

## ALGORITHM

N/A — type-annotation-only change.

## DATA

N/A.

## TDD note

Not applicable: no new behavior. The check is mypy/ruff agreeing the method
is fully typed.

## Verification

- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_format_code`, then commit.

## Commit

One commit: `fix(mlflow): annotate MLflowLogger.__init__ return type`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement
> step 1 exactly as specified: add `-> None` to `MLflowLogger.__init__` in
> `src/mcp_coder/llm/mlflow_logger.py`. Run the verification commands listed
> in the step, fix anything they report, then run `run_format_code` and
> commit with the given message. If the precondition check fails, write one
> line to `pr_info/.blocked.txt` and stop.
