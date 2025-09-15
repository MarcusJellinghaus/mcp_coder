# Step 1: Copy Git Operations Foundation and Update Dependencies

## Goal
Get existing git operations working in MCP Coder by copying foundation from p_fs reference project.

## Tasks
1. Copy `git_operations.py` from p_fs reference to `src/mcp_coder/utils/git_operations.py`
2. Update import statements to work with MCP Coder structure
3. Add GitPython dependency to pyproject.toml

## Functions Being Copied
```python
def is_git_repository(project_dir: Path) -> bool
def is_file_tracked(file_path: Path, project_dir: Path) -> bool  
def git_move(source_path: Path, dest_path: Path, project_dir: Path) -> bool
```

## Expected Changes
- **Source**: `p_fs:src/mcp_server_filesystem/file_tools/git_operations.py`
- **Target**: `src/mcp_coder/utils/git_operations.py`
- **Dependencies**: Add `"GitPython>=3.1.0"` to pyproject.toml

## Done When
- File imports without errors
- All existing function signatures preserved
- GitPython dependency added to project

## Integration Notes
- Update import paths for MCP Coder structure
- Preserve all existing function logic and logging patterns
- No functional changes, only structural adaptations
