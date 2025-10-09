# Step 4: Delete Linked Branch

## LLM Prompt
```
Read pr_info/steps/summary.md for context.

Implement Step 4: Delete linked branch (unlink only, doesn't delete Git branch).
Write tests first, then implement delete_linked_branch() method.
Use graphql_named_mutation() for deleteLinkedBranch.
```

## WHERE
**File**: `src/mcp_coder/utils/github_operations/issue_branch_manager.py`  
**Test File**: `tests/utils/github_operations/test_issue_branch_manager.py`

## WHAT

### Method
```python
def delete_linked_branch(
    self,
    issue_number: int,
    branch_name: str
) -> bool:
    """Unlink branch from issue (doesn't delete Git branch)."""
```

### Test Cases
```python
class TestDeleteLinkedBranch:
    def test_successful_unlink()
    def test_branch_not_linked()
    def test_invalid_issue_number()
    def test_empty_branch_name()
    def test_issue_not_found()
```

## HOW

### Decorators
```python
@log_function_call
@_handle_github_errors(default_return=False)
```

### GraphQL Mutation
```python
self._github_client._Github__requester.graphql_named_mutation(
    mutation_name="deleteLinkedBranch",
    mutation_input={"linkedBranchId": linked_branch_id},
    output_schema="clientMutationId"
)
```

## ALGORITHM

```
1. Validate issue_number and branch_name
2. Query linked branches to get linkedBranch.id
3. Find matching branch by name, extract its ID
4. If not found, log warning and return False
5. Execute deleteLinkedBranch mutation with linkedBranchId
6. Return True on success, False on failure
```

## DATA

### GraphQL Query to Get ID
```graphql
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      linkedBranches(first: 100) {
        nodes {
          id
          ref { name }
        }
      }
    }
  }
}
```

### Mutation Input
```python
{
    "linkedBranchId": "LB_kwDOABCDEF123"  # from query above
}
```

### Return Value
- `True` - Successfully unlinked
- `False` - Branch not found or error occurred

### Error Cases
- Branch not in linked list → log, return `False`
- Invalid inputs → log, return `False`
- Permission errors → caught by decorator, return `False`
