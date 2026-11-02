# Step 1 — `run_rebase_workflow` returns a structured result

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> Write/adjust the tests first, then the implementation. Run pylint, pytest (fast
> unit set, `-n auto`), mypy and lint-imports until they pass, run
> `run_format_code`, and make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/rebase.py`
- `src/mcp_coder/cli/commands/rebase.py`
- Tests: `tests/workflows/rebase/test_workflow.py`, `test_workflow_regression.py`,
  `test_workflow_safety_net.py`, `test_guards.py` (wherever the return value is
  asserted), `tests/cli/commands/test_rebase.py`

## WHAT

```python
@dataclass(frozen=True)
class RebaseRunResult:
    """Outcome of one ``run_rebase_workflow`` call."""
    exit_code: int          # 0 success/no-op, 1 aborted, 2 error / push rejected
    reason: str             # human-readable; "" never on a non-zero exit
    push_rejected: bool = False  # True only for the force-push rejection


def _end(exit_code: int, reason: str, *, push_rejected: bool = False) -> RebaseRunResult:
    """Log the end of the run and build the result."""


def run_rebase_workflow(...same args...) -> RebaseRunResult
```

## HOW

- Every `return 0/1/2` in `run_rebase_workflow` becomes `return _end(code, reason)`.
- `_end` logs: exit 1 → `logger.log(OUTPUT, "Aborted: %s", reason)`;
  exit 2 → `logger.error("%s", reason)`; exit 0 → `logger.log(OUTPUT, "%s", reason)`.
  Keep the existing message texts as the `reason` (e.g. `"Pre-flight failed: <err>"`,
  `"conflict markers remain in a.py"`, `"force-push rejected; pre-rebase state restored"`)
  so existing log assertions keep matching. Drop the now-duplicated log calls.
- The force-push rejection path: `_end(2, ..., push_rejected=True)`.
- `execute_rebase` returns `run_rebase_workflow(...).exit_code`.
- Update the docstring's Returns section.

## ALGORITHM

```
def _end(code, reason, push_rejected=False):
    if code == 1: log OUTPUT "Aborted: <reason>"
    elif code == 2: log error reason
    else: log OUTPUT reason
    return RebaseRunResult(code, reason, push_rejected)
```

## DATA

`RebaseRunResult(exit_code, reason, push_rejected)`; CLI still returns `int`.

## Tests

- Existing workflow tests assert `.exit_code` instead of the int.
- Parametrized: each abort path's `reason` is non-empty; only the force-push
  rejection sets `push_rejected=True` (a pre-flight exit 2 does not).
- CLI test: `execute_rebase` returns `result.exit_code`.
