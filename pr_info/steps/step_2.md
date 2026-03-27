# Step 2: Update `_format_failure_comment()` to Include Elapsed Time and Build URL

## Context

See [summary.md](summary.md) for full context. This step updates the failure comment formatter to display the two new fields when present.

## WHERE

- **Source**: `src/mcp_coder/workflows/implement/core.py` — `_format_failure_comment()` function
- **Tests**: `tests/workflows/implement/test_core.py` — `TestFormatFailureComment` class

## WHAT

Update `_format_failure_comment()` to conditionally include `**Elapsed:**` and `**Build:**` lines.

### Updated function (pseudocode):

```python
def _format_failure_comment(failure: WorkflowFailure, diff_stat: str) -> str:
    lines = [
        "## Implementation Failed",
        f"**Category:** {failure.category.name.replace('_', ' ').title()}",
        f"**Stage:** {failure.stage}",
        f"**Error:** {failure.message}",
    ]
    if failure.tasks_total > 0:
        lines.append(f"**Progress:** {failure.tasks_completed}/{failure.tasks_total} tasks completed")
    if failure.elapsed_time is not None:
        lines.append(f"**Elapsed:** {_format_elapsed_time(failure.elapsed_time)}")
    if failure.build_url:
        lines.append(f"**Build:** {failure.build_url}")
    lines.append("")
    lines.append("### Uncommitted Changes")
    lines.append(f"```\n{diff_stat or 'No uncommitted changes'}\n```")
    return "\n".join(lines)
```

### Helper function:

```python
def _format_elapsed_time(seconds: float) -> str:
    """Format seconds into human-readable string like '12m 34s' or '1h 5m 30s'."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"
```

## HOW

- Add `_format_elapsed_time()` as a private module-level helper in `core.py`
- Modify `_format_failure_comment()` to add the two new optional lines
- Pure functions — no env var reads, no I/O

## DATA

Input: `WorkflowFailure` with optional `build_url` and `elapsed_time`, plus `diff_stat` string.
Output: Markdown-formatted string with conditional lines.

## TESTS

Add to `TestFormatFailureComment` in `tests/workflows/implement/test_core.py`:

```python
def test_includes_elapsed_time_when_set(self):
    failure = WorkflowFailure(
        category=FailureCategory.GENERAL, stage="Test", message="err",
        elapsed_time=754.0,
    )
    comment = _format_failure_comment(failure, "")
    assert "**Elapsed:** 12m 34s" in comment

def test_includes_build_url_when_set(self):
    failure = WorkflowFailure(
        category=FailureCategory.GENERAL, stage="Test", message="err",
        build_url="https://jenkins.example.com/job/123/console",
    )
    comment = _format_failure_comment(failure, "")
    assert "**Build:** https://jenkins.example.com/job/123/console" in comment

def test_excludes_elapsed_time_when_none(self):
    failure = WorkflowFailure(
        category=FailureCategory.GENERAL, stage="Test", message="err",
    )
    comment = _format_failure_comment(failure, "")
    assert "Elapsed" not in comment

def test_excludes_build_url_when_none(self):
    failure = WorkflowFailure(
        category=FailureCategory.GENERAL, stage="Test", message="err",
    )
    comment = _format_failure_comment(failure, "")
    assert "Build" not in comment

def test_includes_both_elapsed_and_build_url(self):
    failure = WorkflowFailure(
        category=FailureCategory.GENERAL, stage="Test", message="err",
        elapsed_time=3661.0, build_url="https://jenkins.example.com/job/1/console",
    )
    comment = _format_failure_comment(failure, "some diff")
    assert "**Elapsed:** 1h 1m 1s" in comment
    assert "**Build:** https://jenkins.example.com/job/1/console" in comment
```

Also add standalone tests for `_format_elapsed_time`:

```python
class TestFormatElapsedTime:
    def test_seconds_only(self):
        assert _format_elapsed_time(45.7) == "45s"

    def test_minutes_and_seconds(self):
        assert _format_elapsed_time(754.0) == "12m 34s"

    def test_hours_minutes_seconds(self):
        assert _format_elapsed_time(3661.0) == "1h 1m 1s"

    def test_zero(self):
        assert _format_elapsed_time(0.0) == "0s"
```

## COMMIT

`feat(core): include elapsed time and build URL in failure comments (#598)`

## LLM PROMPT

```
Implement Step 2 from pr_info/steps/step_2.md.
Context: pr_info/steps/summary.md

1. Add `_format_elapsed_time(seconds: float) -> str` helper to `src/mcp_coder/workflows/implement/core.py`.
2. Update `_format_failure_comment()` to include "**Elapsed:**" and "**Build:**" lines when the corresponding WorkflowFailure fields are set (non-None).
3. Add tests in `tests/workflows/implement/test_core.py` for the updated formatter and the new helper.

These are pure functions with no I/O. Run all code quality checks.
Commit: "feat(core): include elapsed time and build URL in failure comments (#598)"
```
