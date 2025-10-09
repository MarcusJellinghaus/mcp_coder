# Step 5: Integration Test

## LLM Prompt
```
Read pr_info/steps/summary.md for context.

Implement Step 5: Complete end-to-end integration test.
Create test_issue_branch_manager_integration.py following the pattern from test_issue_manager_integration.py.
Test the full workflow with real GitHub API.
```

## WHERE
**File**: `tests/utils/github_operations/test_issue_branch_manager_integration.py`

## WHAT

### Test Class
```python
@pytest.mark.github_integration
class TestIssueBranchManagerIntegration:
    def test_complete_branch_linking_workflow(
        self,
        issue_branch_manager: IssueBranchManager
    ) -> None:
        """Test full workflow: create issue → link branch → query → unlink → verify."""
```

### Fixture
```python
@pytest.fixture
def issue_branch_manager(
    github_test_setup: "GitHubTestSetup"
) -> Generator[IssueBranchManager, None, None]:
    """Create IssueBranchManager instance for testing."""
```

## HOW

### Integration Points
```python
from mcp_coder.utils.github_operations import (
    IssueManager,
    IssueBranchManager
)
from tests.conftest import GitHubTestSetup, create_github_manager
```

### Test Markers
```python
@pytest.mark.github_integration  # Skip without GitHub config
```

## ALGORITHM

```
1. Create test issue via IssueManager
2. Create linked branch via IssueBranchManager.create_remote_branch_for_issue()
3. Query linked branches, verify presence
4. Attempt duplicate creation, verify prevention
5. Unlink branch via delete_linked_branch()
6. Query again, verify absence
7. Cleanup: close issue via IssueManager
```

## DATA

### Workflow Steps
```python
# 1. Create issue
issue = issue_manager.create_issue(
    title="Integration Test - Branch Linking",
    body="Test issue for branch linking"
)

# 2. Create linked branch
result = branch_manager.create_remote_branch_for_issue(
    issue_number=issue["number"]
)
assert result["success"] is True

# 3. Query branches
branches = branch_manager.get_linked_branches(issue["number"])
assert result["branch_name"] in branches

# 4. Test duplicate prevention (default behavior)
dup_result = branch_manager.create_remote_branch_for_issue(
    issue_number=issue["number"]
)
assert dup_result["success"] is False
assert len(dup_result["existing_branches"]) > 0

# 4b. Test allow_multiple=True
result2 = branch_manager.create_remote_branch_for_issue(
    issue_number=issue["number"],
    branch_name=f"{issue['number']}-second-branch",
    allow_multiple=True
)
assert result2["success"] is True

# 5. Unlink
unlinked = branch_manager.delete_linked_branch(
    issue_number=issue["number"],
    branch_name=result["branch_name"]
)
assert unlinked is True

# 6. Verify absence
branches = branch_manager.get_linked_branches(issue["number"])
assert result["branch_name"] not in branches

# 7. Cleanup Git branches (delete actual branches from repo)
repo = branch_manager._get_repository()
repo.get_git_ref(f"heads/{result['branch_name']}").delete()
repo.get_git_ref(f"heads/{result2['branch_name']}").delete()

# 8. Cleanup issue
issue_manager.close_issue(issue["number"])
```

### Verification Points
- Branch appears in GitHub UI "Development" section
- Duplicate prevention returns existing branches
- Unlink removes association but not Git branch
- All operations handle errors gracefully
