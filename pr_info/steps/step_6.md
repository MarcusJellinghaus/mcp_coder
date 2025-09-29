# Step 6: Remove & Set Labels Operations

## Objective
Implement remove and set labels operations: remove_labels, set_labels, with unit tests and enhanced integration test.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class
- **Integration Test**: Enhance existing test in `tests/utils/test_issue_manager_integration.py`

## WHAT
Remove and set labels operations:
```python
@log_function_call
def remove_labels(self, issue_number: int, *labels: str) -> IssueData: ...

@log_function_call
def set_labels(self, issue_number: int, *labels: str) -> IssueData: ...
```

## HOW
- Use @log_function_call decorator consistently
- Follow hybrid error handling (raise for auth/permission errors, empty dict for others)
- Use *args pattern for variable label arguments
- Return updated IssueData after label operations

## ALGORITHM
```
1. Validate issue_number and labels input
2. Get repository and issue using existing methods
3. Call GitHub API label methods (remove_from_labels, set_labels)
4. Convert updated issue to IssueData dictionary
5. Return structured data or empty dict on non-auth errors
```

## DATA
```python
# remove_labels, set_labels return
IssueData or {} on error
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 6: Remove & Set Labels Operations.

Add two methods to the existing IssueManager class: remove_labels, set_labels.

Requirements:
- Follow the same patterns as existing methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Use *args pattern for label arguments
- Return updated IssueData after operations (get fresh issue data)
- Use hybrid error handling: raise exceptions for auth/permission errors, return empty dict for other errors

After implementation, add unit tests to tests/utils/test_issue_manager.py:
- Test both methods with mocked GitHub API calls
- Use KISS approach: essential coverage only
- Test *args pattern for both methods

Then enhance the existing integration test in tests/utils/test_issue_manager_integration.py:
- Extend the existing test flow to: create_issue → add_labels → remove_labels → set_labels → close_issue
- Test with real GitHub API using configured test repository
- Ensure integration test fails clearly with exceptions on permission issues

Focus on these 2 operations, their unit tests, and enhancing the integration test.
```
