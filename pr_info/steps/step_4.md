# Step 4: Implement Label CRUD Methods

## Context
Implement the four core CRUD methods to make Step 3 integration tests pass. Keep it simple - only essential operations.

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
def update_label(self, name: str, new_name: str = "", color: str = "", description: str = "") -> LabelData

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
1. Validate: name using _validate_label_name()
2. Normalize: Strip '#' from color if present (color.lstrip('#'))
3. Validate: normalized color using _validate_color()
4. Get: Repository object via _parse_and_get_repo()
5. Try Create: Label using repo.create_label(name, normalized_color, description)
6. If Exists: Catch GithubException (422 status), get existing label, log debug message
7. Return: LabelData dict with created/existing label info (empty dict on error)
```

### update_label() Logic
```
1. Validate: name using _validate_label_name()
2. Validate: color if provided using _validate_color()
3. Get: Repository object via _parse_and_get_repo()
4. Get: Label object using repo.get_label(name)
5. Update: Label using label.edit(new_name, color, description)
   - Only update fields that are provided (non-empty)
6. Return: LabelData dict with updated label info (empty dict on error)
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
- `update_label()`: `LabelData` (empty dict `{}` on error)
- `delete_label()`: `bool` (False on error)

### Error Handling
```python
try:
    # Try to create label
    label = repo.create_label(name, color, description)
except GithubException as e:
    if e.status == 422:  # Label already exists
        logger.debug(f"Label '{name}' already exists, returning existing label")
        # Get and return existing label
        return self._get_existing_label(name)
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
1. Open labels_manager.py and add four methods to LabelsManager class
2. Implement get_labels() following pattern from pr_manager.list_pull_requests()
3. Implement create_label() with validation and idempotent behavior
4. Implement update_label() with optional parameters (new_name, color, description)
5. Implement delete_label() with validation
6. Use @log_function_call decorator on all methods
7. Handle GithubException gracefully (log and return empty/False)

Implementation notes:
- PyGithub API: repo.get_labels(), repo.create_label(), label.edit(), label.delete()
- Normalize color by stripping '#' prefix before validation and API calls
- Validate inputs before API calls (name and normalized color)
- **Idempotent create**: If label exists (422 status), get and return existing label with debug log
- **Partial updates**: update_label() only changes provided fields (non-empty strings)
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
- **Idempotent create_label()**: Returns existing label if already exists (422 status code)
- Use logger.debug() for "label already exists" case, logger.error() for real errors
- Follow PullRequestManager error handling exactly
- Always log errors before returning empty/False
- Cast return types to match TypedDict (use `cast()` if needed)
