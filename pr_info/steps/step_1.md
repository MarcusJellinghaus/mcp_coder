# Step 1: Add `format_status_labels()` and unify label formatting

> **Reference**: See `pr_info/steps/summary.md` for full context on issue #595.

## Goal

Extract a `format_status_labels()` function and refactor existing code to use it. This step changes no external behavior — same output, same signatures (except `validate_status_label`), same tests passing.

## WHERE

- `src/mcp_coder/cli/commands/set_status.py` — add function, refactor two callers
- `tests/cli/commands/test_set_status.py` — add tests for `format_status_labels`, update `validate_status_label` tests

## WHAT

### New function

```python
def format_status_labels(labels_config: dict) -> str:
    """Format available status labels as an aligned table.

    Args:
        labels_config: Loaded labels config dict with 'workflow_labels' key.

    Returns:
        Formatted string with label names and descriptions.
    """
```

### Changed signature

```python
# WAS:
def validate_status_label(label: str, valid_labels: set[str]) -> Tuple[bool, Optional[str]]:

# NOW:
def validate_status_label(label: str, labels_config: dict) -> Tuple[bool, Optional[str]]:
```

## HOW

- `build_set_status_epilog()`: Replace inline label formatting loop with call to `format_status_labels()`. Remove "Examples" section.
- `validate_status_label()`: Extract label names from `labels_config["workflow_labels"]` internally. Use `format_status_labels()` for the error message.
- `execute_set_status()`: Pass `labels_config` (already loaded) to `validate_status_label()` instead of `status_labels` set.

## ALGORITHM — `format_status_labels`

```
labels = labels_config["workflow_labels"]
max_width = max(len(label["name"]) for label in labels) + 2
lines = ["Available status labels:"]
for label in labels:
    lines.append(f"  {label['name']:<{max_width}} {label['description']}")
return "\n".join(lines)
```

## DATA

- **Input**: `labels_config: dict` — structure: `{"workflow_labels": [{"name": str, "description": str, ...}, ...]}`
- **Output**: `str` — multi-line formatted table, e.g.:
  ```
  Available status labels:
    status-01:created              Issue created and available for planning
    status-02:awaiting-planning    Waiting for planning to start
    ...
  ```

## Tests (TDD)

### New tests

1. `test_format_status_labels_output` — verify output contains header, all label names, descriptions, proper alignment
2. `test_format_status_labels_dynamic_width` — verify column width adapts to label name length (use synthetic config with short/long names)

### Updated tests

3. Update `test_validate_status_label_valid` — pass `full_labels_config` dict instead of `set`
4. Update `test_validate_status_label_invalid` — pass `full_labels_config` dict instead of `set`. Assert that the error message contains at least one label description string (e.g., from the config's `workflow_labels`), not just label names.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement Step 1 of issue #595: Add format_status_labels() and unify label formatting.

1. Write tests first (TDD):
   - In tests/cli/commands/test_set_status.py: add test_format_status_labels_output and test_format_status_labels_dynamic_width
   - Update test_validate_status_label_valid and test_validate_status_label_invalid to pass full_labels_config dict

2. Implement:
   - In src/mcp_coder/cli/commands/set_status.py: add format_status_labels(labels_config: dict) -> str
   - Refactor build_set_status_epilog() to call format_status_labels(), remove Examples section
   - Change validate_status_label() to accept labels_config dict, use format_status_labels() for error
   - In execute_set_status(): pass labels_config to validate_status_label() instead of status_labels set

3. Run all three code quality checks. Fix any issues.
4. Commit with message: "refactor: extract format_status_labels and unify label formatting (#595)"
```
