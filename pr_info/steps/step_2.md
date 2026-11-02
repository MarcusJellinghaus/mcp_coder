# Step 2 — `mcp-coder commit` as a leaf command, push on by default, docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Precondition: `_branch_refusal` exists in `src/mcp_coder/cli/commands/commit.py`
> (from step 1). If it does not, write one line to `pr_info/.blocked.txt` and stop.
> Follow TDD: update the tests first, then the implementation.
> Run pylint, mypy and the fast pytest suite plus `tests/docs` and
> `tests/integration/test_mcp_config_integration.py`; all must pass.
> Run `run_format_code`, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/parsers.py` — `add_commit_parsers`
- `src/mcp_coder/cli/main.py` — `_command_name`, `_handle_commit_command`, `main`
- `src/mcp_coder/cli/command_catalog.py` — `COMMAND_DESCRIPTIONS`, `COMMAND_CATEGORIES`
- `docs/cli-reference.md`
- Tests: `tests/cli/test_parsers.py`, `tests/cli/test_main.py`,
  `tests/cli/test_shared_args.py`, `tests/cli/test_help_anti_drift.py`,
  `tests/cli/commands/test_help.py`, `tests/cli/commands/test_commit.py`,
  `tests/integration/test_mcp_config_integration.py`

## WHAT

### `parsers.py`

```python
def add_commit_parsers(subparsers: Any) -> None:
    """Add the commit command parser."""
    commit_parser = subparsers.add_parser(
        "commit",
        help=COMMAND_DESCRIPTIONS["commit"],
        formatter_class=WideHelpFormatter,
    )
    commit_parser.add_argument("--preview", action="store_true", help=<unchanged>)
    add_llm_method_arg(commit_parser)
    add_project_dir_arg(commit_parser)
    commit_parser.add_argument(
        "--push",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Push to origin after commit; --no-push to skip",
    )
```

No default suffix in the help text (Python 3.11/3.12 append one automatically).

### `main.py`

- Delete `_handle_commit_command`.
- In `main()`: `elif args.command == "commit": return execute_commit_auto(args)`.
- `_command_name`: `sub = getattr(args, f"{cmd.replace('-', '_')}_subcommand", None)`;
  docstring: "followed by its subcommand if any".

### `command_catalog.py`

- `COMMAND_DESCRIPTIONS`: `"commit": "Auto-generate commit message using LLM"`
  replaces the `"commit auto"` key.
- TOOLS entry in `COMMAND_CATEGORIES`: `"commit"` replaces `"commit auto"`.

### `commit.py`

No change (keeps `getattr(args, "push", False)`).

## DATA

- Parsed args for `commit`: `preview: bool`, `llm_method`, `project_dir`,
  `push: bool` (default `True`). No `commit_mode` attribute.
- `mcp-coder commit auto` → top-level parser error "unrecognized arguments: auto", exit 2.

## Tests (update first)

- `tests/cli/test_parsers.py`
  - `test_execution_dir_flag_rejected`: argv `["commit", "--execution-dir", "/tmp/x"]`.
  - `TestCommitPushFlag`: docstring → "Tests for --push/--no-push on commit."
    - Rename `test_commit_auto_accepts_push_flag` → `test_commit_accepts_push_flag`, argv `("commit", "--push")`.
    - Replace the default-false test with `test_commit_push_defaults_true`: `("commit",)` → `args.push is True`.
    - Add `test_commit_no_push_flag`: `("commit", "--no-push")` → `args.push is False`.
- `tests/cli/test_main.py`
  - `_command_name` case: `(argparse.Namespace(command="commit"), "commit")`.
  - Replace `test_commit_no_subcommand_shows_help_hint` with
    `test_bare_commit_runs_commit_flow`: patch `mcp_coder.cli.main.execute_commit_auto`
    (return 0), argv `["mcp-coder", "commit"]`, assert result 0 and called once.
- `tests/cli/test_shared_args.py` (`TestLlmMethodMetavarIntegration`): path
  `("commit", "auto")` → `("commit",)`.
- `tests/cli/test_help_anti_drift.py`: remove `"commit"` from `GROUP_NAMES`;
  comment counting group nodes five → four.
- `tests/cli/commands/test_help.py`: `"commit auto"` → `"commit"` in the
  expected list and the TOOLS order.
- `tests/cli/commands/test_commit.py`: rename `TestCommitAutoParserNoMcpConfig`
  → `TestCommitParserNoMcpConfig`, `test_commit_auto_no_mcp_config_arg` →
  `test_commit_no_mcp_config_arg`, `test_commit_auto_accepts_llm_method` →
  `test_commit_accepts_llm_method`; drop `"auto"` from argv; replace
  "commit auto" in docstrings in this file with "commit".
- `tests/integration/test_mcp_config_integration.py`: rename
  `test_commit_auto_parser_rejects_mcp_config` → `test_commit_parser_rejects_mcp_config`;
  argv `["commit", "--mcp-config", ".mcp.linux.json"]`; docstring "commit command".

## Docs — `docs/cli-reference.md`

- Index row: ``| [`commit`](#commit) | Auto-generate commit message using LLM |``.
- Section heading `### commit` (required by `tests/docs/test_cli_reference.py`).
- Usage `mcp-coder commit [OPTIONS]`; examples `mcp-coder commit`,
  `mcp-coder commit --preview`, `mcp-coder commit --no-push`.
- Text to cover:
  - `--preview` shows the message and asks for confirmation; cancelling exits 0, no commit.
  - Push to origin is on by default; `--no-push` skips it. Push failure,
    including no `origin` remote, keeps the commit and exits 2.
  - Refused before committing (exit 1, no commit): protected branch (`main`,
    `master`, or the detected default branch) or detached / unreadable HEAD.
    Fallback: switch to a feature branch.
- Mention only flags that exist on the `commit` parser (no git flags).
- Do not touch `docs/tests/runtime_statistics.md` or `docs/tests/performance_data/*`.

## Done when

- `search_files` for `commit auto` and `commit_mode` finds matches only in
  `docs/tests/` historical data and `pr_info/`.
- pylint, mypy, fast pytest suite, `tests/docs` and the mcp-config integration test pass.
