# Step 1: Add `is_status_eligible_for_session()` Function

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Implement the `is_status_eligible_for_session()` function in issues.py with TDD approach.
This function determines if a status label should have a VSCodeClaude session.
```

## WHERE

- **Test file**: `tests/workflows/vscodeclaude/test_issues.py`
- **Implementation file**: `src/mcp_coder/workflows/vscodeclaude/issues.py`

## WHAT

### Function Signature

```python
def is_status_eligible_for_session(status: str) -> bool:
    """Check if status should have a VSCodeClaude session.
    
    Returns True only for human_action statuses with non-null initial_command:
    - status-01:created
    - status-04:plan-review
    - status-07:code-review
    
    Returns False for:
    - bot_pickup statuses (02, 05, 08)
    - bot_busy statuses (03, 06, 09)
    - status-10:pr-created (null initial_command)
    - Unknown/invalid status strings
    
    Args:
        status: Status label like "status-07:code-review"
        
    Returns:
        True if status should have a VSCodeClaude session
    """
```

## HOW

### Integration Points

- Uses existing `get_vscodeclaude_config(status)` function from same module
- Add to `__all__` list if module has one (it doesn't currently)
- Will be imported by `orchestrator.py`, `status.py`, and `cleanup.py` in later steps

## ALGORITHM

```
1. Call get_vscodeclaude_config(status)
2. If config is None → return False (bot statuses have no vscodeclaude config)
3. Get initial_command from config
4. Return True if initial_command is not None, else False
```

## DATA

### Input
- `status: str` - Status label like "status-07:code-review"

### Output
- `bool` - True if session eligible, False otherwise

### Test Cases

```python
# Eligible statuses (have initial_command)
("status-01:created", True),
("status-04:plan-review", True),
("status-07:code-review", True),

# Ineligible - bot_pickup (no vscodeclaude config)
("status-02:awaiting-planning", False),
("status-05:plan-ready", False),
("status-08:ready-pr", False),

# Ineligible - bot_busy (no vscodeclaude config)
("status-03:planning", False),
("status-06:implementing", False),
("status-09:pr-creating", False),

# Ineligible - pr-created (has config but null initial_command)
("status-10:pr-created", False),

# Edge cases
("", False),
("invalid-status", False),
("status-99:unknown", False),
```

## Implementation Order

1. Write test class `TestIsStatusEligibleForSession` in `test_issues.py`
2. Add parameterized test for all status labels
3. Implement `is_status_eligible_for_session()` in `issues.py`
4. Run tests to verify
