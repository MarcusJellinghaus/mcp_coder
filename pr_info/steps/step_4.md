# Step 4: Modify `process_eligible_issues()` for Branch-Aware Launch

## LLM Prompt

```
Implement Step 4 of Issue #422 (see pr_info/steps/summary.md for full context).

Modify `process_eligible_issues()` in orchestrator.py to enforce linked branch requirements.
For status-04/07 without linked branch, skip the issue instead of falling back to main.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | MODIFY function |
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | ADD tests |

---

## WHAT

### Modified Logic in `process_eligible_issues()`

Current code (around line 305):
```python
for issue in issues_to_start[:available_slots]:
    try:
        branch_name = get_linked_branch_for_issue(branch_manager, issue["number"])
        session = prepare_and_launch_session(...)
```

New code:
```python
for issue in issues_to_start[:available_slots]:
    try:
        status = get_issue_status(issue)
        branch_name = get_linked_branch_for_issue(branch_manager, issue["number"])
        
        # Check if status requires linked branch
        if status_requires_linked_branch(status) and branch_name is None:
            logger.error(
                "Issue #%d at %s has no linked branch - skipping",
                issue["number"],
                status,
            )
            continue
        
        session = prepare_and_launch_session(...)
```

---

## HOW

### Integration Points

1. Import `status_requires_linked_branch` from `.issues` (add to existing import)
2. Add check before `prepare_and_launch_session()` call
3. Intervention sessions use same check (the `is_intervention` flag doesn't change branch rules)

---

## ALGORITHM

```python
# Inside the for loop in process_eligible_issues():
status = get_issue_status(issue)
branch_name = get_linked_branch_for_issue(branch_manager, issue["number"])

if status_requires_linked_branch(status) and branch_name is None:
    logger.error("Issue #%d at %s has no linked branch - skipping", 
                 issue["number"], status)
    continue  # Skip to next issue

# Continue with existing launch logic
session = prepare_and_launch_session(...)
```

---

## DATA

### Behavior Matrix

| Status | Linked Branch | Action |
|--------|---------------|--------|
| `status-01:created` | `None` | Launch on `main` |
| `status-01:created` | `"feat-123"` | Launch on `feat-123` |
| `status-04:plan-review` | `None` | **Skip** (log error) |
| `status-04:plan-review` | `"feat-123"` | Launch on `feat-123` |
| `status-07:code-review` | `None` | **Skip** (log error) |
| `status-07:code-review` | `"feat-456"` | Launch on `feat-456` |

---

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_orchestrator_launch.py`

Add new test class:

```python
class TestProcessEligibleIssuesBranchRequirement:
    """Tests for branch requirement enforcement in process_eligible_issues()."""

    def test_status_01_without_branch_launches_on_main(
        self, mocker: MockerFixture
    ) -> None:
        """status-01 without linked branch launches session on main."""
        # Setup mocks
        mock_issue: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/123",
        }
        
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_all_cached_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._filter_eligible_vscodeclaude_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value=None,  # No linked branch
        )
        mock_launch = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.prepare_and_launch_session"
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_session_for_issue",
            return_value=None,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_active_session_count",
            return_value=0,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_github_username",
            return_value="testuser",
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_repo_vscodeclaude_config",
            return_value={},
        )
        
        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
        )
        
        # Session should be launched with branch_name=None (defaults to main)
        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] is None

    def test_status_04_without_branch_skips_issue(
        self, mocker: MockerFixture, caplog
    ) -> None:
        """status-04 without linked branch skips issue and logs error."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
        }
        
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_all_cached_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._filter_eligible_vscodeclaude_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value=None,  # No linked branch
        )
        mock_launch = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.prepare_and_launch_session"
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_session_for_issue",
            return_value=None,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_active_session_count",
            return_value=0,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_github_username",
            return_value="testuser",
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_repo_vscodeclaude_config",
            return_value={},
        )
        
        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
            )
        
        # Session should NOT be launched
        mock_launch.assert_not_called()
        # Error should be logged
        assert "no linked branch" in caplog.text.lower()
        assert "#456" in caplog.text
        # Empty result
        assert result == []

    def test_status_07_without_branch_skips_issue(
        self, mocker: MockerFixture, caplog
    ) -> None:
        """status-07 without linked branch skips issue."""
        mock_issue: IssueData = {
            "number": 789,
            "title": "Code Review Issue",
            "labels": ["status-07:code-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/789",
        }
        
        # Similar setup as above...
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_all_cached_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._filter_eligible_vscodeclaude_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value=None,
        )
        mock_launch = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.prepare_and_launch_session"
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_session_for_issue",
            return_value=None,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_active_session_count",
            return_value=0,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_github_username",
            return_value="testuser",
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_repo_vscodeclaude_config",
            return_value={},
        )
        
        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
            )
        
        mock_launch.assert_not_called()
        assert result == []

    def test_status_04_with_branch_launches_session(
        self, mocker: MockerFixture
    ) -> None:
        """status-04 with linked branch launches session normally."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
        }
        
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_all_cached_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._filter_eligible_vscodeclaude_issues",
            return_value=[mock_issue],
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value="feat-456",  # Has linked branch
        )
        mock_launch = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.prepare_and_launch_session"
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_session_for_issue",
            return_value=None,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_active_session_count",
            return_value=0,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_github_username",
            return_value="testuser",
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_repo_vscodeclaude_config",
            return_value={},
        )
        
        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
        )
        
        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] == "feat-456"
```

---

## VERIFICATION

After implementation, run:

```bash
pytest tests/workflows/vscodeclaude/test_orchestrator_launch.py::TestProcessEligibleIssuesBranchRequirement -v
```

All 4 tests should pass.
