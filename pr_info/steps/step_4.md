# Step 4: `mcp-coder setup` CLI command

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_4.md`) only. Step 3 must be done: if `mcp_coder.install.project_setup.run_setup` does not exist, write one line to `pr_info/.blocked.txt` and stop.
Write the tests first, then the implementation. Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Create `src/mcp_coder/cli/commands/setup.py`
- Modify `src/mcp_coder/cli/parsers.py` — `add_setup_parser`
- Modify `src/mcp_coder/cli/command_catalog.py` — `COMMAND_DESCRIPTIONS["setup"]`, add `"setup"` to the `"SETUP"` category after `"install"`
- Modify `src/mcp_coder/cli/main.py` — register parser, dispatch `args.command == "setup"`
- Modify `tests/cli/commands/test_help.py` — `test_command_categories_contains_all_commands` expects `"setup"`
- Modify `docs/cli-reference.md` — command list entry under `### Setup` linking `#setup-1`, and a `### setup` section after `### install`
- Create `tests/cli/commands/test_setup_command.py`

## WHAT

```python
# parsers.py
def add_setup_parser(subparsers: Any) -> None:
    # "setup", help=COMMAND_DESCRIPTIONS["setup"], formatter_class=WideHelpFormatter
    # add_project_dir_arg(parser, help="Project directory to set up (default: current directory)")
    # --refresh (store_true): pass --refresh to uv in the python built-in
    # --skip-overrides (store_true): skip [tool.mcp-coder.install-from-github]

# commands/setup.py
def execute_setup(args: argparse.Namespace) -> int:
    """0 on success; 1 on a config error, failed step or changed files."""
```

Description: `"Set up the project as declared in [tool.mcp-coder.setup]"`.

## ALGORITHM

```
project_dir = Path(args.project_dir or ".").resolve()
try: run_setup(project_dir, refresh=args.refresh, skip_overrides=args.skip_overrides)
except (ValueError, SetupError) as exc: logger.error(str(exc)); return 1
return 0
```

## HOW

- Same shape as `cli/commands/install.py`.
- `docs/cli-reference.md`: `tests/docs/test_cli_reference.py` fails for an undocumented command. The `### Setup` category heading already owns `#setup`, so the list link is `[setup](#setup-1)`. The section documents the flags, `[tool.mcp-coder.setup]` in one sentence, exit codes and the changed-files rule. Do not link `docs/configuration/setup.md` yet — it is created in step 10, which adds the link.

## Tests (`tests/cli/commands/test_setup_command.py`)

- Parser: `setup --project-dir X --refresh --skip-overrides` parses; defaults are `None/False/False`.
- `execute_setup` (patch `run_setup` in the command module): passes resolved dir and flags; `ValueError` → 1 with error logged; `SetupError` → 1; success → 0; no `--project-dir` → cwd.
- `main` dispatch reaches `execute_setup`.

## DATA

Exit code `int`.
