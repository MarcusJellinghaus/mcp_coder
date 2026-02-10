# Step 6: Update `display_status_table()` for New Indicators

## LLM Prompt

```
Implement Step 6 of Issue #422 (see pr_info/steps/summary.md for full context).

Update `display_status_table()` in status.py to show new indicators for branch-related issues.
Pass skip_reason to get_next_action() and show "→ Needs branch" for eligible issues without linked branch.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/status.py` | MODIFY function |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | REFACTOR `execute_coordinator_vscodeclaude_status()` to call `display_status_table()` |
| `tests/workflows/vscodeclaude/test_status_display.py` | ADD tests |

---

## WHAT

### Changes to `display_status_table()`

1. For active sessions: compute `skip_reason` based on branch status for status-04/07
2. Pass `skip_reason` to `get_next_action()`
3. For eligible issues (not yet sessions): show `→ Needs branch` if no linked branch for status-04/07

### New Parameter for `display_status_table()`

Add optional parameter to receive branch availability info:

```python
def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    issues_without_branch: set[tuple[str, int]] | None = None,  # NEW
) -> None:
```

---

## HOW

### Integration Points

1. Import `status_requires_linked_branch` from `.issues`
2. For sessions: caller must compute and pass `skip_reason` (or compute inside)
3. For eligible issues: use `issues_without_branch` set to determine display
4. The calling code (`orchestrator.py` or CLI) builds `issues_without_branch` set

### Design Decision

Rather than making API calls inside `display_status_table()`, the caller provides the set of issues that lack branches. This keeps the display function pure and testable.

---

## ALGORITHM

```python
# For eligible issues section in display_status_table():
for repo_name, issue in eligible_issues:
    if (repo_name, issue["number"]) in session_keys:
        continue  # Already has session
    
    status = get_issue_status(issue)
    
    # Check if issue needs branch but doesn't have one
    # Must check BOTH: status requires branch AND issue lacks one
    needs_branch = (
        status_requires_linked_branch(status)
        and issues_without_branch is not None 
        and (repo_name, issue["number"]) in issues_without_branch
    )
    
    if needs_branch:
        action = "→ Needs branch"
    else:
        action = "→ Create and start"
    
    # Print row with action
```

---

## DATA

### New Indicators

| Condition | Indicator | Location |
|-----------|-----------|----------|
| Session at status-04/07, no branch | `!! No branch` | via `skip_reason` |
| Session at status-04/07, dirty | `!! Dirty` | via `skip_reason` |
| Session git error | `!! Git error` | via `skip_reason` |
| Eligible issue at status-04/07, no branch | `→ Needs branch` | direct |
| Eligible issue, ready to start | `→ Create and start` | existing |

### `issues_without_branch` Set

- Set of `(repo_full_name, issue_number)` tuples
- Populated by caller when processing eligible issues
- Used only for display purposes

---

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_status_display.py`

Add new test class:

```python
class TestDisplayStatusTableBranchIndicators:
    """Tests for branch-related indicators in status table."""

    def test_eligible_issue_without_branch_shows_needs_branch(
        self, capsys, mocker: MockerFixture
    ) -> None:
        """Eligible issue without linked branch shows '→ Needs branch'."""
        mock_issue: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
        }
        
        eligible_issues = [("owner/repo", mock_issue)]
        issues_without_branch = {("owner/repo", 123)}
        
        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            issues_without_branch=issues_without_branch,
        )
        
        captured = capsys.readouterr()
        assert "→ Needs branch" in captured.out
        assert "#123" in captured.out

    def test_eligible_issue_with_branch_shows_create_and_start(
        self, capsys, mocker: MockerFixture
    ) -> None:
        """Eligible issue with linked branch shows '→ Create and start'."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Test Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
        }
        
        eligible_issues = [("owner/repo", mock_issue)]
        issues_without_branch: set[tuple[str, int]] = set()  # Has branch
        
        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            issues_without_branch=issues_without_branch,
        )
        
        captured = capsys.readouterr()
        assert "→ Create and start" in captured.out
        assert "#456" in captured.out

    def test_status_01_without_branch_shows_create_and_start(
        self, capsys, mocker: MockerFixture
    ) -> None:
        """Status-01 issue without branch still shows '→ Create and start'."""
        mock_issue: IssueData = {
            "number": 789,
            "title": "Test Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
        }
        
        eligible_issues = [("owner/repo", mock_issue)]
        # Even if in issues_without_branch, status-01 doesn't require branch
        issues_without_branch = {("owner/repo", 789)}
        
        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            issues_without_branch=issues_without_branch,
        )
        
        captured = capsys.readouterr()
        # Should show Create and start, not Needs branch (status-01 allows main)
        assert "→ Create and start" in captured.out

    def test_session_with_skip_reason_shows_indicator(
        self, capsys, mocker: MockerFixture
    ) -> None:
        """Session with skip_reason shows appropriate indicator."""
        # This tests the integration with get_next_action
        # Mock the necessary functions
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            return_value=False,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            return_value=False,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.status.is_session_stale",
            return_value=False,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            return_value=False,
        )
        
        # Test get_next_action directly with skip_reason
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="No branch",
        )
        
        assert result == "!! No branch"

    def test_none_issues_without_branch_uses_default_behavior(
        self, capsys, mocker: MockerFixture
    ) -> None:
        """None issues_without_branch uses default '→ Create and start'."""
        mock_issue: IssueData = {
            "number": 111,
            "title": "Test Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
        }
        
        eligible_issues = [("owner/repo", mock_issue)]
        
        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            issues_without_branch=None,  # Not provided
        )
        
        captured = capsys.readouterr()
        # Default behavior when branch info not available
        assert "→ Create and start" in captured.out
```

---

## ADDITIONAL CHANGES

### Refactor CLI to use `display_status_table()`

The function `execute_coordinator_vscodeclaude_status()` in `src/mcp_coder/cli/commands/coordinator/commands.py` currently has inline table rendering using `tabulate`. This should be refactored to call `display_status_table()` from `status.py` instead.

**Why refactor:** Better separation of concerns - display logic belongs in the workflows layer, not the CLI layer.

### Build `issues_without_branch` Set in Caller

The code that calls `display_status_table()` needs to build the `issues_without_branch` set:

```python
# In execute_coordinator_vscodeclaude_status() after refactoring:
issues_without_branch: set[tuple[str, int]] = set()

for repo_name, issue in eligible_issues:
    status = get_issue_status(issue)
    if status_requires_linked_branch(status):
        try:
            branch = get_linked_branch_for_issue(branch_manager, issue["number"])
            if branch is None:
                issues_without_branch.add((repo_full_name, issue["number"]))
        except ValueError:
            # Multiple branches - also add to set (will show as needs attention)
            issues_without_branch.add((repo_full_name, issue["number"]))

display_status_table(
    sessions=sessions,
    eligible_issues=eligible_issues,
    issues_without_branch=issues_without_branch,
)
```

---

## VERIFICATION

After implementation, run:

```bash
pytest tests/workflows/vscodeclaude/test_status_display.py::TestDisplayStatusTableBranchIndicators -v
pytest tests/workflows/vscodeclaude/test_next_action.py -v
```

All tests should pass.
