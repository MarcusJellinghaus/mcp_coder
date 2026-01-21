# Step 2: Implement `set_status` Command Module

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Step 1**: `pr_info/steps/step_1.md` (tests must pass)

## LLM Prompt
```
Implement Step 2 from pr_info/steps/summary.md:
Create the `set_status` CLI command in `src/mcp_coder/cli/commands/set_status.py`.
Follow the patterns from `src/mcp_coder/cli/commands/define_labels.py`.
The tests from Step 1 should pass after this implementation.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/set_status.py`

## WHAT - Main Functions

```python
def get_status_labels_from_config(project_dir: Path) -> dict[str, str]:
    """Load status labels from config and return {name: description} mapping.
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        Dict mapping label name to description
        e.g., {"status-05:plan-ready": "Implementation plan approved, ready to code"}
    """

def validate_status_label(label: str, valid_labels: set[str]) -> bool:
    """Check if label is a valid status label.
    
    Args:
        label: Label name to validate
        valid_labels: Set of valid label names from config
        
    Returns:
        True if valid, False otherwise
    """

def compute_new_labels(
    current_labels: set[str],
    new_status: str,
    all_status_names: set[str],
) -> set[str]:
    """Compute new label set: remove all status-*, add new_status.
    
    Args:
        current_labels: Current labels on the issue
        new_status: New status label to set
        all_status_names: All valid status label names
        
    Returns:
        New set of labels to apply
    """

def execute_set_status(args: argparse.Namespace) -> int:
    """Execute the set-status command.
    
    Args:
        args: Parsed CLI arguments with:
            - status_label: The status label to set
            - issue: Optional explicit issue number
            - project_dir: Optional project directory
            
    Returns:
        Exit code (0=success, 1=error)
    """
```

## HOW - Imports and Integration

```python
"""Set status CLI command implementation."""

import argparse
import logging
import sys
from pathlib import Path

from ...utils.git_operations.branches import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from ...utils.github_operations.issue_manager import IssueManager
from ...utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from ...workflows.utils import resolve_project_dir

logger = logging.getLogger(__name__)
```

## ALGORITHM - execute_set_status Pseudocode

```
def execute_set_status(args):
    1. project_dir = resolve_project_dir(args.project_dir)
    
    2. # Load and validate label
       status_labels = get_status_labels_from_config(project_dir)
       if not validate_status_label(args.status_label, set(status_labels.keys())):
           print error with available labels
           return 1
    
    3. # Get issue number
       if args.issue:
           issue_number = args.issue
       else:
           branch = get_current_branch_name(project_dir)
           issue_number = extract_issue_number_from_branch(branch)
           if not issue_number:
               print error about branch pattern
               return 1
    
    4. # Get current issue and compute new labels
       manager = IssueManager(project_dir)
       issue_data = manager.get_issue(issue_number)
       current_labels = set(issue_data["labels"])
       new_labels = compute_new_labels(current_labels, args.status_label, set(status_labels.keys()))
    
    5. # Apply new labels
       result = manager.set_labels(issue_number, *new_labels)
       if result["number"] == 0:
           return 1
       
       logger.info(f"Updated issue #{issue_number} to {args.status_label}")
       return 0
```

## DATA - Return Values

```python
# get_status_labels_from_config returns:
{
    "status-01:created": "Fresh issue, may need refinement",
    "status-02:awaiting-planning": "Issue is refined and ready for implementation planning",
    # ... all 10 status labels
}

# compute_new_labels returns:
{"status-05:plan-ready", "bug", "enhancement"}  # preserves non-status labels

# execute_set_status returns:
0  # success
1  # error (invalid label, no issue detected, API error)
```

## Error Messages

```python
# Invalid label
f"Error: '{label}' is not a valid status label.\nAvailable labels:\n{formatted_labels}"

# No issue from branch  
f"Error: Cannot detect issue number from branch '{branch}'.\n"
f"Branch must follow pattern: {{issue_number}}-title (e.g., '123-feature-name')\n"
f"Use --issue flag to specify issue number explicitly."

# GitHub API error
f"Error: Failed to update labels for issue #{issue_number}: {error}"
```
