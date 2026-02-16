# Step 1: Create Test Suite Foundation

## Objective
Create comprehensive unit tests for the new `get_branch_with_pr_fallback()` method following TDD principles. Write **failing tests first** before any implementation.

**Test Structure:** Use hybrid approach - parametrize very similar tests (e.g., single draft vs open PR) while keeping complex scenarios separate for clarity.

---

## WHERE: File Location
**Create new file:**
```
tests/utils/github_operations/issues/test_branch_resolution.py
```

**Why this location?**
- Follows existing test structure for `IssueBranchManager`
- Lives alongside `test_issue_branch_manager.py`
- Clear separation of new functionality tests

---

## WHAT: Test Functions

### Test Class Structure
```python
class TestGetBranchWithPRFallback:
    """Test suite for IssueBranchManager.get_branch_with_pr_fallback()."""
    
    @pytest.fixture
    def mock_manager(self) -> IssueBranchManager:
        """Create mocked IssueBranchManager for testing."""
    
    # Primary path tests
    def test_linked_branch_found_returns_branch_name(self, mock_manager):
        """Test branch found via linkedBranches (primary path)."""
    
    # Fallback path tests
    def test_no_linked_branch_single_draft_pr_returns_branch(self, mock_manager):
        """Test fallback: no linkedBranches, single draft PR found."""
    
    def test_no_linked_branch_single_open_pr_returns_branch(self, mock_manager):
        """Test fallback: no linkedBranches, single open PR found."""
    
    # Error cases
    def test_no_linked_branch_multiple_prs_returns_none(self, mock_manager):
        """Test multiple PRs found returns None with warning."""
    
    def test_no_linked_branch_no_prs_returns_none(self, mock_manager):
        """Test no linkedBranches and no PRs returns None."""
    
    def test_invalid_issue_number_returns_none(self, mock_manager):
        """Test invalid issue numbers return None."""
    
    def test_graphql_error_returns_none(self, mock_manager):
        """Test GraphQL errors handled by decorator return None."""
    
    def test_repository_not_found_returns_none(self, mock_manager):
        """Test repository access failure returns None."""
```

---

## HOW: Integration Points

### 1. Imports Required
```python
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.utils.github_operations.issues import IssueBranchManager
```

### 2. Mock Manager Fixture Pattern
Follow existing pattern from `test_issue_branch_manager.py`:
```python
@pytest.fixture
def mock_manager(self) -> IssueBranchManager:
    """Create a mock IssueBranchManager for testing."""
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.is_dir.return_value = True

    with (
        patch("mcp_coder.utils.git_operations.is_git_repository", return_value=True),
        patch(
            "mcp_coder.utils.github_operations.base_manager.user_config.get_config_values",
            return_value={("github", "token"): "fake_token"},
        ),
        patch("mcp_coder.utils.github_operations.base_manager.Github"),
    ):
        manager = IssueBranchManager(mock_path)
        return manager
```

### 3. Mock GraphQL Responses
Create mock responses for both scenarios:

**linkedBranches Response (Primary Path):**
```python
# Returns branch via get_linked_branches()
# Mock get_linked_branches to return ["123-feature-branch"]
```

**Timeline PR Response (Fallback):**
```python
timeline_response = {
    "data": {
        "repository": {
            "issue": {
                "timelineItems": {
                    "nodes": [
                        {
                            "__typename": "CrossReferencedEvent",
                            "source": {
                                "number": 42,
                                "state": "OPEN",
                                "isDraft": True,
                                "headRefName": "123-feature-branch"
                            }
                        }
                    ]
                }
            }
        }
    }
}
```

---

## ALGORITHM: Test Logic Pseudocode

### Test 1: Primary Path (linkedBranches)
```
1. Mock get_linked_branches() → return ["123-feature-branch"]
2. Call get_branch_with_pr_fallback(123, "owner", "repo")
3. Assert result == "123-feature-branch"
4. Verify GraphQL timeline query NOT called (short-circuit)
```

### Test 2: Fallback - Single Draft PR
```
1. Mock get_linked_branches() → return []
2. Mock GraphQL timeline query → return single draft PR with headRefName
3. Call get_branch_with_pr_fallback(123, "owner", "repo")
4. Assert result == "123-feature-branch"
5. Verify GraphQL timeline query WAS called
```

### Test 3: Multiple PRs Error Case
```
1. Mock get_linked_branches() → return []
2. Mock GraphQL timeline query → return TWO draft/open PRs
3. Call get_branch_with_pr_fallback(123, "owner", "repo")
4. Assert result == None
5. Verify warning logged with PR numbers
```

### Test 4: No PRs Found
```
1. Mock get_linked_branches() → return []
2. Mock GraphQL timeline query → return empty nodes
3. Call get_branch_with_pr_fallback(123, "owner", "repo")
4. Assert result == None
```

### Test 5: Invalid Issue Number
```
1. Call get_branch_with_pr_fallback(-1, "owner", "repo")
2. Assert result == None
3. Verify error logged
```

---

## DATA: Expected Inputs/Outputs

### Method Signature (Not Yet Implemented)
```python
def get_branch_with_pr_fallback(
    self,
    issue_number: int,
    repo_owner: str,
    repo_name: str
) -> Optional[str]:
```

### Test Data Scenarios

| Scenario | linkedBranches | Timeline PRs | Expected Return | Notes |
|----------|---------------|--------------|-----------------|-------|
| Primary path | `["123-branch"]` | N/A | `"123-branch"` | Fast path |
| Single draft PR | `[]` | 1 draft PR | `"123-branch"` | Fallback |
| Single open PR | `[]` | 1 open PR | `"123-branch"` | Fallback |
| Multiple PRs | `[]` | 2+ PRs | `None` | Ambiguous |
| No PRs | `[]` | 0 PRs | `None` | Not found |
| Invalid issue | N/A | N/A | `None` | Error |
| API error | N/A | Exception | `None` | Decorator |

---

## Test Implementation Template

### Example Test: Primary Path
```python
def test_linked_branch_found_returns_branch_name(
    self, mock_manager: IssueBranchManager
) -> None:
    """Test branch found via linkedBranches (primary path).
    
    When linkedBranches returns a branch, should return immediately
    without querying PR timeline.
    """
    # Setup: Mock repository
    mock_repo = Mock()
    mock_repo.owner.login = "test-owner"
    mock_repo.name = "test-repo"
    mock_manager._repository = mock_repo

    # Setup: Mock get_linked_branches to return branch
    mock_manager.get_linked_branches = Mock(
        return_value=["123-feature-branch"]
    )

    # Setup: Mock GraphQL client (should NOT be called)
    mock_manager._github_client._Github__requester = Mock()
    mock_graphql_query = Mock()
    mock_manager._github_client._Github__requester.graphql_query = (
        mock_graphql_query
    )

    # Execute
    result = mock_manager.get_branch_with_pr_fallback(
        issue_number=123,
        repo_owner="test-owner",
        repo_name="test-repo"
    )

    # Verify
    assert result == "123-feature-branch"
    mock_manager.get_linked_branches.assert_called_once_with(123)
    # GraphQL should NOT be called (short-circuit)
    mock_graphql_query.assert_not_called()
```

### Example Test: Fallback - Single Draft PR
```python
def test_no_linked_branch_single_draft_pr_returns_branch(
    self, mock_manager: IssueBranchManager
) -> None:
    """Test fallback: no linkedBranches, single draft PR found."""
    # Setup: Mock repository
    mock_repo = Mock()
    mock_repo.owner.login = "test-owner"
    mock_repo.name = "test-repo"
    mock_manager._repository = mock_repo

    # Setup: Mock get_linked_branches to return empty
    mock_manager.get_linked_branches = Mock(return_value=[])

    # Setup: Mock GraphQL timeline response with single draft PR
    timeline_response = {
        "data": {
            "repository": {
                "issue": {
                    "timelineItems": {
                        "nodes": [
                            {
                                "__typename": "CrossReferencedEvent",
                                "source": {
                                    "number": 42,
                                    "state": "OPEN",
                                    "isDraft": True,
                                    "headRefName": "123-feature-branch"
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
    
    mock_manager._github_client._Github__requester = Mock()
    mock_manager._github_client._Github__requester.graphql_query = Mock(
        return_value=({}, timeline_response)
    )

    # Execute
    result = mock_manager.get_branch_with_pr_fallback(
        issue_number=123,
        repo_owner="test-owner",
        repo_name="test-repo"
    )

    # Verify
    assert result == "123-feature-branch"
    mock_manager.get_linked_branches.assert_called_once_with(123)
    mock_manager._github_client._Github__requester.graphql_query.assert_called_once()
```

---

## LLM Prompt for Implementation

```
I need to implement Step 1 of the branch resolution feature.

CONTEXT:
- Read pr_info/steps/summary.md for full architectural context
- We're following TDD: write tests FIRST, implementation comes in Step 2

TASK:
Create tests/utils/github_operations/issues/test_branch_resolution.py with comprehensive unit tests for the get_branch_with_pr_fallback() method that doesn't exist yet.

REQUIREMENTS:
1. Follow the test patterns from tests/utils/github_operations/test_issue_branch_manager.py
2. Create a test class TestGetBranchWithPRFallback
3. Include pytest fixture for mock_manager (copy pattern from existing tests)
4. Write 8 test functions covering all scenarios in the step_1.md file:
   - Primary path (linkedBranches found)
   - Fallback with single draft PR
   - Fallback with single open PR  
   - Multiple PRs (should return None)
   - No PRs found (should return None)
   - Invalid issue number
   - GraphQL error handling
   - Repository not found

5. Use Mock/patch for all external dependencies
6. Mock GraphQL responses following the timeline response structure
7. Each test should assert return value and verify mock calls

DELIVERABLE:
- Single test file with ~280 lines (using parametrization for similar tests)
- All tests should FAIL initially (method doesn't exist)
- Clear test names and docstrings
- Follow existing code style and patterns
- Use @pytest.mark.parametrize for similar scenarios (draft vs open PR)

The method signature to test:
def get_branch_with_pr_fallback(self, issue_number: int, repo_owner: str, repo_name: str) -> Optional[str]
```

---

## Expected Outcome
- ✅ Test file created with all 8 test scenarios (some parametrized)
- ❌ All tests fail (method not implemented yet)
- ✅ Test structure follows existing patterns
- ✅ Mock setup reusable for all tests
- ✅ Clear documentation of expected behavior
- ✅ Parametrized tests reduce duplication (~280 lines vs ~350)

**Next Step:** Step 2 will implement the actual method to make these tests pass.
