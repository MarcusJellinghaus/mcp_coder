# Step 4: Implement Label CRUD Methods

## Context
Implement the three core CRUD methods to make Step 3 integration tests pass. Keep it simple - only essential operations.

## WHERE

### File to Modify
```
src/mcp_coder/utils/github_operations/labels_manager.py
```

Add methods to existing LabelsManager class.

## WHAT

### Methods to Implement

```python
@log_function_call
def get_labels(self) -> List[LabelData]

@log_function_call
def create_label(self, name: str, color: str, description: str = "") -> LabelData

@log_function_call
def delete_label(self, name: str) -> bool
```

## HOW

### Integration Pattern
- Use `@log_function_call` decorator on all public methods
- Call `_validate_label_name()` and `_validate_color()` before operations
- Call `_parse_and_get_repo()` to get Repository object
- Handle `GithubException` gracefully (log and return empty/False)
- Return structured data (LabelData dict or bool)

## ALGORITHM

### get_labels() Logic
```
1. Get: Repository object via _parse_and_get_repo()
2. Fetch: All labels using repo.get_labels()
3. Convert: Each label to LabelData dict
4. Return: List of LabelData dicts (empty list on error)
```

### create_label() Logic
```
1. Validate: name and color using validation methods
2. Get: Repository object via _parse_and_get_repo()
3. Create: Label using repo.create_label(name, color, description)
4. Return: LabelData dict with created label info (empty dict on error)
```

### delete_label() Logic
```
1. Validate: name using _validate_label_name()
2. Get: Repository object via _parse_and_get_repo()
3. Get: Label object using repo.get_label(name)
4. Delete: Label using label.delete()
5. Return: True on success, False on error
```

## DATA

### LabelData Structure
```python
{
    "name": "bug",
    "color": "FF0000",
    "description": "Something isn't working",
    "url": "https://github.com/owner/repo/labels/bug"
}
```

### Return Values
- `get_labels()`: `List[LabelData]` (empty list `[]` on error)
- `create_label()`: `LabelData` (empty dict `{}` on error)
- `delete_label()`: `bool` (False on error)

### Error Handling
```python
try:
    # GitHub API operation
except GithubException as e:
    logger.error(f"GitHub API error: {e}")
    return {}  # or [] or False
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {}  # or [] or False
```

## LLM Prompt

```
Implement label CRUD methods to make Step 3 integration tests pass.

Context: Read pr_info/steps/summary.md for overview.
Reference: src/mcp_coder/utils/github_operations/pr_manager.py -> PullRequestManager CRUD methods

Tasks:
1. Open labels_manager.py and add three methods to LabelsManager class
2. Implement get_labels() following pattern from pr_manager.list_pull_requests()
3. Implement create_label() with validation, following pr_manager.create_pull_request()
4. Implement delete_label() with validation
5. Use @log_function_call decorator on all methods
6. Handle GithubException gracefully (log and return empty/False)

Implementation notes:
- PyGithub API: repo.get_labels(), repo.create_label(), repo.get_label(name).delete()
- Validate inputs before API calls
- Return structured data: LabelData dict or bool
- Log errors but don't raise exceptions to caller
- Follow exact same error handling pattern as PullRequestManager

Run tests:
1. pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
2. pytest tests/utils/test_github_operations.py::TestLabelsManagerIntegration -v -m github_integration

Expected: All tests PASS (green phase)
```

## Notes

- Keep methods simple - single responsibility
- Reuse validation methods from Step 2
- Follow PullRequestManager error handling exactly
- Always log errors before returning empty/False
- Cast return types to match TypedDict (use `cast()` if needed)
