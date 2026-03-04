# Step 3: Implement Uncommitted Changes Display Logic

## Context
Read `pr_info/steps/summary.md` for full context. This step implements the logic to make the tests from Step 2 pass.

## Objective
Modify `execute_compact_diff()` to append uncommitted changes to the output when `--committed-only` flag is not set.

## Location
**File**: `src/mcp_coder/cli/commands/git_tool.py`
**Function**: `execute_compact_diff()`

## Changes Required

### WHERE: File and Function
```
src/mcp_coder/cli/commands/git_tool.py
└── execute_compact_diff() function
```

### WHAT: Modified Function Logic

**Current function** (simplified):
```python
def execute_compact_diff(args: argparse.Namespace) -> int:
    # ... validation and setup ...
    
    result = get_compact_diff(project_dir, base_branch, args.exclude or [])
    print(result)
    return 0
```

**Modified function** (after this step):
```python
def execute_compact_diff(args: argparse.Namespace) -> int:
    # ... existing validation and setup (unchanged) ...
    
    # Get committed changes (existing logic)
    committed_diff = get_compact_diff(project_dir, base_branch, args.exclude or [])
    
    # Get uncommitted changes (unless --committed-only flag set)
    if not args.committed_only:
        uncommitted_diff = get_git_diff_for_commit(project_dir)
        
        if uncommitted_diff:
            # Combine committed and uncommitted diffs
            if committed_diff:
                result = f"{committed_diff}\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
            else:
                result = f"No committed changes\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
        else:
            # No uncommitted changes, just return committed diff
            result = committed_diff
    else:
        # --committed-only flag set, skip uncommitted changes
        result = committed_diff
    
    print(result)
    return 0
```

### HOW: Integration Points

#### Import Required Function
Add to imports at top of file:
```python
from ...utils.git_operations.diffs import get_git_diff_for_commit
```

Existing imports in file:
```python
from ...utils.git_operations.compact_diffs import get_compact_diff
from ...workflow_utils.base_branch import detect_base_branch
from ...workflows.utils import resolve_project_dir
```

#### Access New Argument
The `args.committed_only` attribute is already available from Step 1.

### ALGORITHM: Core Logic (Pseudocode)

```python
# 1. Get committed changes (existing)
committed_diff = get_compact_diff(project_dir, base_branch, exclude_patterns)

# 2. Check if we should show uncommitted changes
if not args.committed_only:
    # 3. Get uncommitted changes
    uncommitted_diff = get_git_diff_for_commit(project_dir)
    
    # 4. Combine outputs if uncommitted changes exist
    if uncommitted_diff:
        if committed_diff:
            result = committed_diff + "\n\n=== UNCOMMITTED CHANGES ===\n" + uncommitted_diff
        else:
            result = "No committed changes\n\n=== UNCOMMITTED CHANGES ===\n" + uncommitted_diff
    else:
        result = committed_diff
else:
    # 5. Skip uncommitted changes
    result = committed_diff

# 6. Print and return
print(result)
return 0
```

### DATA: Return Values and Structures

**Function signature** (unchanged):
```python
def execute_compact_diff(args: argparse.Namespace) -> int
```

**Return codes** (unchanged):
- `0`: Success
- `1`: Could not detect base branch
- `2`: Error (invalid repo, exception)

**Output format**:
```
# Case 1: Both committed and uncommitted changes
[compact diff output]

=== UNCOMMITTED CHANGES ===
=== STAGED CHANGES ===
[staged diff]

=== UNSTAGED CHANGES ===
[unstaged diff]

=== UNTRACKED FILES ===
[untracked diff]

# Case 2: Only uncommitted changes
No committed changes

=== UNCOMMITTED CHANGES ===
[uncommitted diff sections]

# Case 3: Only committed changes (or --committed-only flag)
[compact diff output]

# Case 4: Clean working directory
[compact diff output or empty]
```

## Complete Modified Function

```python
def execute_compact_diff(args: argparse.Namespace) -> int:
    """Execute git-tool compact-diff command.

    Returns:
        0  Success — compact diff printed to stdout
        1  Could not detect base branch
        2  Error (invalid repo, unexpected exception)
    """
    try:
        logger.info("Starting compact-diff")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Use provided base branch or auto-detect
        base_branch = (
            args.base_branch if args.base_branch else detect_base_branch(project_dir)
        )

        if base_branch is None:
            logger.warning("Could not detect base branch")
            print("Error: Could not detect base branch", file=sys.stderr)
            return 1

        # Get committed changes
        committed_diff = get_compact_diff(project_dir, base_branch, args.exclude or [])
        
        # Get uncommitted changes (unless --committed-only flag set)
        if not args.committed_only:
            uncommitted_diff = get_git_diff_for_commit(project_dir)
            
            if uncommitted_diff:
                # Combine committed and uncommitted diffs
                if committed_diff:
                    result = f"{committed_diff}\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
                else:
                    result = f"No committed changes\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
            else:
                # No uncommitted changes, just return committed diff
                result = committed_diff
        else:
            # --committed-only flag set, skip uncommitted changes
            result = committed_diff
        
        print(result)
        return 0

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        logger.error(f"Error generating compact diff: {e}")
        logger.debug("Exception details:", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 2
```

## Validation

### Running Tests (Should Now Pass)
```bash
# Run the tests from Step 2
pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges -v

# Expected result: All 5 tests PASS
```

### Manual Testing
```bash
# Test 1: Default behavior (show uncommitted)
# Make some uncommitted changes first
echo "test" > test_file.py
mcp-coder git-tool compact-diff
# Should show both committed and uncommitted sections

# Test 2: Committed-only flag
mcp-coder git-tool compact-diff --committed-only
# Should show only committed changes

# Test 3: Clean working directory
git add -A && git commit -m "test"
mcp-coder git-tool compact-diff
# Should show only committed changes (no uncommitted section)

# Test 4: No committed changes, only uncommitted
# On feature branch with no commits
echo "test" > new_file.py
mcp-coder git-tool compact-diff
# Should show "No committed changes" + uncommitted section
```

### Integration Testing
```bash
# Run all git-tool tests
pytest tests/cli/commands/test_git_tool.py -v

# Run full test suite
pytest tests/ -v
```

## Definition of Done
- [ ] Import `get_git_diff_for_commit` added to `git_tool.py`
- [ ] `execute_compact_diff()` modified with uncommitted logic
- [ ] All 5 tests from Step 2 now PASS
- [ ] No existing tests broken
- [ ] Manual testing confirms correct output format
- [ ] Exit codes unchanged (0, 1, 2)
- [ ] Logging statements appropriate (if any added)

## Edge Cases Handled
1. ✅ No committed changes → "No committed changes" message
2. ✅ No uncommitted changes → Skip uncommitted section
3. ✅ `--committed-only` flag → Skip uncommitted logic entirely
4. ✅ Both present → Show both with separator
5. ✅ `get_git_diff_for_commit()` returns `None` → Treat as no changes

## LLM Implementation Prompt

```
You are implementing Step 3 of the compact-diff uncommitted changes feature.

Read pr_info/steps/summary.md for full context.

Task: Implement uncommitted changes display logic to make Step 2 tests pass.

File: src/mcp_coder/cli/commands/git_tool.py
Function: execute_compact_diff()

Steps:
1. Add import at top of file:
   from ...utils.git_operations.diffs import get_git_diff_for_commit

2. Modify execute_compact_diff() function:
   - After getting committed_diff = get_compact_diff(...)
   - Check if not args.committed_only
   - Call get_git_diff_for_commit(project_dir)
   - If uncommitted changes exist, combine with committed diff
   - Use "=== UNCOMMITTED CHANGES ===" as separator
   - Handle edge case: no committed changes → "No committed changes" message

3. Algorithm:
   committed_diff = get_compact_diff(project_dir, base_branch, args.exclude or [])
   
   if not args.committed_only:
       uncommitted_diff = get_git_diff_for_commit(project_dir)
       if uncommitted_diff:
           if committed_diff:
               result = f"{committed_diff}\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
           else:
               result = f"No committed changes\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
       else:
           result = committed_diff
   else:
       result = committed_diff
   
   print(result)

Verify:
- Run: pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges -v
- Expected: All 5 tests PASS (they were failing in Step 2)
- Run: pytest tests/cli/commands/test_git_tool.py -v
- Expected: All existing tests still pass

Manual test:
- Make uncommitted changes
- Run: mcp-coder git-tool compact-diff
- Should show both committed and uncommitted sections
```

## Next Step
Proceed to `pr_info/steps/step_4.md` - Write tests for exclude pattern filtering on uncommitted changes.
