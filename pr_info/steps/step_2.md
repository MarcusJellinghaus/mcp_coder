# Step 2: Query Linked Branches

## LLM Prompt
```
Read pr_info/steps/summary.md for context.

Implement Step 2: Query linked branches using GraphQL.
Create tests first, then implement IssueBranchManager class with get_linked_branches() method.
Reference base_manager.py and issue_manager.py for patterns.
```

## WHERE
**File**: `src/mcp_coder/utils/github_operations/issue_branch_manager.py`  
**Test File**: `tests/utils/github_operations/test_issue_branch_manager.py`

## WHAT

### Class and Method
```python
class IssueBranchManager(BaseGitHubManager):
    def get_linked_branches(self, issue_number: int) -> List[str]:
        """Query linked branches for an issue via GraphQL."""
```

### TypedDict and Types (add to module)
```python
from typing import Literal

GraphQLOperation = Literal["query", "createLinkedBranch", "deleteLinkedBranch"]

class BranchCreationResult(TypedDict):
    success: bool
    branch_name: str
    error: Optional[str]
    existing_branches: List[str]
```

### Test Cases
```python
class TestGetLinkedBranches:
    def test_valid_issue_number()
    def test_invalid_issue_number()
    def test_issue_not_found()
    def test_no_linked_branches()
    def test_multiple_linked_branches()
    def test_graphql_error_handling()
```

## HOW

### Integration Points
```python
from .base_manager import BaseGitHubManager, _handle_github_errors
from mcp_coder.utils.log_utils import log_function_call
```

### Decorators
```python
@log_function_call
@_handle_github_errors(default_return=[])
```

### GraphQL Access
```python
self._github_client._Github__requester.graphql_query(
    query=query_string,
    variables=variables_dict
)
```

## ALGORITHM

```
1. Validate issue_number (positive integer)
2. Get repository object via _get_repository()
3. Build GraphQL query for linkedBranches field
4. Execute query with owner, repo, issueNumber variables
5. Parse response: data["repository"]["issue"]["linkedBranches"]["nodes"]
6. Extract branch names from nodes[]["ref"]["name"]
```

## DATA

### GraphQL Query
```graphql
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      linkedBranches(first: 100) {
        nodes {
          ref { name }
        }
      }
    }
  }
}
```

### Return Value
- `List[str]` - Branch names (e.g., `["123-feature-branch", "123-hotfix"]`)
- Empty list `[]` on error or no branches

### Error Handling
- Invalid issue_number → log error, return `[]`
- Issue not found → log warning, return `[]`
- GraphQL errors → caught by decorator, return `[]`
