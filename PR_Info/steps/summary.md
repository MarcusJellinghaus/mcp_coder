# Project Directory Parameter Support for Implement Workflow

## Overview

Add `--project-dir` parameter support to the implement workflow script (`workflows/implement.py`) to allow execution from any location while operating on a specified project directory. This replaces hardcoded current working directory (`Path.cwd()`) usage with configurable project directory support.

## Architectural Changes

### Current Architecture Issues
- **Hard-coded CWD dependency**: All operations assume script runs from project root
- **Fixed path assumptions**: Uses `Path.cwd()` for git operations, formatters, and file paths
- **Location-bound execution**: Cannot run workflow from outside project directory
- **Batch file limitation**: `implement.bat` doesn't support project directory specification

### New Architecture Design
- **Configurable project root**: Accept `--project-dir` parameter (relative or absolute paths)
- **Path resolution**: Convert relative paths to absolute paths for consistency
- **Function parameter threading**: Pass `project_dir` through all function calls
- **Batch script enhancement**: Update `implement.bat` to use current directory as default

### Design Principles Applied
- **KISS Principle**: Minimal changes - only add required parameter passing
- **Consistency**: All functions receive same `project_dir: Path` parameter
- **Backward compatibility**: Default behavior unchanged when no parameter provided
- **Fail-fast**: Early validation of project directory existence and git repository status

## Files to be Modified

### Primary Files
1. **`workflows/implement.py`** - Main workflow script
   - Add `--project-dir` argument parsing
   - Update all functions to accept `project_dir` parameter as first parameter
   - Replace `Path.cwd()` calls with `project_dir` usage
   - Update path operations for `PR_INFO_DIR` and `CONVERSATIONS_DIR`
   - Log resolved project directory once in main()

2. **`workflows/implement.bat`** - Batch script wrapper
   - Add `--project-dir .` parameter to Python script call

## Key Functions Modified

### Function Signature Changes
All these functions will receive a new `project_dir: Path` parameter as the **first parameter**:

```python
def check_git_clean(project_dir: Path) -> bool
def check_prerequisites(project_dir: Path) -> bool  
def has_implementation_tasks(project_dir: Path) -> bool
def prepare_task_tracker(project_dir: Path) -> bool
def get_next_task(project_dir: Path) -> Optional[str]
def save_conversation(project_dir: Path, content: str, step_num: int) -> None
def run_formatters(project_dir: Path) -> bool
def commit_changes(project_dir: Path) -> bool
def push_changes(project_dir: Path) -> bool
def process_single_task(project_dir: Path) -> bool
```

### New Functions
```python
def resolve_project_dir(project_dir_arg: Optional[str]) -> Path
def parse_arguments() -> argparse.Namespace  # Modified to include --project-dir
```

## Data Structures

### Argument Parsing Structure
```python
# New argument structure
args = {
    'project_dir': Optional[str],  # e.g., ".", "/path/to/project", "relative/path"  
    'log_level': str              # existing
}
```

### Path Resolution
```python
# Resolved project directory
project_dir: Path  # Always absolute path, e.g., Path("/full/path/to/project")
```

## Integration Points

### Existing Dependencies
- **Git operations**: `is_working_directory_clean()`, `get_full_status()`, `commit_all_changes()`, `git_push()`
- **Task tracker**: `get_incomplete_tasks()` 
- **Formatters**: `format_code()`
- **LLM interface**: `ask_llm()`, `get_prompt()`

### Modified Integration
- All git operations will receive `project_dir` instead of `Path.cwd()`
- Task tracker operations will use `str(project_dir / PR_INFO_DIR)` 
- Formatter operations will receive `project_dir` as root
- File operations will be relative to `project_dir`

## Benefits

### Operational Benefits
- **Location independence**: Run workflow from any directory
- **Multi-project support**: Switch between projects without navigation
- **Automation friendly**: Easier integration with build systems and IDEs
- **Testing improvement**: Run tests with temporary project directories

### Development Benefits  
- **Clean separation**: Project operations isolated from execution location
- **Better testability**: Mock project directories in unit tests
- **Consistent behavior**: Same results regardless of execution location
- **Error reduction**: Eliminate "wrong directory" execution errors
