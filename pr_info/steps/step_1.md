# Step 1: Add `get_closing_issue_numbers()` to PullRequestManager

> **Context**: See `pr_info/steps/summary.md` for full issue context (#776).
> This step adds the GraphQL method that the workflow fallback (step 2) will call.

## WHERE

- **Production**: `src/mcp_coder/utils/github_operations/pr_manager.py`
- **Tests**: `tests/utils/github_operations/test_pr_manager.py`

## WHAT

Add one new method to `PullRequestManager`:

```python
@log_function_call
@_handle_github_errors(default_return=[])
def get_closing_issue_numbers(self, pr_number: int) -> List[int]:
    """Query closing issue references for a PR via GraphQL.

    Args:
        pr_number: Pull request number to query

    Returns:
        List of issue numbers linked as closing references, or empty list on error
    """
```

## HOW

- Decorators: `@log_function_call` + `@_handle_github_errors(default_return=[])` (both already imported in `pr_manager.py`)
- GraphQL access: `self._github_client._Github__requester.graphql_query(...)` — same pattern as `IssueBranchManager.get_linked_branches()` in `branch_manager.py`
- No new imports needed — `List` and `logger` already available

## ALGORITHM

```
1. Validate pr_number (reuse _validate_pr_number)
2. Get repository via _get_repository()
3. Extract owner + repo name
4. Execute GraphQL query for closingIssuesReferences on the PR
5. Parse response: extract issue numbers from nodes
6. Return list of issue numbers
```

## DATA

GraphQL query:
```graphql
query($owner: String!, $repo: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      closingIssuesReferences(first: 10) {
        nodes {
          number
        }
      }
    }
  }
}
```

Return value: `List[int]` — e.g. `[92]` or `[]`

## TESTS

Add to `tests/utils/github_operations/test_pr_manager.py`, in a new test class `TestGetClosingIssueNumbers`:

1. **`test_get_closing_issue_numbers_single_issue`** — GraphQL returns one linked issue → returns `[92]`
2. **`test_get_closing_issue_numbers_multiple_issues`** — GraphQL returns two issues → returns `[92, 55]`
3. **`test_get_closing_issue_numbers_no_issues`** — GraphQL returns empty nodes → returns `[]`
4. **`test_get_closing_issue_numbers_invalid_pr_number`** — pr_number=0 → returns `[]`
5. **`test_get_closing_issue_numbers_pr_not_found`** — GraphQL returns null pullRequest → returns `[]`

Test pattern: mock `_github_client._Github__requester.graphql_query` to return canned responses, same as `test_issue_branch_manager.py` tests.

## LLM PROMPT

```
Implement step 1 of issue #776. See pr_info/steps/summary.md for context and pr_info/steps/step_1.md for details.

Add `get_closing_issue_numbers(pr_number: int) -> List[int]` method to PullRequestManager
in src/mcp_coder/utils/github_operations/pr_manager.py.

Write tests FIRST in tests/utils/github_operations/test_pr_manager.py, then implement the method.
Follow the existing GraphQL pattern from IssueBranchManager.get_linked_branches() in branch_manager.py.
Run all code quality checks after implementation.
```
