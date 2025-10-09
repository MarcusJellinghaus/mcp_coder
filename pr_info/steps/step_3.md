# Step 3: Create Linked Branch

## LLM Prompt
```
Read pr_info/steps/summary.md for context.

Implement Step 3: Create linked branch with duplicate prevention.
Write tests first, then implement create_remote_branch_for_issue() method.
Use graphql_named_mutation() from PyGithub's requester.
```

## WHERE
**File**: `src/mcp_coder/utils/github_operations/issue_branch_manager.py`  
**Test File**: `tests/utils/github_operations/test_issue_branch_manager.py`

## WHAT

### Method
```python
def create_remote_branch_for_issue(
    self,
    issue_number: int,
    branch_name: Optional[str] = None,
    base_branch: Optional[str] = None
) -> BranchCreationResult:
    """Create and link branch to issue via GraphQL."""
```

### Test Cases
```python
class TestCreateLinkedBranch:
    def test_create_with_auto_name()
    def test_create_with_custom_name()
    def test_create_with_base_branch()
    def test_duplicate_prevention()
    def test_invalid_issue_number()
    def test_issue_not_found()
    def test_permission_error()
```

## HOW

### Decorators
```python
@log_function_call
@_handle_github_errors(
    default_return=BranchCreationResult(
        success=False, branch_name="", error=None, existing_branches=[]
    )
)
```

### GraphQL Mutation
```python
self._github_client._Github__requester.graphql_named_mutation(
    mutation_name="createLinkedBranch",
    mutation_input=input_dict,
    output_schema="linkedBranch { id ref { name target { oid } } }"
)
```

## ALGORITHM

```
1. Check existing linked branches (duplicate prevention)
2. If branch_name not provided, generate using generate_branch_name_from_issue()
3. Get issue.node_id and repo.node_id via PyGithub
4. Get base commit SHA (base_branch or default branch)
5. Execute createLinkedBranch mutation with input
6. Return BranchCreationResult with success/error details
```

## DATA

### GraphQL Mutation Input
```python
{
    "issueId": "I_kwDOABCDEF123",  # issue.node_id
    "repositoryId": "R_kgDOABCDEF",  # repo.node_id
    "oid": "abc123...",              # base commit SHA
    "name": "123-feature-branch"     # optional branch name
}
```

### Return Value
```python
BranchCreationResult(
    success=True,
    branch_name="123-feature-branch",
    error=None,
    existing_branches=[]
)
# Or on duplicate:
BranchCreationResult(
    success=False,
    branch_name="",
    error="Branch already linked",
    existing_branches=["123-feature-branch"]
)
```

### Error Cases
- Duplicate branch → `success=False`, populate `existing_branches`
- Invalid issue → `success=False`, set `error` message
- Permission denied → caught by decorator, returns default
