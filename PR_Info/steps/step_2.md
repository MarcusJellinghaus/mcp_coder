# Step 2: Move Claude-Related Test Files

## Objective

Move existing Claude-related test files from the flat `tests/` structure to the new `tests/llm_providers/claude/` subdirectory to match the source code organization.

## Context

Reference the **summary** (`pr_info/steps/summary.md`) for complete project context. This step depends on Step 1 completing successfully (directory structure created).

## Implementation Details

### WHERE
Move files from `tests/` to `tests/llm_providers/claude/`:
- `tests/test_claude_client.py` → `tests/llm_providers/claude/test_claude_client.py`
- `tests/test_claude_client_integration.py` → `tests/llm_providers/claude/test_claude_client_integration.py`
- `tests/test_claude_code_api.py` → `tests/llm_providers/claude/test_claude_code_api.py`
- `tests/test_claude_code_cli.py` → `tests/llm_providers/claude/test_claude_code_cli.py`
- `tests/test_claude_executable_finder.py` → `tests/llm_providers/claude/test_claude_executable_finder.py`

### WHAT
**Main Functions**:
- File movement using `shutil.move()` or `pathlib.Path.rename()`
- Import statement verification and updates if needed
- Path validation for source and destination

**File Operations**:
```python
moves = [
    ("test_claude_client.py", "llm_providers/claude/test_claude_client.py"),
    ("test_claude_client_integration.py", "llm_providers/claude/test_claude_client_integration.py"),
    ("test_claude_code_api.py", "llm_providers/claude/test_claude_code_api.py"),
    ("test_claude_code_cli.py", "llm_providers/claude/test_claude_code_cli.py"),
    ("test_claude_executable_finder.py", "llm_providers/claude/test_claude_executable_finder.py")
]
```

### HOW
**Integration Points**:
- Use MCP file system tools (`move_file` function)
- Verify source files exist before moving
- Ensure destination directories exist (from Step 1)
- Validate moves completed successfully

### ALGORITHM
**Core Logic (5-6 lines)**:
```python
for source_file, dest_path in file_moves:
    source = Path("tests") / source_file
    destination = Path("tests") / dest_path
    if source.exists():
        source.rename(destination)
        verify_move_success(destination)
```

### DATA
**Return Values**:
- Moved files: `List[Tuple[Path, Path]]` (source, destination)
- Move status: `Dict[str, bool]` (filename → success)

**Data Structures**:
- File path mappings as tuples
- Status tracking dictionary

## LLM Implementation Prompt

Please review the implementation plan in PR_Info, especially the summary and steps/step_2.md.

**Task**: Move Claude-related test files to the new directory structure.

**Requirements**:
1. Move 5 Claude-related test files from `tests/` to `tests/llm_providers/claude/`
2. Use the MCP file system `move_file` function for reliable file operations
3. Verify each source file exists before attempting to move
4. Confirm each destination location after move
5. Preserve file contents exactly - only location changes
6. Do not modify import statements yet (Step 4 will handle that)

**Files to Move**:
- `test_claude_client.py` → `llm_providers/claude/test_claude_client.py`
- `test_claude_client_integration.py` → `llm_providers/claude/test_claude_client_integration.py`
- `test_claude_code_api.py` → `llm_providers/claude/test_claude_code_api.py`
- `test_claude_code_cli.py` → `llm_providers/claude/test_claude_code_cli.py`
- `test_claude_executable_finder.py` → `llm_providers/claude/test_claude_executable_finder.py`

**Validation**:
- Confirm all 5 files moved successfully
- Verify original locations are empty (files removed from `tests/`)
- Check new locations contain the files with identical content

Please implement this step carefully, ensuring all Claude test files are properly relocated to their new subdirectory structure.

## Acceptance Criteria

- [ ] All 5 Claude test files moved to `tests/llm_providers/claude/`
- [ ] Original files no longer exist in `tests/` root directory
- [ ] File contents remain unchanged during move
- [ ] New file locations are accessible and readable
- [ ] No files lost or corrupted during move process
- [ ] Directory structure matches source code organization
