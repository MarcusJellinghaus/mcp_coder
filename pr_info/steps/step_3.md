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
set_status_parser = subparsers.add_parser(
    "set-status",
    help="Update GitHub issue workflow status label",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""Available status labels:
  status-01:created           Fresh issue, may need refinement
  status-02:awaiting-planning Issue is refined and ready for implementation planning
  status-03:planning          Implementation plan being drafted (auto/in-progress)
  status-04:plan-review       First implementation plan available for review/discussion
  status-05:plan-ready        Implementation plan approved, ready to code
  status-06:implementing      Code being written (auto/in-progress)
  status-07:code-review       Implementation complete, needs code review
  status-08:ready-pr          Approved for pull request creation
  status-09:pr-creating       Bot is creating the pull request (auto/in-progress)
  status-10:pr-created        Pull request created, awaiting approval/merge

Examples:
  mcp-coder set-status status-05:plan-ready
  mcp-coder set-status status-08:ready-pr --issue 123
""",
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
