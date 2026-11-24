# Step 3 — `DispatchResult` from `dispatch_workflow`

## LLM prompt

> Read `pr_info/steps/summary.md` (section "`dispatch_workflow` result") and this file, then
> implement Step 3 only. Write/adjust the tests first, then the implementation. Behaviour of
> `execute_coordinator_run` must not change in this step. Run pylint, mypy and the fast unit
> tests (see `.claude/CLAUDE.md`), run the formatter, and make exactly one commit:
> `refactor(coordinator): dispatch_workflow reports whether a build started`.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/core.py` — new enum, `dispatch_workflow` return type.
- `src/mcp_coder/cli/commands/coordinator/commands.py` — call site in `execute_coordinator_run`.
- `src/mcp_coder/cli/commands/coordinator/__init__.py` — import and export `DispatchResult`.
- Tests: `tests/cli/commands/coordinator/test_core_dispatch.py`, `test_commands.py`,
  `test_integration.py`, `test_commands_trust_gate.py`.

## WHAT

```python
class DispatchResult(Enum):
    """Outcome of dispatch_workflow."""

    STARTED = "started"
    NOT_STARTED = "not_started"  # no linked branch, or invalid repo URL
    STARTED_LABEL_RATE_LIMITED = "started_label_rate_limited"


def dispatch_workflow(...same parameters...) -> DispatchResult:
```

## HOW

- `from enum import Enum` in `core.py`.
- Return mapping inside `dispatch_workflow`:
  - invalid repo URL branch (`return True` today) → `DispatchResult.NOT_STARTED`
  - "No branch found" branch (`return True` today) → `DispatchResult.NOT_STARTED`
  - rate-limited label update (`return False` today) → `DispatchResult.STARTED_LABEL_RATE_LIMITED`
  - success (`return True` today) → `DispatchResult.STARTED`
- Update the docstring `Returns:` section accordingly.
- Call site in `commands.py` (enum members are always truthy, so `if not ...` must go):

```python
result = dispatch_workflow(...)
if result is DispatchResult.STARTED_LABEL_RATE_LIMITED:
    # Job started, label swap hit a rate limit
    return 1
# cache label update unchanged (runs for STARTED and NOT_STARTED, as today)
```

## DATA

- `DispatchResult` enum, three members as above.

## Tests (write/adjust first)

- `test_core_dispatch.py`: assertions on `result` become `DispatchResult.STARTED` /
  `DispatchResult.NOT_STARTED` (missing branch test) / `DispatchResult.STARTED_LABEL_RATE_LIMITED`
  (rate-limited label test). Add one test for the invalid-repo-URL branch → `NOT_STARTED`
  if none exists.
- `test_commands.py`, `test_integration.py`, `test_commands_trust_gate.py`: every
  `dispatch_workflow` mock that returns `True` returns `DispatchResult.STARTED`; a mock returning
  `False` (if any) returns `DispatchResult.STARTED_LABEL_RATE_LIMITED` and still expects exit 1.
- New test in `test_commands.py` (or the trust-gate file's `mocks` fixture): a dispatch returning
  `NOT_STARTED` still triggers `update_issue_labels_in_cache` and the run returns 0.
