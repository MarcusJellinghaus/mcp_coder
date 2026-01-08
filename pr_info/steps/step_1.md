# Step 1: Create CLI Command Module and Refactor Error Handling

## Overview

Create the `define_labels.py` CLI command module containing core logic for label synchronization. Also refactor `resolve_project_dir` to use exceptions instead of `sys.exit(1)`.

## WHERE

- **Create**: `src/mcp_coder/cli/commands/define_labels.py`
- **Modify**: `src/mcp_coder/workflows/utils.py` (refactor `resolve_project_dir`)
- **Modify**: `workflows/validate_labels.py` (add try/except wrapper)

## WHAT

### Part A: Refactor `resolve_project_dir` in `workflows/utils.py`

Change from `sys.exit(1)` to raising `ValueError`:

```python
# BEFORE (current)
logger.error(f"Project directory does not exist: {project_path}")
sys.exit(1)

# AFTER (new pattern)
raise ValueError(f"Project directory does not exist: {project_path}")
```

All validation failures should raise `ValueError` with descriptive message.

### Part B: Update `workflows/validate_labels.py`

Wrap the `resolve_project_dir` call in try/except:

```python
try:
    project_dir = resolve_project_dir(args.project_dir)
except ValueError as e:
    logger.error(str(e))
    sys.exit(1)
```

### Part C: Create CLI Command Module

Functions to implement in `src/mcp_coder/cli/commands/define_labels.py`:

```python
def calculate_label_changes(
    existing_labels: list[tuple[str, str, str]],
    target_labels: list[tuple[str, str, str]]
) -> dict[str, list[str]]
```
Pure function comparing existing vs target labels. Returns dict with keys: `created`, `updated`, `deleted`, `unchanged`.

```python
def apply_labels(
    project_dir: Path,
    workflow_labels: list[tuple[str, str, str]],
    dry_run: bool = False
) -> dict[str, list[str]]
```
Orchestrator that fetches existing labels, calculates changes, and applies them via `LabelsManager`. **Raises exceptions instead of sys.exit()**.

```python
def execute_define_labels(args: argparse.Namespace) -> int
```
CLI entry point that parses args, calls `apply_labels`, handles exceptions, and returns exit code.

## HOW

### Imports for CLI command module:
```python
import argparse
import logging
import sys
from pathlib import Path

from mcp_coder.utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.utils.github_operations.labels_manager import LabelsManager
from mcp_coder.workflows.utils import resolve_project_dir  # Import, don't copy!
```

### Exception pattern for `apply_labels`:
```python
# BEFORE (old pattern)
except Exception as e:
    logger.error(f"Failed to create label '{label_name}': {e}")
    sys.exit(1)

# AFTER (new pattern)
except Exception as e:
    raise RuntimeError(f"Failed to create label '{label_name}': {e}") from e
```

### `execute_define_labels` structure:
```python
def execute_define_labels(args: argparse.Namespace) -> int:
    try:
        project_dir = resolve_project_dir(args.project_dir)
        # ... load config, call apply_labels ...
        return 0
    except ValueError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

## ALGORITHM

### `calculate_label_changes`:
```
1. Build existing_map: {name: (color, description)} from existing_labels
2. Build target_names set from target_labels
3. For each target label:
   - If not in existing_map → add to 'created'
   - If exists but differs → add to 'updated'
   - If identical → add to 'unchanged'
4. For each existing status-* label not in target_names → add to 'deleted'
5. Return result dict
```

### `execute_define_labels`:
```
1. Resolve project_dir from args (default: cwd) - may raise ValueError
2. Load labels config (project local → bundled fallback)
3. Convert config to tuple format
4. Call apply_labels(project_dir, workflow_labels, dry_run) - may raise RuntimeError
5. Log summary and return 0 on success
6. Catch exceptions and return 1 on failure
```

## DATA

### Input (args):
- `args.project_dir: Optional[str]` - Project directory path
- `args.dry_run: bool` - Preview mode flag

### Output:
- Returns `int` exit code (0=success, 1=error)

### Exception types:
- `ValueError` - Invalid project directory, config errors
- `RuntimeError` - GitHub API failures during label operations

### Internal data structures:
```python
# Label tuple format
label_tuple = (name: str, color: str, description: str)

# Changes result
changes = {
    'created': ['label-name', ...],
    'updated': ['label-name', ...],
    'deleted': ['label-name', ...],
    'unchanged': ['label-name', ...]
}
```

## LLM Prompt

```
Please implement Step 1 of the implementation plan in `pr_info/steps/step_1.md`.

Context: See `pr_info/steps/summary.md` for the overall plan.

Task has three parts:

PART A: Refactor `src/mcp_coder/workflows/utils.py`
- Change `resolve_project_dir` to raise `ValueError` instead of calling `sys.exit(1)`
- All error conditions should raise ValueError with descriptive messages
- Remove the sys import if no longer needed

PART B: Update `workflows/validate_labels.py`
- Wrap the `resolve_project_dir(args.project_dir)` call in try/except
- Catch ValueError, log the error, and call sys.exit(1)

PART C: Create `src/mcp_coder/cli/commands/define_labels.py`
1. Copy these functions from `workflows/define_labels.py`:
   - `calculate_label_changes()` (keep as-is, it's a pure function)
   - `apply_labels()` (refactor to raise exceptions instead of sys.exit)

2. Import `resolve_project_dir` from `mcp_coder.workflows.utils` (do NOT copy it)

3. Add new `execute_define_labels(args)` function that:
   - Takes argparse.Namespace with project_dir and dry_run
   - Calls resolve_project_dir (catches ValueError)
   - Loads label config using existing `label_config.py` utilities
   - Calls `apply_labels()` (catches RuntimeError)
   - Returns exit code (0 success, 1 error)

Reference existing CLI command patterns in:
- `src/mcp_coder/cli/commands/create_pr.py` (uses resolve_project_dir + exception handling)
- `src/mcp_coder/cli/commands/commit.py` (exception handling pattern)

Do not modify main.py or help.py in this step - that's Step 2.
```

## Verification

- [ ] `resolve_project_dir` in `workflows/utils.py` raises `ValueError` instead of `sys.exit(1)`
- [ ] `workflows/validate_labels.py` has try/except wrapper for `resolve_project_dir`
- [ ] CLI command file created at correct location
- [ ] `calculate_label_changes` and `apply_labels` functions implemented
- [ ] `apply_labels` raises exceptions instead of `sys.exit(1)`
- [ ] `execute_define_labels` handles exceptions and returns exit codes
- [ ] Imports use package structure (imports `resolve_project_dir` from `workflows.utils`)
- [ ] No syntax errors: `python -c "from mcp_coder.cli.commands.define_labels import execute_define_labels"`
