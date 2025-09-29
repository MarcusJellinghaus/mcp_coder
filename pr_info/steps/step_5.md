# Step 5: Repository Labels & Add Labels Operations

## Objective
Implement repository labels and add labels operations: get_available_labels, add_labels, with unit tests.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class

## WHAT
Repository labels and add labels operations:
```python
@log_function_call
def get_available_labels(self) -> List[LabelData]: ...

@log_function_call
def add_labels(self, issue_number: int, *labels: str) -> IssueData: ...
```

## HOW
- Use @log_function_call decorator consistently
- Follow hybrid error handling (raise for auth/permission errors, empty dict/list for others)
- Use *args pattern for variable label arguments
- Convert GitHub objects to LabelData/IssueData dictionaries

## ALGORITHM
```
1. For get_available_labels: Get repository labels and convert to LabelData
2. For add_labels: Validate issue_number and labels, get repository using inherited _get_repository(), add to issue
3. Call GitHub API methods (get_labels, add_to_labels)
4. Convert GitHub objects to structured dictionary formats
5. Return structured data or empty dict/list on non-auth errors
```

## DATA
```python
# get_available_labels returns
List[LabelData] or [] on error

# add_labels returns
IssueData or {} on error

# LabelData structure
{
    "name": str,
    "color": str, 
    "description": Optional[str]
}
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 5: Repository Labels & Add Labels Operations.

Add two methods to the existing IssueManager class: get_available_labels, add_labels.

Requirements:
- Follow the same patterns as existing methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Use *args pattern for label arguments
- Convert repository labels to LabelData dictionaries in get_available_labels
- Return updated IssueData after add_labels operation
- Use hybrid error handling: raise exceptions for auth/permission errors, return empty dict/list for other errors

After implementation, add unit tests to tests/utils/test_issue_manager.py:
- Test both methods with mocked GitHub API calls
- Use KISS approach: essential coverage only
- Test success scenarios and basic error handling
- Test *args pattern for add_labels

Focus only on these 2 label operations and their unit tests.
```
