# Simplified Git Commit Feature Implementation Summary

## Overview
Implement git commit functionality for MCP Coder by copying and adapting git operations from the `p_fs` reference project, then extending it with simple, git-aligned commit capabilities.

## Core Objectives
1. **Copy Foundation**: Port `git_operations.py` and tests from `p_fs` to MCP Coder
2. **Add Dependencies**: Include GitPython in project requirements 
3. **Implement Simple Commit API**: Add git-aligned functions with basic error handling
4. **Test Coverage**: Ensure robust testing for all git operations

## Key Components

### Files to Create/Modify
- `src/mcp_coder/utils/git_operations.py` (copied + extended)
- `tests/utils/test_git_operations.py` (copied + extended)
- `pyproject.toml` (add GitPython dependency)
- Module exports in `__init__.py` files

### Main Functions to Implement
```python
# Existing (copied from p_fs)
def is_git_repository(project_dir: Path) -> bool
def is_file_tracked(file_path: Path, project_dir: Path) -> bool

# New git-aligned functionality
def get_staged_changes(project_dir: Path) -> list[str]
def get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]
def get_full_status(project_dir: Path) -> dict[str, list[str]]  # Added comprehensive status
def stage_specific_files(files: list[Path], project_dir: Path) -> bool
def stage_all_changes(project_dir: Path) -> bool
def commit_staged_files(message: str, project_dir: Path) -> CommitResult
def commit_all_changes(message: str, project_dir: Path) -> CommitResult
```

**Note**: Removed `commit_specific_files()` to avoid API duplication - users achieve the same result with `stage_specific_files()` → `commit_staged_files()`

### API Design Principles
- **Simplicity**: Clean, git-aligned functions that match git's mental model
- **Safety**: Always validate git repository before operations
- **Clarity**: Simple return structures that are easily extendable
- **Git-Reality**: Explicit staging then commit workflow, no complex parameters

### Data Structures
```python
# Unstaged changes (structured)
get_unstaged_changes() -> {
    "modified": list[str],    # Modified but unstaged files  
    "untracked": list[str]   # New files not tracked by git
}

# Simple commit result (extensible)
CommitResult = {
    "success": bool,
    "commit_hash": str | None,  # Short hash like "a1b2c3d"
    "error": str | None
}
```

## Implementation Strategy
- **Steps 1-2**: Copy foundation (git_operations.py + tests) and update dependencies
- **Steps 3-5**: Implement git status functions (TDD: test & implement each function)
- **Steps 6-8**: Implement file staging functions (TDD: test & implement each function)
- **Steps 9-10**: Implement commit functions (TDD: test & implement each function)
- **Steps 11-12**: Integration testing and module exports

*Total: 12 focused steps using KISS + TDD + small incremental approach*

## Quality Assurance
- Follow TDD: Write tests before implementation
- Use existing `p_fs` tests as reference for git repository testing patterns
- Comprehensive error handling for common git scenarios
- Integration tests with real git repositories in temporary directories
