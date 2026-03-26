# Step 1: Add `FailureCategory` enum and `WorkflowFailure` dataclass

## Context
See [summary.md](./summary.md) for full implementation overview.

This step adds the data structures that all subsequent steps depend on.

## WHERE
- `src/mcp_coder/workflows/implement/constants.py` — add to existing file
- `src/mcp_coder/workflows/implement/__init__.py` — add exports
- `tests/workflows/implement/test_constants.py` — new test file (simple, test-first)

## WHAT

### `FailureCategory` (Enum)
```python
class FailureCategory(Enum):
    """Maps 1:1 to failure label IDs in labels.json."""
    GENERAL = "implementing_failed"
    CI_FIX_EXHAUSTED = "ci_fix_needed"
    LLM_TIMEOUT = "llm_timeout"
```

### `WorkflowFailure` (frozen dataclass)
```python
@dataclass(frozen=True)
class WorkflowFailure:
    """Structured failure info for the implement workflow."""
    category: FailureCategory
    stage: str                  # human-readable: "black formatting", "LLM call"
    message: str                # one-line error description
    tasks_completed: int = 0
    tasks_total: int = 0
```

## HOW
- Import `Enum` from `enum` and `dataclass` from `dataclasses` (already imported in constants.py for other uses — check)
- Add both at the bottom of `constants.py`
- Export from `__init__.py`

## DATA
- `FailureCategory.GENERAL.value` → `"implementing_failed"` (matches `labels.json` `internal_id`)
- `WorkflowFailure` is frozen — immutable after creation
- `tasks_completed` and `tasks_total` default to 0 (for failures where task count is unknown)

## TESTS (write first)
```python
# tests/workflows/implement/test_constants.py
class TestFailureCategory:
    def test_values_match_label_ids():
        """FailureCategory values must match labels.json internal_id values."""
        assert FailureCategory.GENERAL.value == "implementing_failed"
        assert FailureCategory.CI_FIX_EXHAUSTED.value == "ci_fix_needed"
        assert FailureCategory.LLM_TIMEOUT.value == "llm_timeout"

class TestWorkflowFailure:
    def test_frozen():
        """WorkflowFailure should be immutable."""
        wf = WorkflowFailure(category=FailureCategory.GENERAL, stage="test", message="msg")
        with pytest.raises(FrozenInstanceError):
            wf.stage = "other"

    def test_defaults():
        """Default task counts should be 0."""
        wf = WorkflowFailure(category=FailureCategory.GENERAL, stage="test", message="msg")
        assert wf.tasks_completed == 0
        assert wf.tasks_total == 0

    def test_with_task_counts():
        """Task counts should be settable."""
        wf = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT, stage="task impl",
            message="timed out", tasks_completed=2, tasks_total=5
        )
        assert wf.tasks_completed == 2
        assert wf.tasks_total == 5
```

## LLM PROMPT
```
Implement Step 1 of issue #189 (see pr_info/steps/summary.md for context).

Add `FailureCategory` enum and `WorkflowFailure` frozen dataclass to
`src/mcp_coder/workflows/implement/constants.py`.

Write tests first in `tests/workflows/implement/test_constants.py`,
then implement, then export from `__init__.py`.

See pr_info/steps/step_1.md for exact signatures and test cases.
Run all quality checks after changes.
```
