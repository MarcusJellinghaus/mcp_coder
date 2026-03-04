# Step 5: Implement Exclude Pattern Filtering for Uncommitted Changes

## Context
Read `pr_info/steps/summary.md` for full context. This step implements exclude pattern filtering to make Step 4 tests pass.

## Objective
Create a helper function to filter uncommitted diff output by exclude patterns, and integrate it into `execute_compact_diff()`.

## Location
**File**: `src/mcp_coder/cli/commands/git_tool.py`

## Changes Required

### WHERE: Add Helper Function

Add new private helper function before `execute_compact_diff()`:

```python
def _apply_exclude_patterns_to_uncommitted_diff(
    uncommitted_diff: str, exclude_patterns: list[str]
) -> str:
    """Filter uncommitted diff by exclude patterns.
    
    Args:
        uncommitted_diff: Raw uncommitted diff from get_git_diff_for_commit()
        exclude_patterns: List of glob patterns to exclude (e.g., ["*.log", "pr_info/**"])
    
    Returns:
        Filtered diff with excluded files removed, preserving section headers.
        Returns empty string if all files are excluded.
    """
```

### WHAT: Helper Function Implementation

```python
def _apply_exclude_patterns_to_uncommitted_diff(
    uncommitted_diff: str, exclude_patterns: list[str]
) -> str:
    """Filter uncommitted diff by exclude patterns.
    
    Removes diff blocks for files matching any exclude pattern.
    Preserves section headers (=== STAGED CHANGES ===, etc.) only if
    they have remaining content after filtering.
    
    Args:
        uncommitted_diff: Raw uncommitted diff from get_git_diff_for_commit()
        exclude_patterns: List of glob patterns to exclude (e.g., ["*.log", "pr_info/**"])
    
    Returns:
        Filtered diff with excluded files removed, preserving section headers.
        Returns empty string if all files are excluded.
    """
    if not exclude_patterns or not uncommitted_diff:
        return uncommitted_diff
    
    import fnmatch
    from pathlib import Path
    
    lines = uncommitted_diff.split("\n")
    filtered_lines = []
    current_block = []
    skip_current_block = False
    
    for line in lines:
        # Section headers (keep them, decide later if section is empty)
        if line.startswith("=== ") and line.endswith(" ==="):
            # Flush previous block
            if current_block and not skip_current_block:
                filtered_lines.extend(current_block)
            current_block = [line]
            skip_current_block = False
            continue
        
        # Diff block start (diff --git <file> <file>)
        if line.startswith("diff --git "):
            # Flush previous block
            if current_block and not skip_current_block:
                filtered_lines.extend(current_block)
            
            # Extract filename from "diff --git a/file.py b/file.py"
            # Format: "diff --git <path> <path>" (no a/ b/ prefix due to --no-prefix)
            parts = line.split()
            if len(parts) >= 3:
                filepath = parts[2]  # Second path (destination)
                
                # Check if file matches any exclude pattern
                skip_current_block = any(
                    fnmatch.fnmatch(filepath, pattern) for pattern in exclude_patterns
                )
            else:
                skip_current_block = False
            
            current_block = [line]
            continue
        
        # Regular diff line (part of current block)
        current_block.append(line)
    
    # Flush last block
    if current_block and not skip_current_block:
        filtered_lines.extend(current_block)
    
    # Remove empty sections (section header with no content)
    result = []
    i = 0
    while i < len(filtered_lines):
        line = filtered_lines[i]
        
        # If it's a section header, check if next non-empty line is another section header
        if line.startswith("=== ") and line.endswith(" ==="):
            # Look ahead for content
            j = i + 1
            has_content = False
            while j < len(filtered_lines):
                next_line = filtered_lines[j]
                if next_line.strip():  # Non-empty line
                    if next_line.startswith("=== ") and next_line.endswith(" ==="):
                        # Another section header, no content in current section
                        break
                    else:
                        # Found content
                        has_content = True
                        break
                j += 1
            
            if has_content or j >= len(filtered_lines):
                result.append(line)
        else:
            result.append(line)
        
        i += 1
    
    return "\n".join(result).strip()
```

### ALGORITHM: Core Logic (Pseudocode)

```python
# 1. Split diff into lines
lines = uncommitted_diff.split("\n")

# 2. Iterate through lines, tracking current diff block
for line in lines:
    # 3. Detect section headers (=== STAGED CHANGES ===)
    if is_section_header(line):
        save_current_block()
        start_new_section(line)
    
    # 4. Detect diff block start (diff --git <file>)
    elif line.startswith("diff --git"):
        extract_filepath_from_line()
        check_if_matches_exclude_patterns()
        if matches:
            skip_current_block = True
        else:
            skip_current_block = False
    
    # 5. Add line to current block
    current_block.append(line)

# 6. Remove empty sections (header with no content)
# 7. Return filtered result
```

### HOW: Integrate into execute_compact_diff()

**Modify Step 3 implementation** to apply exclude patterns:

```python
# In execute_compact_diff(), replace:
if not args.committed_only:
    uncommitted_diff = get_git_diff_for_commit(project_dir)
    
    if uncommitted_diff:
        # ... combine logic ...

# With:
if not args.committed_only:
    uncommitted_diff = get_git_diff_for_commit(project_dir)
    
    # Apply exclude patterns to uncommitted diff
    if uncommitted_diff and args.exclude:
        uncommitted_diff = _apply_exclude_patterns_to_uncommitted_diff(
            uncommitted_diff, args.exclude
        )
    
    if uncommitted_diff:
        # ... combine logic (unchanged) ...
```

### DATA: Function Signatures

**Helper function**:
```python
def _apply_exclude_patterns_to_uncommitted_diff(
    uncommitted_diff: str,
    exclude_patterns: list[str]
) -> str
```

**Input**:
- `uncommitted_diff`: String with section headers and diff blocks
- `exclude_patterns`: List of glob patterns (e.g., `["*.log", "pr_info/**"]`)

**Output**:
- Filtered diff string with excluded files removed
- Empty string if all files excluded
- Preserves section structure

**Example**:
```python
Input:
=== STAGED CHANGES ===
diff --git code.py code.py
+python code
diff --git test.log test.log
+log content

Patterns: ["*.log"]

Output:
=== STAGED CHANGES ===
diff --git code.py code.py
+python code
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
            
            # Apply exclude patterns to uncommitted diff
            if uncommitted_diff and args.exclude:
                uncommitted_diff = _apply_exclude_patterns_to_uncommitted_diff(
                    uncommitted_diff, args.exclude
                )
            
            if uncommitted_diff:
                # Combine committed and uncommitted diffs
                if committed_diff:
                    result = f"{committed_diff}\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
                else:
                    result = f"No committed changes\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
            else:
                # No uncommitted changes (or all excluded), just return committed diff
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
# Run all tests from Step 4
pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges -v

# Expected result: All tests PASS (including new exclude pattern tests)

# Run all git-tool tests
pytest tests/cli/commands/test_git_tool.py -v

# Expected result: All tests PASS
```

### Manual Testing
```bash
# Test 1: Exclude *.log from uncommitted
echo "test" > test.py
echo "debug" > debug.log
git add test.py debug.log
mcp-coder git-tool compact-diff --exclude "*.log"
# Should show test.py but NOT debug.log

# Test 2: Exclude path prefix
echo "code" > src/main.py
echo "notes" > pr_info/notes.md
git add src/main.py pr_info/notes.md
mcp-coder git-tool compact-diff --exclude "pr_info/**"
# Should show src/main.py but NOT pr_info/notes.md

# Test 3: Multiple exclude patterns
echo "a" > file.py
echo "b" > file.log
echo "c" > file.json
git add file.py file.log file.json
mcp-coder git-tool compact-diff --exclude "*.log" --exclude "*.json"
# Should show only file.py

# Test 4: Exclude all uncommitted
echo "log" > only.log
git add only.log
mcp-coder git-tool compact-diff --exclude "*.log"
# Should NOT show "UNCOMMITTED CHANGES" section
```

### Edge Case Testing
```bash
# Edge 1: Empty exclude patterns
mcp-coder git-tool compact-diff --exclude ""
# Should work without error

# Edge 2: Pattern matches nothing
echo "test" > test.py
git add test.py
mcp-coder git-tool compact-diff --exclude "*.cpp"
# Should show test.py (no matches)

# Edge 3: Committed and uncommitted both excluded
mcp-coder git-tool compact-diff --exclude "*.py" --exclude "*.log"
# Should handle gracefully
```

## Definition of Done
- [ ] `_apply_exclude_patterns_to_uncommitted_diff()` helper function added
- [ ] Helper function filters files by glob patterns (fnmatch)
- [ ] Helper function removes empty sections
- [ ] `execute_compact_diff()` calls helper function with exclude patterns
- [ ] All 5 tests from Step 4 now PASS
- [ ] No existing tests broken
- [ ] Manual testing confirms correct filtering
- [ ] Edge cases handled (empty patterns, no matches, etc.)

## Performance Considerations
- Helper function complexity: O(n) where n = number of lines in diff
- fnmatch pattern matching: O(m) where m = number of patterns
- Overall: O(n × m), acceptable for typical use cases

## LLM Implementation Prompt

```
You are implementing Step 5 of the compact-diff uncommitted changes feature.

Read pr_info/steps/summary.md for full context.

Task: Implement exclude pattern filtering for uncommitted changes.

File: src/mcp_coder/cli/commands/git_tool.py

Steps:
1. Add helper function _apply_exclude_patterns_to_uncommitted_diff()
   - Takes uncommitted_diff (str) and exclude_patterns (list[str])
   - Returns filtered diff string
   - Use fnmatch to match glob patterns (import fnmatch)

2. Algorithm:
   - Split diff into lines
   - Track current diff block
   - When "diff --git <file>" found, extract filename
   - Check if filename matches any exclude pattern
   - Skip block if match found
   - Remove empty sections (section header with no content)

3. Integrate into execute_compact_diff():
   - After getting uncommitted_diff = get_git_diff_for_commit(project_dir)
   - If uncommitted_diff and args.exclude:
       uncommitted_diff = _apply_exclude_patterns_to_uncommitted_diff(
           uncommitted_diff, args.exclude
       )

4. Handle edge cases:
   - Empty uncommitted_diff → return as-is
   - Empty exclude_patterns → return as-is
   - All files excluded → return empty string (triggers "no uncommitted" logic)

Reference the complete implementation in this step file.

Verify:
- Run: pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges -v
- Expected: All tests PASS (including Step 4 tests that were failing)
- Manual test: Create uncommitted .log file, run with --exclude "*.log"
- Expected: .log file NOT shown in output
```

## Next Step
Proceed to `pr_info/steps/step_6.md` - Update documentation.
