# Step 2: Implement `gh-tool get-base-branch` Command

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement the `gh-tool get-base-branch` CLI command. The tests from Step 1 should now pass.
Follow the existing CLI command patterns in the codebase (see check_branch_status.py as reference).
```

## WHERE

- **Create**: `src/mcp_coder/cli/commands/gh_tool.py`
- **Modify**: `src/mcp_coder/cli/main.py`

## WHAT

### New File: `gh_tool.py`

```python
def execute_get_base_branch(args: argparse.Namespace) -> int:
    """Execute get-base-branch command.
    
    Detection priority:
    1. GitHub PR base branch (if open PR exists)
    2. Linked issue's ### Base Branch section
    3. Default branch (main/master)
    
    Args:
        args: Parsed arguments with project_dir option
        
    Returns:
        0: Success, branch name printed to stdout
        1: Could not detect base branch
        2: Error (not a git repo, API failure)
    """
```

### Modify: `main.py`

```python
# Add import
from .commands.gh_tool import execute_get_base_branch

# Add parser in create_parser()
gh_tool_parser = subparsers.add_parser("gh-tool", help="GitHub tool commands")
gh_tool_subparsers = gh_tool_parser.add_subparsers(...)

get_base_branch_parser = gh_tool_subparsers.add_parser(
    "get-base-branch",
    help="Detect base branch for current feature branch",
    formatter_class=WideHelpFormatter,
    epilog="""Exit codes:
  0  Success - base branch printed to stdout
  1  Could not detect base branch
  2  Error (not a git repo, API failure)"""
)
get_base_branch_parser.add_argument("--project-dir", ...)

# Add routing in main()
elif args.command == "gh-tool":
    if args.gh_tool_subcommand == "get-base-branch":
        return execute_get_base_branch(args)
```

## HOW

### Imports in `gh_tool.py`

```python
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from ...utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
)
from ...utils.github_operations.issue_manager import IssueManager
from ...utils.github_operations.pr_manager import PullRequestManager
from ...workflows.utils import resolve_project_dir
```

## ALGORITHM

### `execute_get_base_branch` Core Logic

```
1. Resolve project directory (or use current dir)
2. Get current branch name
   - If None: return exit code 2 (error)
3. Try PR detection:
   - Create PullRequestManager
   - List open PRs
   - Find PR where head_branch == current_branch
   - If found: print base_branch, return 0
4. Try Issue detection:
   - Extract issue number from branch name
   - If found: get issue via IssueManager
   - If issue has base_branch: print it, return 0
5. Fallback to default branch:
   - Get default branch name
   - If found: print it, return 0
6. If all fail: return 1
```

### Error Handling

```python
try:
    # Main logic
except Exception as e:
    logger.error(f"Error detecting base branch: {e}")
    print(f"Error: {e}", file=sys.stderr)
    return 2  # Error exit code
```

## DATA

### Function Signature

```python
def execute_get_base_branch(args: argparse.Namespace) -> int:
    """
    Args:
        args.project_dir: Optional[str] - Project directory path
        
    Returns:
        int - Exit code (0=success, 1=detection failed, 2=error)
        
    Side Effects:
        - Prints branch name to stdout on success
        - Prints error message to stderr on failure
    """
```

### CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--project-dir` | str | None | Project directory (default: current) |

## Acceptance Criteria

- [ ] Command registered under `mcp-coder gh-tool get-base-branch`
- [ ] Detection priority: PR → Issue → Default
- [ ] Exit codes: 0 (success), 1 (no detection), 2 (error)
- [ ] Exit codes documented in `--help` epilog
- [ ] Output: branch name only to stdout
- [ ] All tests from Step 1 pass
- [ ] Follows existing code patterns (resolve_project_dir, logging)
