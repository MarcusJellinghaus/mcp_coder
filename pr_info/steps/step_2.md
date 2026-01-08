# Step 2: Integrate Command into CLI

## Overview

Add the `define-labels` subparser to `main.py` and include it in the help command output.

## WHERE

- **Modify**: `src/mcp_coder/cli/main.py`
- **Modify**: `src/mcp_coder/cli/commands/help.py`

## WHAT

### Changes to `main.py`:

1. Add import:
```python
from .commands.define_labels import execute_define_labels
```

2. Add subparser in `create_parser()`:
```python
define_labels_parser = subparsers.add_parser(
    "define-labels", help="Sync workflow status labels to GitHub repository"
)
define_labels_parser.add_argument(
    "--project-dir",
    type=str,
    default=None,
    help="Project directory path (default: current directory)",
)
define_labels_parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Preview changes without applying them",
)
```

**Note**: No `--log-level` argument - the parent parser already provides this. Users use:
```bash
mcp-coder --log-level DEBUG define-labels
```

3. Add routing in `main()`:
```python
elif args.command == "define-labels":
    return execute_define_labels(args)
```

### Changes to `help.py`:

Add to the COMMANDS section in `get_help_text()`:
```
    define-labels           Sync workflow status labels to GitHub repository
                           --project-dir PATH    Project directory (default: current)
                           --dry-run             Preview changes without applying
```

## HOW

### Integration points in `main.py`:

1. Import at top with other command imports (after existing imports like `execute_verify`)
2. Subparser after the `coordinator_parser` block
3. Command routing in the `main()` function after the coordinator elif block

### Integration point in `help.py`:

Add in `get_help_text()` function, in the COMMANDS section. Place it logically - either alphabetically or grouped with similar commands.

## ALGORITHM

N/A - This step is configuration/wiring only.

## DATA

### Argument structure:
```python
# After parsing "mcp-coder define-labels --dry-run"
args.command = "define-labels"
args.project_dir = None  # or provided path
args.dry_run = True
args.log_level = "INFO"  # inherited from parent parser
```

## LLM Prompt

```
Please implement Step 2 of the implementation plan in `pr_info/steps/step_2.md`.

Context: See `pr_info/steps/summary.md` for the overall plan.

Task: Integrate the `define-labels` command into the CLI:

1. In `src/mcp_coder/cli/main.py`:
   - Add import for `execute_define_labels` from `.commands.define_labels`
   - Add `define-labels` subparser with ONLY these options:
     - `--project-dir` (type=str, default=None)
     - `--dry-run` (action="store_true")
   - Do NOT add `--log-level` - parent parser already provides it
   - Add command routing to call `execute_define_labels(args)`
   
2. In `src/mcp_coder/cli/commands/help.py`:
   - Add `define-labels` command to the COMMANDS section in `get_help_text()`
   - Document both options (--project-dir and --dry-run)

Follow the existing patterns for other commands like `verify`, `commit`, `create-pr`.

Do not modify any other files in this step.
```

## Verification

- [ ] `mcp-coder define-labels --help` shows correct usage (only --project-dir and --dry-run)
- [ ] `mcp-coder help` lists `define-labels` command with options
- [ ] `mcp-coder --help` shows `define-labels` in command list
- [ ] `mcp-coder --log-level DEBUG define-labels --dry-run` works (log level from parent)
- [ ] No import errors when running CLI

### Code Quality Checks:
- [ ] `mcp__code-checker__run_pylint_check()` - No errors
- [ ] `mcp__code-checker__run_pytest_check()` - All tests pass
- [ ] `mcp__code-checker__run_mypy_check()` - No type errors
