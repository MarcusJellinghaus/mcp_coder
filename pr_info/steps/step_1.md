# Step 1: Add `build_url` and `elapsed_time` to `WorkflowFailure` Dataclass

## Context

See [summary.md](summary.md) for full context. This step adds the two new optional fields to the `WorkflowFailure` frozen dataclass, plus tests.

## WHERE

- **Source**: `src/mcp_coder/workflows/implement/constants.py`
- **Tests**: `tests/workflows/implement/test_constants.py`

## WHAT

Extend the `WorkflowFailure` dataclass with two new optional fields:

```python
@dataclass(frozen=True)
class WorkflowFailure:
    """Structured failure info for the implement workflow."""
    category: FailureCategory
    stage: str
    message: str
    tasks_completed: int = 0
    tasks_total: int = 0
    build_url: str | None = None      # NEW — from BUILD_URL env var
    elapsed_time: float | None = None  # NEW — seconds since workflow start
```

## HOW

- Add `from __future__ import annotations` if not present (for `str | None` syntax)
- Add two fields with `None` defaults after existing defaults — no breaking changes to existing callers

## DATA

- `build_url`: Optional string, e.g. `"https://jenkins.example.com/job/Windows-Agents/123/console"`
- `elapsed_time`: Optional float in seconds, e.g. `754.3`

## TESTS

Add to `tests/workflows/implement/test_constants.py`:

```python
class TestWorkflowFailure:
    # Existing tests: test_frozen, test_defaults, test_with_task_counts

    def test_build_url_default_none(self):
        """build_url defaults to None."""
        failure = WorkflowFailure(category=FailureCategory.GENERAL, stage="test", message="msg")
        assert failure.build_url is None

    def test_elapsed_time_default_none(self):
        """elapsed_time defaults to None."""
        failure = WorkflowFailure(category=FailureCategory.GENERAL, stage="test", message="msg")
        assert failure.elapsed_time is None

    def test_build_url_set(self):
        """build_url can be set."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="msg",
            build_url="https://jenkins.example.com/job/123/console",
        )
        assert failure.build_url == "https://jenkins.example.com/job/123/console"

    def test_elapsed_time_set(self):
        """elapsed_time can be set."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="msg",
            elapsed_time=754.3,
        )
        assert failure.elapsed_time == 754.3

    def test_frozen_new_fields(self):
        """New fields are also frozen."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="msg",
            build_url="url", elapsed_time=1.0,
        )
        with pytest.raises(FrozenInstanceError):
            failure.build_url = "other"  # type: ignore[misc]
```

## COMMIT

`feat(constants): add build_url and elapsed_time fields to WorkflowFailure (#598)`

## LLM PROMPT

```
Implement Step 1 from pr_info/steps/step_1.md.
Context: pr_info/steps/summary.md

Add `build_url: str | None = None` and `elapsed_time: float | None = None` fields to the
`WorkflowFailure` frozen dataclass in `src/mcp_coder/workflows/implement/constants.py`.

Add tests in `tests/workflows/implement/test_constants.py` for the new fields:
- Default to None
- Can be set
- Are frozen (immutable)

Run all code quality checks. Commit: "feat(constants): add build_url and elapsed_time fields to WorkflowFailure (#598)"
```
