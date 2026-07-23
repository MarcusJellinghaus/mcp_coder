# Step 7 — CLI wiring

Goal: expose `mcp-coder rebase` — catalog entry, parser, thin command that
resolves the least-privilege settings default (materializing a temp settings file
from the in-code constant, bypassing broad auto-detect) and calls
`run_rebase_workflow`, and the `main.py` route. One commit.

## WHERE
- MODIFY `src/mcp_coder/cli/command_catalog.py` — add `"rebase"` description +
  place it in a category (recommend BACKGROUND DEVELOPMENT, next to `implement`).
- MODIFY `src/mcp_coder/cli/parsers.py` — add `add_rebase_parser(subparsers)`.
- MODIFY `src/mcp_coder/cli/main.py` — import `execute_rebase`, call
  `add_rebase_parser`, route `elif args.command == "rebase"`.
- CREATE `src/mcp_coder/cli/commands/rebase.py` — `execute_rebase` +
  `_resolve_rebase_settings`.
- CREATE `tests/cli/commands/test_rebase.py`.
- MODIFY `tests/cli/test_help_anti_drift.py` if it enumerates commands.

## WHAT
```python
# cli/commands/rebase.py
def execute_rebase(args: argparse.Namespace) -> int: ...

def _resolve_rebase_settings(settings_arg: str | None, project_dir: str | None) -> str:
    """Explicit --settings via resolve_claude_settings_path; else materialize a
    temp settings file from REBASE_LLM_PERMISSIONS (bypassing the broad
    settings.local.json auto-detect)."""

# cli/parsers.py
def add_rebase_parser(subparsers: Any) -> None: ...
```

## HOW
- `add_rebase_parser`: mirror `add_create_plan_parser` flags via the shared arg
  helpers — `add_project_dir_arg`, `add_llm_method_arg`, `add_mcp_config_arg`,
  `add_settings_arg`, `add_execution_dir_arg` — plus
  `--base-branch` (default `None`). No `issue_number`, no
  `--update-issue-labels`/`--post-issue-comments` (no GitHub side-effects).
  `help=COMMAND_DESCRIPTIONS["rebase"]`; epilog documenting exit codes `0/1/2`.
- `_resolve_rebase_settings`: if `settings_arg` is not None →
  `resolve_claude_settings_path(settings_arg, project_dir)`; else → write
  `REBASE_LLM_PERMISSIONS` (from `mcp_coder.workflows.rebase_permissions`) as JSON
  to a temp file via `tempfile` (e.g. `tempfile.NamedTemporaryFile(suffix=".json",
  delete=False)`) and return that path. The temp file lives for the duration of
  the process/session.
- `execute_rebase`: mirror `execute_create_plan` shape — resolve project/execution
  dir, `resolve_llm_method` + `parse_llm_method_from_args`,
  `resolve_mcp_config_path`, then `run_rebase_workflow(project_dir, provider,
  args.base_branch, mcp_config, settings_file, execution_dir)`. Same
  ValueError/KeyboardInterrupt/Exception boundary returning `1`/`2`.
- `main.py`: register `add_rebase_parser(subparsers)` and route to
  `execute_rebase(args)`.

## ALGORITHM
```
execute_rebase:
  project_dir = resolve_project_dir(args.project_dir)
  execution_dir = resolve_execution_dir(args.execution_dir)
  provider = parse_llm_method_from_args(resolve_llm_method(args.llm_method)[0])
  mcp_config = resolve_mcp_config_path(args.mcp_config, project_dir=args.project_dir)
  settings_file = _resolve_rebase_settings(args.settings, args.project_dir)
  return run_rebase_workflow(project_dir, provider, args.base_branch,
                             mcp_config, settings_file, execution_dir)
```

## DATA
- `execute_rebase` → `int` exit code (`0/1/2`; `1` on caught boundary errors).
- `add_rebase_parser` → `None` (registers the subparser).

## TESTS (write first)
`test_rebase.py`:
1. Parser: `create_parser().parse_args(["rebase", "--base-branch", "main"])`
   yields `command == "rebase"` and `base_branch == "main"`; default
   `base_branch is None`.
2. `_resolve_rebase_settings(None, None)` returns a path to an existing temp
   `.json` file whose parsed contents equal `REBASE_LLM_PERMISSIONS`.
3. `_resolve_rebase_settings("x.json", dir)` delegates to
   `resolve_claude_settings_path` (patch it; assert called).
4. `execute_rebase` calls `run_rebase_workflow` with the parsed args and returns
   its exit code (patch `run_rebase_workflow` → e.g. `2`).
Update `test_help_anti_drift.py` expectations to include `rebase` if it checks the
catalog/help set.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`. Implement Step 7
> (TDD). First write `tests/cli/commands/test_rebase.py` per the four cases here
> and update `tests/cli/test_help_anti_drift.py` if it enumerates commands. Then:
> add `"rebase"` to `COMMAND_DESCRIPTIONS` and a category in `command_catalog.py`;
> add `add_rebase_parser` to `parsers.py` (create-plan-style flags plus
> `--base-branch`, no issue/label flags, exit-code epilog); create
> `cli/commands/rebase.py` with `execute_rebase` and `_resolve_rebase_settings`
> (default: materialize a temp JSON settings file from `REBASE_LLM_PERMISSIONS`,
> bypassing broad auto-detect);
> and wire import + `add_rebase_parser` + routing into `cli/main.py`. Run pylint,
> pytest (`-n auto`, unit markers), mypy; fix everything. Exactly one commit.
