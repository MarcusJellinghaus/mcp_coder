# Step 3 — Remove the `--execution-dir` flag and replace the resolver

**Context:** [summary.md](./summary.md), sections 1, 2 and 5.

After this step the flag is gone from the CLI and every command anchors Claude's working
directory with one uniform line. The workflow-layer `execution_dir` parameters still exist and
still receive a real path — now always `project_dir`. Step 4 deletes them.

**Why this order:** several workflow sites pass `execution_dir=str(execution_dir) if
execution_dir else None`. A `None` cwd is the #1113 bug. So the flag can only be removed while
the workflow parameter still receives a real path.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/cli/shared_args.py` | delete `_EXECUTION_DIR_HELP` (`:33`), `add_execution_dir_arg` (`:95`), the mention in the module docstring (`:4`) |
| `src/mcp_coder/cli/parsers.py` | delete the import (`:16`) and 10 call sites (`:113, 136, 155, 181, 207, 237, 267, 289, 432, 599`) |
| `src/mcp_coder/cli/utils.py` | `report_context_root` (`:420`) → one parameter; `resolve_execution_dir` (`:450`) → `resolve_claude_cwd`; update `__all__` (`:37`); drop the now-unused `warnings` import |
| `src/mcp_coder/cli/commands/*.py` | 9 commands: uniform resolver line, error-handler relabel/delete |
| `pyproject.toml` | delete the `execution_dir` marker (`:164`) |

## WHAT

```python
def report_context_root(project_dir: Path) -> None:
    """Log the Claude working directory and the project instructions in effect.

    Logs at OUTPUT level. Warns when no resolved file lies inside project_dir.
    """


def resolve_claude_cwd(project_dir: str | Path) -> Path:
    """Resolve the working directory for the Claude subprocess.

    Returns:
        Absolute, resolved path — always the project directory.
    """
```

`resolve_claude_cwd` **cannot raise**: no existence check (each command validates its own
`project_dir` and owns that error message), no `ValueError`, no deprecation warning.

## ALGORITHM

```
resolve_claude_cwd(project_dir):
    resolved = Path(project_dir).resolve()      # the one place resolution happens
    report_context_root(resolved)               # OUTPUT log + warn-if-none-inside
    return resolved

report_context_root(project_dir):
    log OUTPUT "Claude working directory: %s"
    hits = find_context_claude_md(project_dir)  # same dir for walk and inside-test
    log each hit (or "none found" and return)
    if all(is_outside_project_dir(hit, project_dir) for hit in hits): warn once
```

## HOW — integration points

**Uniform idiom in all nine commands** (`prompt`, `commit`, `implement`, `create_plan`,
`create_pr`, `review`, `rebase`, `check_branch_status`, `icoder`):

```python
project_dir = resolve_claude_cwd(project_dir)
```

placed exactly where `resolve_execution_dir(...)` is called today. `resolve_project_dir`
already resolves, so in eight commands this is idempotent; in `commit.py` (which builds
`Path(args.project_dir)` unresolved) it supplies the resolve the issue calls for. Delete every
`getattr(args, "execution_dir", None)` and every `logger.debug("Execution directory: …")`.

**Transitional, intentional:** where a command passed `execution_dir` onward, it now passes
`project_dir` — so the same value appears twice in the call. Step 4 deletes the duplicate.

| Command | Downstream site |
|---|---|
| `check_branch_status.py:345` | `execution_dir=project_dir` |
| `implement.py:77`, `create_plan.py:81`, `create_pr.py:77`, `review.py:115`, `rebase.py:105` | positional `project_dir` in the workflow call |
| `commit.py:95` | `generate_commit_message_with_llm(project_dir, provider, execution_dir=str(project_dir))` |
| `prompt.py:156, 196, 219` | `execution_dir=str(project_dir)`; metadata at `:170` → `str(project_dir)` |
| `icoder.py:202` | `execution_dir=str(project_dir)` |

**Error handling** (summary §5):

- **Relabel** the whole-body handlers to `"Invalid project directory: …"` —
  `create_plan.py:86-89`, `create_pr.py:83`, `implement.py:83`, `review.py:121`,
  `rebase.py:108-110`. They still catch `resolve_project_dir` failures. **`rebase.py` keeps
  exit code 2**; the other four keep 1. Only the message and the stale
  `# Handle invalid execution_dir` comment change.
- **Delete** the three now-dead narrow blocks: `commit.py:76-83` (with the obsolete
  `:74-75` ordering comment), `prompt.py:71-78`, `icoder.py:63-69`.

## DATA

`resolve_claude_cwd` returns an absolute `Path`. `report_context_root` returns `None` (logging
only). No other data structures change.

## TDD

**Tests first**, then implementation. Per-site handling — this is *not* a uniform delete:

| Test file | Action |
|---|---|
| `tests/cli/test_utils.py:221-364` (`TestResolveExecutionDir`) | **Split.** Delete the tests for an explicitly passed flag, its existence validation and its deprecation warning. **Retain and rename onto `resolve_claude_cwd`**: `test_none_with_project_dir_returns_project_dir` (`:280`), `test_project_dir_accepts_str_and_path` (`:287`), `test_relative_project_dir_is_resolved` (`:295`), `test_nonexistent_project_dir_is_not_validated` (`:312`). Rename the class to `TestResolveClaudeCwd`; the retained tests now call with one positional argument. |
| `tests/cli/test_main.py` | Delete `:448-513` — start at the `class TestExecutionDirArgument:` header (`:448`), **not** its docstring (`:449`), which would leave an empty class body. Delete `:683-692`. **Update, do not delete,** `test_check_branch_status_with_all_flags` (`:694-721`): it also covers `--project-dir`, `--fix`, `--llm-truncate`, `--llm-method`, `--mcp-config`. |
| `tests/cli/test_shared_args.py` | Delete the `add_execution_dir_arg` class (`:151-165`), `test_execution_dir_wording` (`:198-203`) and the import at `:21`. |
| `tests/icoder/test_cli_icoder_parser.py` | Delete `:40-44`. In `test_icoder_default_values` (`:47-54`) drop **only** the `execution_dir` assertion at `:54`. |
| `tests/cli/test_utils_context_root.py` | Delete **only** `test_resolver_reports_on_explicit_branch` (`:316-327`). Keep `test_resolver_reports_on_default_branch` (`:305-314`) and retarget it to `resolve_claude_cwd`; it pins the reporting this step preserves. |
| `tests/cli/commands/test_check_branch_status.py` | Delete `:167-199` inclusive at both ends. `test_read_only_invalid_execution_dir_returns_two` starts at `:170` but its three `@patch` decorators are at `:167-169`; starting at `:170` silently adds three mock arguments to the next test. **Stop at `:199`** — `:201-205` are decorators for `test_execute_check_branch_status_with_fixes_success` (`:208`), which survives. |
| `tests/integration/test_execution_dir_integration.py` | `git mv` → `tests/integration/test_claude_cwd_integration.py`. Keep **only** `test_prompt_command_no_project_dir_falls_back_to_cwd` (`:289`) and `test_prompt_command_defaults_cwd_to_project_dir` (`:345`), both in `TestSubprocessCwdParameter` (`:229`). They are the only tests patching `stream_subprocess`, i.e. spanning every layer this change rewrites. Remove the `execution_dir` marker applications (`:48`, `:150`, `:227`). |
| `tests/cli/commands/test_prompt.py` | Keep the shallower duplicates (`TestPromptExecutionDir`, `:706`) — different mocking depth, complementary — but **rename the class** (e.g. `TestPromptClaudeCwd`) and drop any case that passes a *distinct* execution dir. |
| `tests/cli/commands/test_*.py`, `tests/icoder/conftest.py:44` | Mechanical: delete `execution_dir=` attributes from `argparse.Namespace` fixtures; any assertion expecting a *distinct* execution dir to reach a workflow now expects `project_dir`. |

**New test** (replaces the deleted `TestExecutionDirArgument` in `tests/cli/test_main.py`):

```python
@pytest.mark.parametrize("argv", [
    ["prompt", "hi", "--execution-dir", "/tmp/x"],
    ["commit", "auto", "--execution-dir", "/tmp/x"],
    ["implement", "--execution-dir", "/tmp/x"],
    # … review-plan, review-implementation, create-plan, rebase, create-pr,
    #    branch-status, icoder
])
def test_execution_dir_flag_rejected(argv: list[str]) -> None:
    """The removed flag must fail loudly, not be silently ignored."""
    with pytest.raises(SystemExit):
        create_parser().parse_args(argv)
```

Then implement. Order that keeps the feedback loop tight: `utils.py` → the 9 commands →
`parsers.py` / `shared_args.py` → `pyproject.toml`.

## Verification beyond the gate

- `mcp-coder implement --project-dir X --execution-dir Y` → `error: unrecognized arguments`.
- A run from an unrelated shell cwd still logs `Claude working directory: <project_dir>` and
  the project instructions files (the report must not have gone missing).
- `--strict-markers` still passes after the marker is deleted (nothing applies it any more).

## Commit

```
Remove --execution-dir flag; replace resolver with resolve_claude_cwd

The flag's only job — MCP config discovery — was removed by #977, #981 and
#1113. Commands now anchor Claude's cwd with resolve_claude_cwd(project_dir),
which keeps the resolve and the #1113 context report. Part of #1132.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`, then implement step 3 only.
>
> Remove the `--execution-dir` CLI flag (`add_execution_dir_arg` and `_EXECUTION_DIR_HELP` in
> `src/mcp_coder/cli/shared_args.py`, plus its 10 call sites in `src/mcp_coder/cli/parsers.py`)
> and replace `resolve_execution_dir` in `src/mcp_coder/cli/utils.py` with
> `resolve_claude_cwd(project_dir: str | Path) -> Path`, which resolves the path, calls
> `report_context_root` and returns it — no existence check, no `ValueError`, no deprecation
> warning. Collapse `report_context_root`'s two parameters into one. Keep
> `find_context_claude_md` and `is_outside_project_dir` unchanged.
>
> In all nine commands use the single idiom `project_dir = resolve_claude_cwd(project_dir)`
> where `resolve_execution_dir(...)` is called today, and pass `project_dir` wherever the
> command passed `execution_dir` onward. **Do not change any workflow, `prompt_llm` or
> provider signature — that is step 4;** passing the same value twice in a call is the
> intended temporary state. Relabel the five whole-body `except ValueError` handlers to
> "Invalid project directory" (keeping `rebase.py`'s exit code 2) and delete the three now-dead
> narrow handlers in `commit.py`, `prompt.py` and `icoder.py`. Delete the `execution_dir` pytest
> marker from `pyproject.toml`.
>
> Follow TDD and the per-file test table in the step document exactly — it is not a uniform
> delete: some classes are split, some tests are only updated, and two line ranges have
> decorator-boundary traps. Rename
> `tests/integration/test_execution_dir_integration.py` to `test_claude_cwd_integration.py`
> (use `mcp__workspace__move_file` so history is preserved) keeping only the two
> `TestSubprocessCwdParameter` default-behaviour tests, and add the parametrized
> "flag is rejected" test shown in the step.
>
> Use MCP tools exclusively. Finish with `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n","auto","-m","not git_integration
> and not claude_cli_integration and not claude_api_integration and not formatter_integration
> and not github_integration and not langchain_integration"]`) and
> `mcp__tools-py__run_mypy_check`; all three must pass. One commit for this step.
