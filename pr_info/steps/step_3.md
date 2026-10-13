# Step 3 — fix-conflict CLI verb wiring

Reference: `pr_info/steps/summary.md`. Depends on Step 2
(`workflows/fix_conflict/core.py` must export
`run_fix_conflict_workflow(project_dir: Path) -> int`). This step makes
`mcp-coder fix-conflict --project-dir ...` a working command. The
`WORKFLOW_MAPPING`/Jenkins wiring that calls it comes in Step 4.

## Precondition check

Read `src/mcp_coder/cli/parsers.py` around `add_create_pr_parser`, and
`src/mcp_coder/cli/main.py` around its import block, `create_parser()`'s
`add_*_parser(subparsers)` calls, and the `elif args.command == "create-pr":`
dispatch line. If `add_create_pr_parser` is no longer immediately followed
by `add_coordinator_parsers` in the registration list, or the `elif`
dispatch chain no longer has a `create-pr` branch in that shape, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/fix_conflict.py` (new)
- `src/mcp_coder/cli/parsers.py` (modify — add `add_fix_conflict_parser`)
- `src/mcp_coder/cli/main.py` (modify — import + register + dispatch)
- `src/mcp_coder/cli/command_catalog.py` (modify — description + category)
- `tests/cli/commands/test_fix_conflict.py` (new)
- `tests/cli/test_parsers.py` (modify)
- `tests/cli/commands/test_help.py` (modify)

## WHAT

```python
# src/mcp_coder/cli/commands/fix_conflict.py

def execute_fix_conflict(args: argparse.Namespace) -> int:
    """Execute the fix-conflict workflow command.

    Args:
        args: Parsed arguments with `project_dir`.

    Returns:
        int: exit code from run_fix_conflict_workflow (0/1), or 1 on a
        resolution/argument/keyboard-interrupt error at the CLI boundary.
    """
```

```python
# src/mcp_coder/cli/parsers.py

def add_fix_conflict_parser(subparsers: Any) -> None:
    """Add the fix-conflict command parser (project-dir only, no LLM args)."""
```

## HOW

- `execute_fix_conflict` mirrors `execute_create_pr`'s structure minus the
  LLM/mcp-config/settings resolution it doesn't need:
  `resolve_project_dir(args.project_dir)` →
  `log_command_startup("fix-conflict", project_dir)` →
  `enable_crash_logging(project_dir, "fix-conflict")` → import
  `run_fix_conflict_workflow` from `...workflows.fix_conflict.core` (local
  import, same as `execute_rebase` does for `run_rebase_workflow`, to avoid
  module-load-time circularity) → call it → return its result. Catches
  `ValueError` (invalid project dir, return 1), `KeyboardInterrupt` (log via
  `OUTPUT`, return 1), and `Exception` (log with `exc_info=True`, return 1).
  No `resolve_claude_cwd` call — that's Claude-subprocess-specific and
  irrelevant here.
- `add_fix_conflict_parser`: `subparsers.add_parser("fix-conflict",
  help=COMMAND_DESCRIPTIONS["fix-conflict"], formatter_class=WideHelpFormatter)`
  then only `add_project_dir_arg(fix_conflict_parser)`. No
  `add_llm_method_arg`/`add_mcp_config_arg`/`add_settings_arg`.
- `main.py`: add `from .commands.fix_conflict import execute_fix_conflict`
  next to the `create_pr` import; add `add_fix_conflict_parser` to the
  `from .parsers import (...)` block and to the `create_parser()` body
  immediately after `add_create_pr_parser(subparsers)`; add
  `elif args.command == "fix-conflict": return execute_fix_conflict(args)`
  immediately after the `create-pr` branch.
- `command_catalog.py`: add
  `"fix-conflict": "Rebase onto base branch to resolve a merge conflict"` to
  `COMMAND_DESCRIPTIONS`, and `"fix-conflict"` to the `"BACKGROUND
  DEVELOPMENT"` list in `COMMAND_CATEGORIES`, after `"create-pr"`.

## ALGORITHM

```
project_dir = resolve_project_dir(args.project_dir)
log_command_startup("fix-conflict", project_dir)
enable_crash_logging(project_dir, "fix-conflict")
from ...workflows.fix_conflict.core import run_fix_conflict_workflow
return run_fix_conflict_workflow(project_dir)
# ValueError -> log, return 1
# KeyboardInterrupt -> log via OUTPUT, return 1
# Exception -> log with exc_info=True, return 1
```

## DATA

`execute_fix_conflict` returns `int` (0/1), same contract as
`run_fix_conflict_workflow`.

## TDD order

1. Write `tests/cli/commands/test_fix_conflict.py` first (mock
   `resolve_project_dir`, `run_fix_conflict_workflow`,
   `enable_crash_logging`), covering the success path and each exception
   branch. Confirm it fails (module doesn't exist).
2. Update `tests/cli/test_parsers.py`: add a `["fix-conflict"]` parse case
   (mirroring the existing `["create-pr"]` one at line ~220) asserting
   `args.command == "fix-conflict"` and `hasattr(args, "project_dir")`, and
   confirming it has no `llm_method` attribute.
3. Update `tests/cli/commands/test_help.py`:
   `test_command_categories_contains_all_commands` — add `"fix-conflict"`
   to `expected_commands` and bump `len(all_command_names) == 23` to `24`.
4. Confirm all three new/updated test files fail against current code.
5. Implement `fix_conflict.py`, the `parsers.py` addition, the `main.py`
   wiring, and the `command_catalog.py` entries to make them pass.

## Checks before commit

pylint, pytest (fast unit marker set), mypy,
`mcp__mcp-tools-py__run_format_code`. All must pass.

## Commit message

```
feat(cli): add fix-conflict command
```

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for the overall design, then implement
> `pr_info/steps/step_3.md` exactly as written. Follow TDD: write/update
> the three test files first and confirm they fail, then wire up
> `cli/commands/fix_conflict.py`, `cli/parsers.py`, `cli/main.py`, and
> `cli/command_catalog.py` to make them pass. If this step's "Precondition
> check" section fails, write one line to `pr_info/.blocked.txt` and stop.
> Otherwise make one commit containing all the changes, after formatters/
> pylint/pytest/mypy all pass.
