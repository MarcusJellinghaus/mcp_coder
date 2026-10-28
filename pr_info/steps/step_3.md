# Step 3 — Register the command name for the traffic log

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`).
> Implement only Step 3. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/mcp_workspace_github.py` (re-export)
- `src/mcp_coder/cli/main.py`
- `tests/cli/test_main.py`

## WHAT
- Shim: `from mcp_workspace.traffic_log import set_traffic_log_context`, add to
  `__all__` (comment: sourced from `mcp_workspace.traffic_log`, like `get_github_token`).
- `cli/main.py`:
  ```python
  def _command_name(args: argparse.Namespace) -> str:
      """Return the catalog name of the parsed command, e.g. "vscodeclaude launch"."""
  ```
  and in `main()`, directly after `args = parser.parse_args()`:
  ```python
  if args.command:
      set_traffic_log_context(_command_name(args))
  ```

## ALGORITHM
```
cmd = args.command
sub = getattr(args, f"{cmd.replace('-', '_')}_subcommand", None)
      or getattr(args, "commit_mode", None)
return f"{cmd} {sub}" if sub else cmd
```

## HOW
- Import `set_traffic_log_context` from `..mcp_workspace_github` (never from
  `mcp_workspace` directly).
- Tests (TDD), in `tests/cli/test_main.py`:
  - parametrized `_command_name(argparse.Namespace(...))`:
    `vscodeclaude`+`vscodeclaude_subcommand="launch"` → `"vscodeclaude launch"`,
    `gh-tool`+`gh_tool_subcommand="set-status"` → `"gh-tool set-status"`,
    `commit`+`commit_mode="auto"` → `"commit auto"`, `coordinator` → `"coordinator"`;
    each result is a key of `COMMAND_DESCRIPTIONS`.
  - `main()` with argv `["mcp-coder", "vscodeclaude", "status"]`: patch
    `mcp_coder.cli.main.set_traffic_log_context` and
    `mcp_coder.cli.main.execute_coordinator_vscodeclaude_status` with a shared
    `MagicMock` parent; assert the context call comes first, with `"vscodeclaude status"`.

## DATA
`_command_name` returns `str`.
