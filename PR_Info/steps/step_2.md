# Step 2: Add Project Directory Parameter to Argument Parser

## Overview
Implement the `--project-dir` argument parsing and path resolution functionality in `workflows/implement.py`. This step focuses on the argument parsing and path resolution core functionality.

## WHERE
- **File**: `workflows/implement.py`
- **Functions**: `parse_arguments()`, `resolve_project_dir()` (new function)

## WHAT

### Modified Function
```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including project directory and log level."""
    
def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert project directory argument to absolute Path, with validation."""
```

### Function Signatures
```python
# Enhanced argument parser
parse_arguments() -> argparse.Namespace  # Now includes project_dir field

# New path resolution function  
resolve_project_dir(project_dir_arg: Optional[str]) -> Path
```

## HOW

### Integration Points
- **argparse**: Add `--project-dir` argument to existing parser
- **pathlib**: Use `Path.resolve()` for absolute path conversion
- **os.path**: Validate directory existence and permissions
- **sys.exit()**: Handle fatal errors (invalid directories)

### Imports (add these)
```python
from typing import Optional  # Already imported
from pathlib import Path    # Already imported  
import os                   # Already imported
```

## ALGORITHM

### Argument Parsing (5-6 steps)
```pseudocode
1. Create ArgumentParser with existing log_level argument
2. Add --project-dir argument with help text and metavar
3. Parse arguments and return namespace
4. In main(), call resolve_project_dir() with parsed argument
5. Use resolved path for all subsequent operations
6. Handle validation errors with clear error messages
```

### Path Resolution Algorithm  
```pseudocode
1. If project_dir_arg is None, use Path.cwd()
2. Create Path object from project_dir_arg
3. Resolve to absolute path using Path.resolve()
4. Validate directory exists and is accessible
5. Validate directory contains .git subdirectory
6. Return validated absolute Path object
```

## DATA

### Input Parameters
```python
# parse_arguments() input: command line args
# --project-dir "." | --project-dir "/abs/path" | --project-dir "rel/path" | (none)

# resolve_project_dir() input
project_dir_arg: Optional[str] = None | "." | "relative/path" | "/absolute/path"
```

### Return Values
```python
# parse_arguments() returns
args: argparse.Namespace {
    project_dir: Optional[str],  # Raw argument value
    log_level: str              # Existing field
}

# resolve_project_dir() returns
project_dir: Path  # Always absolute, validated path
```

### Error Handling
```python
# Possible exceptions to handle
FileNotFoundError   # Directory doesn't exist
PermissionError     # No read access  
ValueError          # Invalid path format
```

## Integration with main()

### Updated main() function structure
```python
def main() -> None:
    args = parse_arguments()
    project_dir = resolve_project_dir(args.project_dir)  # New line
    
    setup_logging(args.log_level)
    # All subsequent function calls pass project_dir parameter
```

## LLM PROMPT

Please read the **summary.md** file and implement **Step 2** exactly as specified.

**Context**: We're adding `--project-dir` parameter support to eliminate hardcoded `Path.cwd()` usage.

**Your Task**: Modify `workflows/implement.py` to add:

1. **Enhanced `parse_arguments()` function** - Add `--project-dir` argument that accepts optional path string
2. **New `resolve_project_dir()` function** - Convert project directory argument to absolute Path with validation
3. **Updated `main()` function** - Use resolved project directory and log it once after resolution

**Specific Requirements**:
- `--project-dir` argument should be optional, accept relative/absolute paths
- `resolve_project_dir()` should convert relative paths to absolute paths  
- Validate directory exists and is a git repository (contains .git)
- Provide clear error messages for invalid directories
- Default behavior (no `--project-dir`) should use current working directory
- Convert to absolute path immediately and log the resolved project directory in main()
- Don't modify other functions yet - just the argument parsing and path resolution

**Implementation Details**:
- Use `Path.resolve()` for absolute path conversion
- Use `argparse` with clear help text and metavar
- Handle `FileNotFoundError`, `PermissionError`, and invalid paths
- Exit gracefully with `sys.exit(1)` on validation errors

This step focuses purely on argument parsing and path resolution functionality.
