# Step 3: Integrate with CLI Main Entry Point

## Context
See `pr_info/steps/summary.md` for architectural context.

This step integrates the new `create-pr` command into the main CLI entry point, making it accessible via `mcp-coder create-pr` command.

## Objective
Add `create-pr` subcommand to `src/mcp_coder/cli/main.py` following the exact pattern from `implement` command integration.

---

## WHERE
**File to modify:** `src/mcp_coder/cli/main.py`

---

## WHAT - Changes Required

### 1. Add Import Statement

**Location:** Top of file with other command imports

```python
from .commands.create_pr import execute_create_pr
```

**Context (existing imports):**
```python
from .commands.commit import execute_commit_auto, execute_commit_clipboard
from .commands.help import execute_help, get_help_text
from .commands.implement import execute_implement
from .commands.prompt import execute_prompt
from .commands.verify import execute_verify
from .commands.create_pr import execute_create_pr  # ADD THIS LINE
```

### 2. Add Subcommand to Argument Parser

**Location:** In `create_parser()` function, after the `implement_parser` definition

**Code to add:**
```python
# Create PR command - Step X
create_pr_parser = subparsers.add_parser(
    "create-pr", help="Create pull request with AI-generated summary"
)
create_pr_parser.add_argument(
    "--project-dir",
    type=str,
    default=None,
    help="Project directory path (default: current directory)",
)
create_pr_parser.add_argument(
    "--llm-method",
    choices=["claude_code_cli", "claude_code_api"],
    default="claude_code_cli",
    help="LLM method to use (default: claude_code_cli)",
)
```

**Context (insert after):**
```python
# Implement command - Step 5
implement_parser = subparsers.add_parser(
    "implement", help="Execute implementation workflow from task tracker"
)
implement_parser.add_argument(
    "--project-dir",
    type=str,
    default=None,
    help="Project directory path (default: current directory)",
)
implement_parser.add_argument(
    "--llm-method",
    choices=["claude_code_cli", "claude_code_api"],
    default="claude_code_cli",
    help="LLM method to use (default: claude_code_cli)",
)

# CREATE-PR COMMAND GOES HERE (after implement)
```

### 3. Add Command Routing

**Location:** In `main()` function, after the `implement` command handler

**Code to add:**
```python
elif args.command == "create-pr":
    return execute_create_pr(args)
```

**Context (insert after):**
```python
elif args.command == "implement":
    return execute_implement(args)
elif args.command == "create-pr":
    return execute_create_pr(args)

# Other commands will be implemented in later steps
```

---

## HOW - Integration Points

### Full Context of Changes

**Import section (top of file):**
```python
from ..utils.log_utils import setup_logging
from .commands.commit import execute_commit_auto, execute_commit_clipboard
from .commands.create_pr import execute_create_pr  # NEW
from .commands.help import execute_help, get_help_text
from .commands.implement import execute_implement
from .commands.prompt import execute_prompt
from .commands.verify import execute_verify
```

**Argument parser section:**
```python
def create_parser() -> argparse.ArgumentParser:
    # ... existing code ...
    
    # Implement command
    implement_parser = subparsers.add_parser(
        "implement", help="Execute implementation workflow from task tracker"
    )
    # ... implement args ...
    
    # Create PR command (NEW)
    create_pr_parser = subparsers.add_parser(
        "create-pr", help="Create pull request with AI-generated summary"
    )
    create_pr_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    create_pr_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    
    return parser
```

**Command routing section:**
```python
def main() -> int:
    # ... existing code ...
    
    # Route to appropriate command handler
    if args.command == "help":
        return execute_help(args)
    elif args.command == "verify":
        return execute_verify(args)
    elif args.command == "prompt":
        return execute_prompt(args)
    elif args.command == "commit" and hasattr(args, "commit_mode"):
        if args.commit_mode == "auto":
            return execute_commit_auto(args)
        elif args.commit_mode == "clipboard":
            return execute_commit_clipboard(args)
        else:
            logger.error(f"Commit mode '{args.commit_mode}' not yet implemented")
            print(f"Error: Commit mode '{args.commit_mode}' is not yet implemented.")
            return 1
    elif args.command == "implement":
        return execute_implement(args)
    elif args.command == "create-pr":  # NEW
        return execute_create_pr(args)
    
    # Other commands...
```

---

## ALGORITHM - Integration Steps (Pseudocode)

```
1. Add import for execute_create_pr at top of file
2. In create_parser():
   - Add create_pr_parser subcommand after implement_parser
   - Add --project-dir argument
   - Add --llm-method argument
3. In main():
   - Add elif branch for "create-pr" command
   - Route to execute_create_pr(args)
4. No changes to error handling or other logic
```

---

## VALIDATION

### Manual Testing

```bash
# Test 1: Help text shows new command
mcp-coder --help
# Expected: "create-pr" appears in available commands

# Test 2: Command-specific help works
mcp-coder create-pr --help
# Expected: Shows create-pr specific help with --project-dir and --llm-method options

# Test 3: Execute with defaults (in a git repo)
mcp-coder create-pr
# Expected: Runs workflow (or fails with appropriate prerequisites check)

# Test 4: Execute with options
mcp-coder create-pr --project-dir /path/to/project --llm-method claude_code_api
# Expected: Uses specified options
```

### Automated Testing

```bash
# Run CLI command tests
pytest tests/cli/commands/test_create_pr.py -v

# Run all CLI tests
pytest tests/cli/ -v

# Code quality checks on modified file
pylint src/mcp_coder/cli/main.py
mypy src/mcp_coder/cli/main.py
```

---

## DATA - Changes Summary

**Lines added:** ~20 lines
**Lines modified:** 0 (only additions)
**Files changed:** 1 (`src/mcp_coder/cli/main.py`)

**New command signature:**
```bash
mcp-coder create-pr [--project-dir PATH] [--llm-method METHOD]
```

**Arguments:**
- `--project-dir`: Optional, defaults to current directory
- `--llm-method`: Optional, choices: ["claude_code_cli", "claude_code_api"], default: "claude_code_cli"

---

## LLM Prompt for This Step

```
I'm implementing Step 3 of the create_PR to CLI command conversion (Issue #139).

Context: Read pr_info/steps/summary.md for full architectural overview.

Task: Integrate create-pr command into main CLI entry point.

Step 3 Details: Read pr_info/steps/step_3.md

Instructions:
1. Open src/mcp_coder/cli/main.py
2. Add import: from .commands.create_pr import execute_create_pr
3. In create_parser(), add create-pr subcommand with --project-dir and --llm-method arguments (copy pattern from implement command)
4. In main(), add routing: elif args.command == "create-pr": return execute_create_pr(args)
5. Test manually: mcp-coder create-pr --help
6. Run automated tests: pytest tests/cli/ -v
7. Run code quality checks: pylint and mypy on main.py

Reference: Look at how "implement" command is integrated - follow exact same pattern.

Changes are minimal - just adding the new command to existing infrastructure.
```

---

## Verification Checklist

- [ ] Import added for `execute_create_pr`
- [ ] `create-pr` subcommand added to parser
- [ ] `--project-dir` argument added
- [ ] `--llm-method` argument added
- [ ] Command routing added in `main()`
- [ ] `mcp-coder --help` shows create-pr
- [ ] `mcp-coder create-pr --help` works
- [ ] CLI tests pass: `pytest tests/cli/ -v`
- [ ] Pylint passes on main.py
- [ ] Mypy passes on main.py

---

## Dependencies

### Required Before This Step
- ✅ Step 1 completed (CLI command interface exists)
- ✅ Step 2 completed (Workflow package exists)

### Blocks
- Step 4 (can proceed independently, but integration is needed for end-to-end testing)

---

## Notes

- **Minimal changes:** Only 3 additions (import, parser, routing)
- **Consistent pattern:** Exactly matches `implement` command integration
- **No breaking changes:** Existing commands unaffected
- **Easy to verify:** Simple manual testing shows it works
- After this step, `mcp-coder create-pr` will be fully functional!
