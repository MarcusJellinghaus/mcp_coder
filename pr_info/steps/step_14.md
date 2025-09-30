# Step 14: Apply Decorator to LabelsManager Methods

## Objective
Apply `_handle_github_errors` decorator to all 5 methods in `LabelsManager`, removing bare `Exception` catches.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/labels_manager.py`
- **Methods**: 5 public methods (create_label, get_label, get_labels, update_label, delete_label)

## WHAT
Transform error handling:
```python
# BEFORE
@log_function_call
def create_label(...) -> LabelData:
    try:
        ...
    except GithubException as e:
        logger.error("GitHub API error creating label: %s", e)
        return cast(LabelData, {})
    except Exception as e:  # REMOVE THIS BLOCK
        logger.error("Unexpected error creating label: %s", e)
        return cast(LabelData, {})

# AFTER
@log_function_call
@_handle_github_errors(lambda: cast(LabelData, {}))
def create_label(...) -> LabelData:
    try:
        ...
    except GithubException as e:
        logger.error("GitHub API error creating label: %s", e)
        return cast(LabelData, {})
```

## HOW
- Import decorator from base_manager
- Add decorator to all 5 methods
- Remove bare `except Exception` blocks
- Keep GithubException handling unchanged

## ALGORITHM
```
1. For each of 5 methods in LabelsManager:
2. Add @_handle_github_errors decorator with appropriate factory
3. Remove bare Exception catch block
4. Keep GithubException handling (custom error messages)
5. Verify tests still pass
```

## DATA
```python
# Methods and their empty return factories
create_label: lambda: cast(LabelData, {})
get_label: lambda: cast(LabelData, {})
update_label: lambda: cast(LabelData, {})
get_labels: lambda: []
delete_label: lambda: False
```

## LLM Prompt
```
Based on Step 11, implement Step 14: Apply Decorator to LabelsManager Methods.

Apply the `_handle_github_errors` decorator to all 5 methods in labels_manager.py:
1. create_label
2. get_label
3. get_labels
4. update_label
5. delete_label

Requirements:
- Add decorator below @log_function_call
- Remove bare `except Exception` blocks
- Keep GithubException handling unchanged
- Use appropriate empty return factory for each method

Run tests to verify all LabelsManager tests pass.
```
