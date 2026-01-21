# Step 3: Register Command in CLI Main

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Step 2**: `pr_info/steps/step_2.md` (command module must exist)

## LLM Prompt
```
Implement Step 3 from pr_info/steps/summary.md:
Register the `set-status` command in `src/mcp_coder/cli/main.py`.
Follow the existing patterns for other commands like `define-labels`.
```

## WHERE
- **File**: `src/mcp_coder/cli/main.py`
- **Sections to modify**:
  1. Import section (top of file)
  2. `create_parser()` function - add subparser
  3. `main()` function - add routing

## WHAT - Changes Required

### 1. Add Import
```python
from .commands.set_status import execute_set_status
```

### 2. Add Subparser in `create_parser()`
```python
# Set-status command - Update GitHub issue workflow label
# NOTE: Generate epilog dynamically from labels.json config (Decision #3)
set_status_parser = subparsers.add_parser(
    "set-status",
    help="Update GitHub issue workflow status label",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=_build_set_status_epilog(),  # Dynamic generation from config
)

# Helper function to generate epilog from config:
def _build_set_status_epilog() -> str:
    """Build epilog text with available labels from config."""
    try:
        from .commands.set_status import get_status_labels_from_config
        from ..workflows.utils import resolve_project_dir
        
        # Use package bundled config (always available)
        config_path = get_labels_config_path(None)
        labels_config = load_labels_config(config_path)
        
        lines = ["Available status labels:"]
        for label in labels_config["workflow_labels"]:
            lines.append(f"  {label['name']:30} {label['description']}")
        lines.append("")
        lines.append("Examples:")
        lines.append("  mcp-coder set-status status-05:plan-ready")
        lines.append("  mcp-coder set-status status-08:ready-pr --issue 123")
        return "\n".join(lines)
    except Exception:
        return "Run in a project directory to see available status labels."
)
set_status_parser.add_argument(
    "status_label",
    help="Status label to set (e.g., status-05:plan-ready)",
)
set_status_parser.add_argument(
    "--issue",
    type=int,
    default=None,
    help="Issue number (default: auto-detect from branch name)",
)
set_status_parser.add_argument(
    "--project-dir",
    type=str,
    default=None,
    help="Project directory path (default: current directory)",
)
```

### 3. Add Routing in `main()`
```python
elif args.command == "set-status":
    return execute_set_status(args)
```

## HOW - Integration Points

Location in `create_parser()`:
- Add after `define_labels_parser` block (similar command type)

Location in `main()`:
- Add in the command routing section, after `define-labels` case

## ALGORITHM - No complex logic

```
# In create_parser():
1. Create subparser with name "set-status"
2. Add epilog with available labels table
3. Add positional arg: status_label
4. Add optional arg: --issue
5. Add optional arg: --project-dir

# In main():
1. Check if args.command == "set-status"
2. Call execute_set_status(args)
3. Return the exit code
```

## DATA - Argument Namespace

After parsing `mcp-coder set-status status-05:plan-ready --issue 123`:

```python
args = argparse.Namespace(
    command="set-status",
    status_label="status-05:plan-ready",
    issue=123,
    project_dir=None,
    log_level="INFO",
)
```

## Verification

After implementation, verify with:
```bash
mcp-coder set-status --help
# Should display available labels and usage examples
```
