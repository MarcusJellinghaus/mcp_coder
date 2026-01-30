# Step 2: Extend `IssueData` and Populate in `get_issue()` / `list_issues()`

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 2.

Extend the IssueData TypedDict and populate base_branch in get_issue() and list_issues():
1. First write/update the unit tests
2. Then modify IssueData and the methods
3. Run tests to verify

Follow the specifications in this step file exactly.
```

---

## Overview

Extend the `IssueData` TypedDict to include the optional `base_branch` field and populate it when retrieving issues.

---

## WHERE: File Paths

| File | Action |
|------|--------|
| `src/mcp_coder/utils/github_operations/issue_manager.py` | Extend `IssueData`, modify `get_issue()`, `list_issues()` |
| `tests/utils/github_operations/test_issue_manager.py` | Add/update tests for `base_branch` in issue data |

---

## WHAT: TypedDict Extension

### Current IssueData (before)

```python
class IssueData(TypedDict):
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    assignees: List[str]
    user: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    url: str
    locked: bool
```

### New IssueData (after)

```python
from typing import NotRequired  # Add to imports

class IssueData(TypedDict):
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    assignees: List[str]
    user: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    url: str
    locked: bool
    base_branch: NotRequired[Optional[str]]  # NEW - parsed from body
```

---

## HOW: Integration Points

### Imports to Add

```python
from typing import List, Optional, TypedDict, NotRequired  # Add NotRequired
```

### Methods to Modify

1. **`get_issue()`** - Add `base_branch` to returned `IssueData`
2. **`list_issues()`** - Add `base_branch` to each `IssueData` in the list
3. **`create_issue()`** - Add `base_branch` to returned `IssueData` (for consistency)

---

## ALGORITHM: Changes to `get_issue()`

Location: Around line 520 in `issue_manager.py`

```python
# In get_issue() method, before the final return statement:

# Parse base_branch from body
body = github_issue.body or ""
try:
    base_branch = _parse_base_branch(body)
except ValueError as e:
    logger.warning(f"Issue #{issue_number} has malformed base branch: {e}")
    base_branch = None

# Add to returned IssueData:
return IssueData(
    number=github_issue.number,
    title=github_issue.title,
    body=github_issue.body or "",
    # ... existing fields ...
    locked=github_issue.locked,
    base_branch=base_branch,  # NEW
)
```

---

## ALGORITHM: Changes to `list_issues()`

Location: Around line 580 in `issue_manager.py`

```python
# In list_issues() method, inside the for loop:

body = issue.body or ""
try:
    base_branch = _parse_base_branch(body)
except ValueError as e:
    logger.warning(f"Issue #{issue.number} has malformed base branch: {e}")
    base_branch = None

issue_data = IssueData(
    number=issue.number,
    # ... existing fields ...
    locked=issue.locked,
    base_branch=base_branch,  # NEW
)
```

---

## DATA: Test Cases

### Test Updates for `get_issue()`

```python
class TestGetIssueBaseBranch:
    """Tests for base_branch field in get_issue()."""

    def test_get_issue_with_base_branch(self, mock_github_client, mock_repo):
        """Issue with valid base branch returns it in IssueData."""
        # Setup mock issue with base branch in body
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "### Base Branch\n\nfeature/v2\n\n### Description\n\nContent"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.user = None
        mock_issue.created_at = None
        mock_issue.updated_at = None
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.locked = False

        mock_repo.get_issue.return_value = mock_issue

        manager = IssueManager(project_dir=Path("/tmp/test"))
        result = manager.get_issue(123)

        assert result["base_branch"] == "feature/v2"

    def test_get_issue_without_base_branch(self, mock_github_client, mock_repo):
        """Issue without base branch section returns None."""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.body = "### Description\n\nNo base branch here"
        # ... other fields ...

        mock_repo.get_issue.return_value = mock_issue

        manager = IssueManager(project_dir=Path("/tmp/test"))
        result = manager.get_issue(123)

        assert result["base_branch"] is None

    def test_get_issue_with_malformed_base_branch_logs_warning(
        self, mock_github_client, mock_repo, caplog
    ):
        """Issue with multi-line base branch logs warning and returns None."""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.body = "### Base Branch\n\nline1\nline2\n\n### Description"
        # ... other fields ...

        mock_repo.get_issue.return_value = mock_issue

        manager = IssueManager(project_dir=Path("/tmp/test"))
        result = manager.get_issue(123)

        assert result["base_branch"] is None
        assert "malformed base branch" in caplog.text.lower()
```

### Test Updates for `list_issues()`

```python
class TestListIssuesBaseBranch:
    """Tests for base_branch field in list_issues()."""

    def test_list_issues_includes_base_branch(self, mock_github_client, mock_repo):
        """list_issues() includes base_branch in each IssueData."""
        mock_issue1 = Mock()
        mock_issue1.number = 1
        mock_issue1.body = "### Base Branch\n\nmain\n\n### Desc"
        mock_issue1.pull_request = None
        # ... other fields ...

        mock_issue2 = Mock()
        mock_issue2.number = 2
        mock_issue2.body = "### Description\n\nNo base branch"
        mock_issue2.pull_request = None
        # ... other fields ...

        mock_repo.get_issues.return_value = [mock_issue1, mock_issue2]

        manager = IssueManager(project_dir=Path("/tmp/test"))
        results = manager.list_issues()

        assert results[0]["base_branch"] == "main"
        assert results[1]["base_branch"] is None
```

---

## Verification

After implementation, run:

```bash
pytest tests/utils/github_operations/test_issue_manager.py -v -k "base_branch"
```

Expected: All tests pass.

Also run the full test suite to ensure no regressions:

```bash
pytest tests/utils/github_operations/test_issue_manager.py -v
```
