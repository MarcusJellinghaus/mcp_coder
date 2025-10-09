# Step 6: Module Integration

## LLM Prompt
```
Read pr_info/steps/summary.md for context.

Implement Step 6: Update module exports and verify integration.
Add new classes to __init__.py and run verification tests.
```

## WHERE
**File**: `src/mcp_coder/utils/github_operations/__init__.py`

## WHAT

### Update Exports
```python
from .issue_branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)

__all__ = [
    "BaseGitHubManager",
    "PullRequestManager",
    "LabelsManager",
    "IssueManager",
    "IssueBranchManager",  # NEW
    "LabelData",
    "IssueData",
    "CommentData",
    "BranchCreationResult",  # NEW
    "generate_branch_name_from_issue",  # NEW (optional utility export)
]
```

## HOW

### Integration Points
```python
# In __init__.py, add imports:
from .issue_branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)
```

### Verification Commands
```bash
# Run unit tests
pytest tests/utils/github_operations/test_issue_branch_manager.py -v

# Run integration tests (requires GitHub config)
pytest tests/utils/github_operations/test_issue_branch_manager_integration.py -v -m github_integration

# Run all GitHub operations tests
pytest tests/utils/github_operations/ -v

# Verify imports work
python -c "from mcp_coder.utils.github_operations import IssueBranchManager, BranchCreationResult"
```

## ALGORITHM

```
1. Add import statements to __init__.py
2. Update __all__ list with new exports
3. Run pylint check on new module
4. Run mypy check on new module
5. Run unit tests (all should pass)
6. Run integration test (if GitHub configured)
```

## DATA

### Module Structure Verification
```python
# Test that imports work correctly
from mcp_coder.utils.github_operations import (
    IssueBranchManager,
    BranchCreationResult,
    generate_branch_name_from_issue,
)

# Verify class exists and inherits correctly
assert issubclass(IssueBranchManager, BaseGitHubManager)

# Verify TypedDict structure
result: BranchCreationResult = {
    "success": True,
    "branch_name": "test",
    "error": None,
    "existing_branches": []
}
```

### Quality Checks
```bash
# Expected results:
✓ Pylint: No errors or warnings
✓ Mypy: Type checks pass
✓ Pytest: All unit tests pass (100%)
✓ Integration: Workflow test passes (if configured)
✓ Import: Module exports accessible
```

## Completion Checklist
- [ ] __init__.py updated with new exports
- [ ] All imports resolve correctly
- [ ] Pylint check passes
- [ ] Mypy check passes
- [ ] Unit tests pass (100% coverage)
- [ ] Integration test passes (if GitHub configured)
- [ ] Documentation strings complete
- [ ] Code follows existing patterns
