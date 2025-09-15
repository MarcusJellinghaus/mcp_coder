# Step 1: Copy Git Operations Foundation and Update Dependencies

## WHERE
- **Source**: `p_fs:src/mcp_server_filesystem/file_tools/git_operations.py`
- **Target**: `src/mcp_coder/utils/git_operations.py`
- **Dependencies**: `pyproject.toml`

## WHAT
Copy existing git operations from reference project and add GitPython dependency.

### Main Functions (Copied)
```python
def is_git_repository(project_dir: Path) -> bool
def is_file_tracked(file_path: Path, project_dir: Path) -> bool  
def git_move(source_path: Path, dest_path: Path, project_dir: Path) -> bool
```

## HOW
### Integration Points
- Import adaptations: Update import paths for MCP Coder structure
- Logging: Use MCP Coder's logging patterns
- Dependencies: Add GitPython to pyproject.toml

### File Modifications
1. **Copy git_operations.py**: Copy from p_fs and adapt imports
2. **Update pyproject.toml**: Add `"GitPython>=3.1.0"` to dependencies

## ALGORITHM
```
1. Read source git_operations.py from p_fs reference
2. Update import statements to match MCP Coder structure  
3. Preserve all existing function signatures and logic
4. Add GitPython dependency to pyproject.toml dependencies list
5. Verify imports work correctly
```

## DATA
### Input Files
- `p_fs:src/mcp_server_filesystem/file_tools/git_operations.py`

### Output Files  
- `src/mcp_coder/utils/git_operations.py`
- `pyproject.toml` (modified dependencies)

### Return Values
- All existing functions maintain original return types:
  - `is_git_repository()` → `bool`
  - `is_file_tracked()` → `bool` 
  - `git_move()` → `bool`

---

## LLM PROMPT
```
Reference the summary in pr_info/steps/summary.md and decisions in pr_info/steps/Decisions.md for context.

Implement Step 1: Copy the git_operations.py file from the p_fs reference project to src/mcp_coder/utils/git_operations.py. Update any import statements to work with MCP Coder's structure. Also add GitPython>=3.1.0 to the dependencies in pyproject.toml.

Key requirements:
- Copy all functions exactly as they are: is_git_repository, is_file_tracked, git_move
- Update imports to work with mcp_coder structure  
- Add GitPython dependency to pyproject.toml
- Preserve all existing functionality and logging patterns
- Do not modify function logic, only adapt imports/structure

This establishes the foundation for our simplified git commit API.

Test by verifying the file imports correctly and all existing tests would still pass.
```
