# Step 1: Add `status_requires_linked_branch()` Helper

## LLM Prompt

```
Implement Step 1 of Issue #422 (see pr_info/steps/summary.md for full context).

Add the `status_requires_linked_branch()` helper function to issues.py with TDD approach.
This is a simple predicate function that determines if a status requires a linked branch.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | ADD function |
| `tests/workflows/vscodeclaude/test_issues.py` | ADD tests |

---

## WHAT

### Function Signature

```python
def status_requires_linked_branch(status: str) -> bool:
    """Check if status requires a linked branch to start/restart session.
    
    Args:
        status: Status label like "status-04:plan-review"
        
    Returns:
        True if status requires linked branch (status-04, status-07)
        False for status-01 and all other statuses
    """
```

---

## HOW

### Integration Points

1. Add function after `is_status_eligible_for_session()` in `issues.py` (around line 115)
2. Export in module's implicit exports (no `__all__` in issues.py)
3. Will be imported by `orchestrator.py` and `status.py` in later steps

---

## ALGORITHM

```python
def status_requires_linked_branch(status: str) -> bool:
    # Extract status number from label (e.g., "status-04:plan-review" -> 4)
    # Return True if status is 04 or 07
    # Return False otherwise
    return status in ("status-04:plan-review", "status-07:code-review")
```

---

## DATA

### Input
- `status: str` - Status label string (e.g., `"status-04:plan-review"`)

### Output
- `bool` - `True` if linked branch required, `False` otherwise

### Test Cases

| Input | Expected | Reason |
|-------|----------|--------|
| `"status-01:created"` | `False` | Created status allows main fallback |
| `"status-04:plan-review"` | `True` | Plan review requires branch |
| `"status-07:code-review"` | `True` | Code review requires branch |
| `"status-02:bot-pickup"` | `False` | Bot status, not relevant |
| `"status-10:pr-created"` | `False` | PR created, not relevant |
| `""` | `False` | Empty string edge case |
| `"invalid"` | `False` | Invalid status edge case |

---

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_issues.py`

Add new test class after existing tests:

```python
class TestStatusRequiresLinkedBranch:
    """Tests for status_requires_linked_branch()."""

    def test_status_01_does_not_require_branch(self) -> None:
        """status-01:created allows fallback to main."""
        assert status_requires_linked_branch("status-01:created") is False

    def test_status_04_requires_branch(self) -> None:
        """status-04:plan-review requires linked branch."""
        assert status_requires_linked_branch("status-04:plan-review") is True

    def test_status_07_requires_branch(self) -> None:
        """status-07:code-review requires linked branch."""
        assert status_requires_linked_branch("status-07:code-review") is True

    def test_bot_statuses_do_not_require_branch(self) -> None:
        """Bot statuses don't require linked branch."""
        assert status_requires_linked_branch("status-02:bot-pickup") is False
        assert status_requires_linked_branch("status-05:bot-pickup") is False
        assert status_requires_linked_branch("status-08:bot-pickup") is False

    def test_pr_created_does_not_require_branch(self) -> None:
        """status-10:pr-created doesn't require linked branch."""
        assert status_requires_linked_branch("status-10:pr-created") is False

    def test_empty_string_returns_false(self) -> None:
        """Empty string returns False."""
        assert status_requires_linked_branch("") is False

    def test_invalid_status_returns_false(self) -> None:
        """Invalid status string returns False."""
        assert status_requires_linked_branch("invalid") is False
        assert status_requires_linked_branch("status-99:unknown") is False
```

---

## VERIFICATION

After implementation, run:

```bash
pytest tests/workflows/vscodeclaude/test_issues.py::TestStatusRequiresLinkedBranch -v
```

All 7 tests should pass.
