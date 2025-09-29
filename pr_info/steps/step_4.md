# Step 4: Issue Creation & Lifecycle Operations

## Objective
Implement issue creation and lifecycle operations: create_issue, close_issue, reopen_issue, with unit tests and integration test.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class
- **Integration Test**: `tests/utils/test_issue_manager_integration.py`

## WHAT
Issue creation and lifecycle operations:
```python
@log_function_call
def create_issue(self, title: str, body: str = "", labels: Optional[List[str]] = None) -> IssueData: ...

@log_function_call
def close_issue(self, issue_number: int) -> IssueData: ...

@log_function_call
def reopen_issue(self, issue_number: int) -> IssueData: ...
```

## HOW
- Use @log_function_call decorator consistently
- Follow hybrid error handling (raise for auth/permission errors, empty dict for others)
- Convert GitHub Issue objects to IssueData dictionaries
- Return updated IssueData after operations

## ALGORITHM
```
1. Validate inputs (title, body, issue_number, labels)
2. Get repository using _parse_and_get_repo()
3. Call GitHub API methods (create_issue, edit for close/reopen)
4. Convert GitHub objects to IssueData dictionary format
5. Return structured data or empty dict on non-auth errors
```

## DATA
```python
# create_issue, close_issue, reopen_issue return
IssueData or {} on error
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 4: Issue Creation & Lifecycle Operations.

Add three methods to the existing IssueManager class: create_issue, close_issue, reopen_issue.

Requirements:
- Follow the same patterns as existing methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Use hybrid error handling: raise exceptions for auth/permission errors, return empty dict for other errors
- Return updated IssueData after operations (get fresh issue data)
- Include comprehensive input validation and detailed docstrings

After implementation, add unit tests to tests/utils/test_issue_manager.py:
- Test all three methods with mocked GitHub API calls
- Use KISS approach: essential coverage only
- Test success scenarios and basic error handling

Then create integration test in tests/utils/test_issue_manager_integration.py:
- Create one integration test that uses the configured test repository
- Test flow: create_issue → get_issue → close_issue → reopen_issue
- Use @pytest.mark.github_integration marker
- Integration test should fail clearly with exceptions on permission issues

Focus on these 3 operations, their unit tests, and the initial integration test.
```
