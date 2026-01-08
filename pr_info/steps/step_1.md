# Step 1: Create CLI Command Module

## Overview

Create the `define_labels.py` CLI command module containing all logic for label synchronization.

## WHERE

- **Create**: `src/mcp_coder/cli/commands/define_labels.py`

## WHAT

### Functions to implement (moved from `workflows/define_labels.py`):

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
Orchestrator that fetches existing labels, calculates changes, and applies them via `LabelsManager`.

```python
def resolve_project_dir(project_dir_arg: Optional[str]) -> Path
```
Validates and resolves project directory path. Ensures it exists and is a git repository.

```python
def execute_define_labels(args: argparse.Namespace) -> int
```
CLI entry point that parses args and calls `apply_labels`.

## HOW

### Imports needed:
```python
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp_coder.utils import get_github_repository_url
from mcp_coder.utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.utils.github_operations.labels_manager import LabelsManager
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
1. Resolve project_dir from args (default: cwd)
2. Load labels config (project local → bundled fallback)
3. Convert config to tuple format
4. Call apply_labels(project_dir, workflow_labels, dry_run)
5. Log summary and return 0 on success
```

## DATA

### Input (args):
- `args.project_dir: Optional[str]` - Project directory path
- `args.dry_run: bool` - Preview mode flag

### Output:
- Returns `int` exit code (0=success, 1=error)

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

Task: Create `src/mcp_coder/cli/commands/define_labels.py` by:

1. Copy the following functions from `workflows/define_labels.py`:
   - `calculate_label_changes()` 
   - `apply_labels()`
   - `resolve_project_dir()`

2. Add a new `execute_define_labels(args)` function that:
   - Takes argparse.Namespace with project_dir and dry_run
   - Resolves project directory
   - Loads label config using existing `label_config.py` utilities
   - Calls `apply_labels()`
   - Returns exit code (0 success, 1 error)

3. Update imports to use the package structure (not relative workflows imports)

Reference existing CLI command patterns in:
- `src/mcp_coder/cli/commands/verify.py` 
- `src/mcp_coder/cli/commands/commit.py`

Do not modify any other files in this step.
```

## Verification

- [ ] File created at correct location
- [ ] All four functions implemented
- [ ] Imports use package structure
- [ ] No syntax errors (run `python -c "from mcp_coder.cli.commands.define_labels import execute_define_labels"`)
