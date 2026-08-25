# Step 6 — Branch-name call sites use `project_dir`

**Depends on:** Step 4.
Independent of Steps 5 and 7.

Requirement 4 of the issue. Two lines.

---

## Be clear about what this buys

Once Step 4 has landed this is **not** fixing a live defect. `task_processing.py` receives
`execution_dir` from the CLI where it is never `None`, so `cwd` at `:396` already equals
`project_dir` and the branch name becomes correct on its own. The acceptance criterion
("LLM log filenames carry the branch name when the command is run from outside the repo")
would pass with this step omitted entirely.

What it *does* buy: the branch name stays correct **when `--execution-dir` is passed
explicitly**. That is the only reason to do it — and it is a two-line change, so there is no
cost to being correct. Do not let a later reader mistake it for the fix.

The other 10 `get_branch_name_for_logging` invocations in `src/` already pass `project_dir`;
these two are the outliers.

---

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py` — `:214-216` and `:434`
- `tests/workflows/implement/test_task_processing.py`

## WHAT

No signature changes. Two call-argument fixes.

`:214-216` — currently:
```python
branch_name = get_branch_name_for_logging(
    str(execution_dir) if execution_dir else str(project_dir)
)
```
becomes:
```python
branch_name = get_branch_name_for_logging(str(project_dir))
```

`:434` — currently `get_branch_name_for_logging(cwd)` becomes
`get_branch_name_for_logging(str(project_dir))`.

## HOW

- `project_dir` is in scope at both sites (`:241` uses `project_dir / ".mcp-coder"`; `:388`
  passes it to `_cleanup_commit_message_file`).
- **Do not touch the `execution_dir` arguments** to `prompt_llm` at `:223-225` and `:441`.
  Those correctly stay `execution_dir` — only the *branch-name lookup* moves to `project_dir`.
- **Leave `cwd` at `:396` alone.** `cwd = str(execution_dir) if execution_dir else str(project_dir)`
  contains a branch that is dead from the CLI path (`resolve_execution_dir` never returns
  `None`), but it is still the value passed as `execution_dir=cwd` at `:441`. #1132 removes it.

## ALGORITHM

None — direct substitution.

## DATA

`get_branch_name_for_logging(path: str) -> str`. Unchanged return; the only difference is which
directory is queried for the branch, which determines whether LLM log filenames carry a real
branch name or a fallback when the two directories differ.

## TESTS (write first)

In `tests/workflows/implement/test_task_processing.py`, patch `get_branch_name_for_logging` and
assert on its argument:

1. **The discriminating test:** call the task-processing entry point with `execution_dir` set to
   a directory **different from** `project_dir`, and assert `get_branch_name_for_logging` was
   called with `str(project_dir)`. This must fail before the change — if it passes beforehand,
   the test is not exercising the site.
2. Same assertion for the mypy-fix path (`:214-216`), which is a different code path from the
   implementation path (`:434`).
3. Regression: with `execution_dir == project_dir`, the argument is still `str(project_dir)`.

Check whether existing tests in that file assert on `get_branch_name_for_logging` arguments and
update them rather than adding duplicates.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Then `./tools/format_all.sh`, review the diff, commit.

## Commit message

```
Derive the implement branch name from project_dir, not execution_dir (#1113)

task_processing.py was the only place in src/ still reading the branch from
the execution directory; the other ten call sites already use project_dir.
After the cwd default change the two coincide unless --execution-dir is
passed explicitly, which is the case this keeps correct.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`, then implement Step 6.
>
> In `src/mcp_coder/workflows/implement/task_processing.py`, change the two
> `get_branch_name_for_logging` calls at `:214-216` and `:434` to pass `str(project_dir)`.
>
> Do **not** change the `execution_dir=` arguments passed to `prompt_llm` at `:223-225` and
> `:441` — only the branch-name lookup moves. Leave the `cwd` assignment at `:396` alone; its
> dead branch is removed by #1132.
>
> Follow TDD: write the three tests listed under TESTS in
> `tests/workflows/implement/test_task_processing.py` first. Test 1 is the discriminating one —
> it sets `execution_dir` to a directory different from `project_dir` and asserts the branch
> name is looked up from `project_dir`. Confirm it **fails** before you make the change; if it
> passes beforehand it is not exercising the call site. Check whether existing tests in that
> file already assert on `get_branch_name_for_logging` arguments and update those rather than
> adding duplicates.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md) and `run_mypy_check`. Fix
> everything before finishing. One commit.
