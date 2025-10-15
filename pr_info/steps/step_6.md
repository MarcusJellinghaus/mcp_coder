# Step 6: Code Review Fixes - Critical Issues

## Goal
Fix critical issues identified during code review to improve code quality, eliminate duplication, and ensure proper error handling.

## Context
Code review identified three critical issues that need immediate fixes:
1. Hardcoded label name fallback could hide configuration errors
2. Temporary test file in wrong location
3. Duplicate `resolve_project_dir()` function implementation

## WHERE

### Files to MODIFY:
- `workflows/validate_labels.py` (3 changes)

### Files to DELETE:
- `test_multiple_labels_manual.py` (project root)
- `pr_info/test_results_multiple_labels.md`

## WHAT

### Change 1: Remove Hardcoded Label Fallback

**Location:** `workflows/validate_labels.py`, line ~276 in `process_issues()` function

**Current Code:**
```python
created_label_name = id_to_name.get("created", "status-01:created")
```

**New Code:**
```python
created_label_name = id_to_name["created"]
```

**Rationale:** Direct dictionary access will raise `KeyError` if "created" label is missing from config, providing clear failure instead of silent fallback to potentially wrong label name.

### Change 2: Add Import Statement

**Location:** `workflows/validate_labels.py`, imports section (top of file)

**Add:**
```python
from mcp_coder.workflows.utils import resolve_project_dir
```

### Change 3: Remove Duplicate Function

**Location:** `workflows/validate_labels.py`, lines ~430-480

**Remove entire function:**
```python
def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert project directory argument to absolute Path, with validation.
    
    Args:
        project_dir_arg: Project directory path string or None
        
    Returns:
        Absolute Path to validated project directory
        
    Raises:
        SystemExit: On validation errors
    """
    # [entire function body - ~50 lines]
```

**Keep the function call in `main()`:**
```python
project_dir = resolve_project_dir(args.project_dir)
```

### Change 4: Delete Temporary Files

**Files to delete:**
1. `test_multiple_labels_manual.py` (project root)
2. `pr_info/test_results_multiple_labels.md`

## HOW

### Integration Points

**Import Addition:**
- Add to existing imports from `mcp_coder` modules
- Place near other `mcp_coder.workflows` imports

**Function Removal:**
- Remove entire function definition
- Keep existing call in `main()` - it will now use the imported version
- No changes needed to function parameters or return value

## ALGORITHM

### For developers implementing this step:

```python
# 1. Add import at top of file
from mcp_coder.workflows.utils import resolve_project_dir

# 2. In process_issues(), change fallback to direct access
created_label_name = id_to_name["created"]  # Will raise KeyError if missing

# 3. Find and delete the resolve_project_dir() function (~50 lines)
# Search for: "def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:"
# Delete entire function including docstring

# 4. Delete temporary files
# - test_multiple_labels_manual.py
# - pr_info/test_results_multiple_labels.md

# 5. Verify main() still works (it calls resolve_project_dir via import)
```

## DATA

### Expected Behavior Changes

**Before (with fallback):**
```python
# If "created" missing from config
created_label_name = "status-01:created"  # Silent fallback
# Issue gets potentially wrong label
```

**After (no fallback):**
```python
# If "created" missing from config
KeyError: 'created'  # Clear error
# Script exits with traceback showing configuration problem
```

### No Functional Changes
- Same behavior when configuration is correct
- Better error messages when configuration is wrong
- No code duplication
- Cleaner import structure

## Tests

### Testing Strategy

**No new tests needed** - this is pure refactoring:
- Existing tests already validate correct behavior
- KeyError will be caught by existing error handling tests
- Import change is transparent (same function, different location)

### Verification Steps

1. **Run existing tests:**
   ```bash
   pytest tests/workflows/test_validate_labels.py -v
   ```
   All tests should still pass.

2. **Verify import works:**
   ```bash
   python -c "from mcp_coder.workflows.utils import resolve_project_dir; print('OK')"
   ```

3. **Test script runs:**
   ```bash
   workflows\validate_labels.bat --help
   ```

4. **Verify files deleted:**
   ```bash
   # Should not exist
   test_multiple_labels_manual.py
   pr_info/test_results_multiple_labels.md
   ```

## LLM Prompt for Implementation

```
Please implement Step 6 from pr_info/steps/step_6.md

This step fixes critical issues from code review:
1. Remove hardcoded label fallback (use direct dict access)
2. Import resolve_project_dir from mcp_coder.workflows.utils
3. Delete duplicate resolve_project_dir() function
4. Delete temporary test files

Key requirements:
- Change id_to_name.get("created", "status-01:created") to id_to_name["created"]
- Add import: from mcp_coder.workflows.utils import resolve_project_dir
- Remove lines ~430-480 (duplicate resolve_project_dir function)
- Delete: test_multiple_labels_manual.py
- Delete: pr_info/test_results_multiple_labels.md
- Keep the function call in main() unchanged (it uses the import)

After implementation:
1. Run pytest tests/workflows/test_validate_labels.py -v
2. Run workflows\validate_labels.bat --help
3. Verify files are deleted
4. Run quality checks: pylint, mypy
5. Provide commit message

This is pure refactoring - no functional changes, just cleaner code.
```

## Definition of Done

- [ ] Hardcoded fallback removed (direct dict access)
- [ ] Import added for resolve_project_dir
- [ ] Duplicate function removed (~50 lines)
- [ ] test_multiple_labels_manual.py deleted
- [ ] pr_info/test_results_multiple_labels.md deleted
- [ ] All existing tests still pass
- [ ] Script runs without errors (--help works)
- [ ] All quality checks pass (pylint, mypy)
- [ ] Code is cleaner with no duplication
