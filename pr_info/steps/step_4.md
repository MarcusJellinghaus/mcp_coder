# Step 4 — `fix-ci` CLI verb

See [summary.md](./summary.md) for full context. Depends on Step 3
(`run_fix_ci_workflow` must exist).

## WHERE

- `src/mcp_coder/cli/commands/fix_ci.py` (create)
- `src/mcp_coder/cli/parsers.py` (modify)
- `src/mcp_coder/cli/main.py` (modify)
- `src/mcp_coder/cli/command_catalog.py` (modify)
- `tests/cli/commands/test_fix_ci.py` (create)
- `tests/cli/test_parsers.py` (modify)
- `tests/cli/commands/test_help.py` (modify)

## WHAT

```python
# cli/commands/fix_ci.py
def execute_fix_ci(args: argparse.Namespace) -> int: ...

# cli/parsers.py
def add_fix_ci_parser(subparsers: Any) -> None: ...
```

## HOW

`execute_fix_ci` is `execute_implement` (`cli/commands/implement.py`)
verbatim, with every `implement`/`"implement"` renamed to `fix_ci`/`"fix-ci"`
and the workflow import swapped:
```python
from ...workflows.fix_ci.core import run_fix_ci_workflow
...
return run_fix_ci_workflow(project_dir, provider, mcp_config, settings_file,
                            update_issue_labels, post_issue_comments)
```
Same helper imports from `..utils`: `log_command_startup`,
`parse_llm_method_from_args`, `resolve_claude_cwd`,
`resolve_claude_settings_path`, `resolve_issue_interaction_flags`,
`resolve_llm_method`, `resolve_mcp_config_path`.

`add_fix_ci_parser` is `add_implement_parser` verbatim, renamed, i.e.
`add_project_dir_arg` + `add_llm_method_arg` + `add_mcp_config_arg` +
`add_settings_arg` + `--update-issue-labels` + `--post-issue-comments`
(`BooleanOptionalAction`, `default=None`).

`command_catalog.py`:
- `COMMAND_DESCRIPTIONS["fix-ci"] = "Run the CI auto-fix loop to resolve a failing PR"`
- Add `"fix-ci"` to the `"BACKGROUND DEVELOPMENT"` category list, right
  after `"fix-conflict"`.

`main.py`:
- Import `execute_fix_ci` from `.commands.fix_ci` (alongside the existing
  `execute_fix_conflict` import).
- Import `add_fix_ci_parser` from `.parsers` (alongside `add_fix_conflict_parser`).
- Call `add_fix_ci_parser(subparsers)` right after
  `add_fix_conflict_parser(subparsers)`.
- Add `elif args.command == "fix-ci": return execute_fix_ci(args)` right
  after the `"fix-conflict"` branch.

## ALGORITHM

N/A — pure delegation/wiring, no new logic beyond what Step 3 already wrote.

## DATA

`execute_fix_ci` returns `int` (CLI exit code), identical contract to
`execute_implement`.

## Test-first steps

1. Create `tests/cli/commands/test_fix_ci.py` mirroring
   `tests/cli/commands/test_fix_conflict.py`'s structure but with the extra
   LLM-related mocks `test_implement.py` uses (`resolve_llm_method`,
   `parse_llm_method_from_args`, `resolve_mcp_config_path`,
   `resolve_claude_settings_path`, `resolve_issue_interaction_flags`,
   `resolve_claude_cwd`). Cover: success path, workflow-failure passthrough,
   invalid project dir, `KeyboardInterrupt`, unexpected exception, and a
   `TestFixCiCliIntegration` class with `test_fix_ci_command_registered`
   and `test_fix_ci_command_has_llm_arguments` (asserts `llm_method`,
   `mcp_config`, `settings` attributes *are* present — the opposite of
   `fix-conflict`'s "no LLM args" assertion).
2. In `tests/cli/test_parsers.py`, add `TestFixCiParser` mirroring
   `TestFixConflictParser` but asserting `hasattr(args, "llm_method")` is
   `True`.
3. In `tests/cli/commands/test_help.py`, add `"fix-ci"` to
   `expected_commands` right after `"fix-conflict"`.
4. Run all three — confirm red (module/wiring doesn't exist).
5. Implement `fix_ci.py`, `add_fix_ci_parser`, and the `main.py`/
   `command_catalog.py` wiring above.
6. Re-run — confirm green.

## Checks

`run_pytest_check`, `run_pylint_check`, `run_mypy_check` — all pass. Then
`run_format_code`, then commit.

## Commit

One commit: `feat(cli): add fix-ci command`.

## LLM Prompt

> Implement Step 4 of the plan in `pr_info/steps/summary.md`. Read that
> summary first, then follow `pr_info/steps/step_4.md` exactly: write the
> three test files/updates first (red), then create
> `src/mcp_coder/cli/commands/fix_ci.py`, add `add_fix_ci_parser` to
> `cli/parsers.py`, and wire both into `cli/main.py` and
> `cli/command_catalog.py` exactly as specified (green). Run
> pytest/pylint/mypy, format, and produce exactly one commit.
