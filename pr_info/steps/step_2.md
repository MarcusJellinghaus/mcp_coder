# Step 2: Implement Clean Working Directory Check

## LLM Prompt
```
Implement Step 2 from pr_info/steps/summary.md: Add the --force flag and working directory check to set-status command.

Reference: pr_info/steps/step_2.md for detailed specifications.
```

## Overview
Implement the core functionality: add `--force` CLI argument and working directory cleanliness check to `execute_set_status()`.

## WHERE: File Paths
- **Modify**: `src/mcp_coder/cli/main.py` (add --force argument)
- **Modify**: `src/mcp_coder/cli/commands/set_status.py` (add check logic)

## WHAT: Changes Required

### 2.1 main.py - Add CLI Argument

**Location**: In `create_parser()`, after the existing `set-status` arguments

```python
set_status_parser.add_argument(
    "--force",
    action="store_true",
    help="Bypass clean working directory check",
)
```

### 2.2 set_status.py - Add Imports

**Location**: Top of file, with other imports

```python
from ...constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from ...utils.git_operations.repository import is_working_directory_clean
```

### 2.3 set_status.py - Add Check in execute_set_status()

**Location**: After Step 1 (resolve project directory), before Step 2 (load and validate label)

## HOW: Integration Points

### Import Additions (set_status.py)
```python
# Add to existing imports section:
from ...constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from ...utils.git_operations.repository import is_working_directory_clean
```

### Function Modification (execute_set_status)
Insert new code block between Step 1 and Step 2.

## ALGORITHM: Check Logic (Pseudocode)

```
1. IF args.force is False:
2.     TRY:
3.         IF NOT is_working_directory_clean(project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS):
4.             PRINT error message to stderr
5.             RETURN 1
6.     EXCEPT ValueError as e:  # Not a git repository
7.         PRINT error message to stderr
8.         RETURN 1
```

## DATA: Error Message

Exact error message from issue requirements:
```
Error: Working directory has uncommitted changes. Commit/stash first or use --force.
```

## Code Changes

### main.py Addition
Insert after line ~295 (after `--project-dir` argument for set-status):

```python
    set_status_parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass clean working directory check",
    )
```

### set_status.py Changes

**Imports** (add at top with other imports):
```python
from ...constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from ...utils.git_operations.repository import is_working_directory_clean
```

**New code block** (insert in execute_set_status after Step 1):
```python
        # Step 1.5: Check working directory is clean (unless --force)
        if not args.force:
            try:
                if not is_working_directory_clean(
                    project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
                ):
                    print(
                        "Error: Working directory has uncommitted changes. "
                        "Commit/stash first or use --force.",
                        file=sys.stderr,
                    )
                    return 1
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1
```

## Notes
- Use `args.force` directly - the CLI parser guarantees the attribute exists (per Decision 2)
- Follow existing error handling pattern in the function
- Keep the check simple - no need for detailed status output (unlike implement command)
