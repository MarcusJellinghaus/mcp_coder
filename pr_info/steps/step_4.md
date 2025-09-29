# Step 4: Label Management Operations

## Objective
Implement label management methods for issues: add_labels, remove_labels, set_labels, get_available_labels.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class

## WHAT
Label management operations:
```python
@log_function_call
def add_labels(self, issue_number: int, *labels: str) -> IssueData: ...

@log_function_call
def remove_labels(self, issue_number: int, *labels: str) -> IssueData: ...

@log_function_call
def set_labels(self, issue_number: int, *labels: str) -> IssueData: ...

@log_function_call
def get_available_labels(self) -> List[LabelData]: ...
```

## HOW
- Use @log_function_call decorator consistently
- Follow same error handling patterns (return empty dict/list on error)
- Use *args pattern for variable label arguments (same as original proposal)
- Return updated IssueData after label operations

## ALGORITHM
```
1. Validate issue_number and labels input
2. Get repository and issue using existing methods
3. Call GitHub API label methods (add_to_labels, remove_from_labels, set_labels)
4. For get_available_labels: get repository labels and convert to LabelData
5. Return updated issue data or empty dict/list on error
```

## DATA
```python
# add_labels, remove_labels, set_labels return
IssueData or {} on error

# get_available_labels returns
List[LabelData] or [] on error

# LabelData structure
{
    "name": str,
    "color": str, 
    "description": Optional[str]
}
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 4: Label Management Operations.

Add four methods to the existing IssueManager class: add_labels, remove_labels, set_labels, get_available_labels.

Requirements:
- Follow the same patterns as existing methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Use *args pattern for label arguments (matching the original proposal signature)
- Return updated IssueData after label operations (get fresh issue data)
- Convert repository labels to LabelData dictionaries in get_available_labels
- Include comprehensive input validation and error handling

Focus only on these 4 label management operations.
```
