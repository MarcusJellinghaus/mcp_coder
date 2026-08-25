# Step 4 — Nine call sites default to `project_dir`

**Depends on:** Step 2 (the parameter), Step 3 (the reporting it now emits).

**This is the behaviour change.** Everything before it was preparation. After this commit,
`mcp-coder implement --project-dir <repo>` launches Claude with `cwd == <repo>` from any shell
working directory, and the driven project's `CLAUDE.md` reaches the agent.

---

## WHERE

### Source — six sites that already have `project_dir` in scope

| File | Line | `project_dir` source |
|---|---|---|
| `src/mcp_coder/cli/commands/check_branch_status.py` | 331 | `resolve_project_dir(...)` earlier in the function |
| `src/mcp_coder/cli/commands/create_plan.py` | 46 | `resolve_project_dir(args.project_dir)` at `:43` |
| `src/mcp_coder/cli/commands/create_pr.py` | 46 | same |
| `src/mcp_coder/cli/commands/implement.py` | 46 | same |
| `src/mcp_coder/cli/commands/rebase.py` | 81 | same (`:80`) |
| `src/mcp_coder/cli/commands/review.py` | 84 | same |

One-line edit each:
```python
execution_dir = resolve_execution_dir(args.execution_dir, project_dir=project_dir)
```
Pass the **resolved `Path`**, not `args.project_dir`.

### Source — three sites needing statement reordering

These resolve `execution_dir` *before* `project_dir`, so they need the statements moved, not
just a new argument.

| File | Move | To |
|---|---|---|
| `commit.py` | the `try:` block at `:72-78` | below `project_dir = ...` (`:80`), and **above** `validate_git_repository` (`:83`) |
| `prompt.py` | the `try:` block at `:46-52` | below the whole `env_vars` try/except (`:53-73`) |
| `icoder.py` | the `try:` block at `:49-54` | below the project-dir resolution block (`:56-67`) |

All three use their own `Path(args.project_dir) or Path.cwd()` rather than `resolve_project_dir`
(no git-repo requirement). **"Default to `project_dir`" means each command's own `project_dir`
— do not try to unify the three resolutions.** That is a separate concern and not in scope.

`commit.py` ordering matters: keeping `resolve_execution_dir` above `validate_git_repository`
preserves today's behaviour where a bad `--execution-dir` errors before a bad repo does.
`prompt.py`: `project_dir` is assigned inside the `try` at `:56-67` and stays bound even when
`prepare_llm_environment` raises `RuntimeError` at `:69`, so placing the resolver after the
whole block is safe.

### Source — help text

`src/mcp_coder/cli/shared_args.py:33-36`:
```python
_EXECUTION_DIR_HELP = (
    "DEPRECATED (removal tracked in #1132): execution directory: "
    "where Claude subprocess runs. Default: the project directory"
)
```
**Must keep the substring `where Claude subprocess runs`** — `tests/cli/test_shared_args.py:161-165`
(`test_canonical_help`) asserts on it and should survive unchanged.

### Tests

`tests/cli/test_shared_args.py:198-203` asserts `_EXECUTION_DIR_HELP` verbatim — update to match.

## HOW

The 14 assertions the issue lists (`assert_called_once_with(None)` ×11,
`assert_called_once_with(str(execution_dir))` ×3) break because the call gains an argument:

| File | Lines |
|---|---|
| `tests/cli/commands/test_create_pr.py` | 85, 178, 251, 534, 580 |
| `tests/cli/commands/test_implement.py` | 81, 129, 206, 539, 585 |
| `tests/cli/commands/test_create_plan.py` | 63, 185, 231 |
| `tests/cli/commands/test_review.py` | 76 |

Each becomes `assert_called_once_with(<first arg>, project_dir=<resolved project dir>)`.

> **Do not trust that list as exhaustive.** `tests/cli/commands/test_check_branch_status.py`
> (`:167`, `:226`) and `tests/cli/commands/test_rebase.py` (`:73`, `:107`, `:122`) also patch
> `resolve_execution_dir` and are not in the issue's list. Grep for `assert_called` on every
> `resolve_execution_dir` mock across `tests/` and fix whatever the test run reports.

**Comment, do not change** — `tests/cli/commands/test_commit.py:1099`, `:1129`, `:1158`,
`:1183` (their args at `:1110`, `:1140`, `:1169`, `:1194`). They call `execute_commit_auto`
with `project_dir="/repo"`, a path that does not exist, and do not patch
`resolve_execution_dir`. After the reorder that value becomes the default source, and they pass
**only because the default is not existence-validated** (Step 2). Add a one-line comment
recording that coupling so a future change to the validation rule surfaces here.

**Rename or fix the comment** — `tests/integration/test_execution_dir_integration.py:285-330`
(`test_prompt_command_none_execution_dir_uses_none_as_cwd`) passes `project_dir=None`, so both
the old and new defaults resolve to `Path.cwd()`. It still passes but its name and the comment
at `:328` now describe the wrong reason.

## ALGORITHM

`commit.py` after the reorder:

```
project_dir = Path(args.project_dir) if args.project_dir else Path.cwd()
try:    execution_dir = resolve_execution_dir(args.execution_dir, project_dir=project_dir)
except ValueError: log; return 1
success, error = validate_git_repository(project_dir)     # still owns bad-project_dir errors
```

## DATA

No return-type or data-structure changes. The observable change is the value of `cwd` handed to
the Claude subprocess (`claude_code_cli_streaming.py:154`) and the new `OUTPUT` lines from
Step 3.

## TESTS (write first)

TDD here is naturally red-first: **update the ~14+ assertions to expect `project_dir` before
touching the call sites**, run the suite, watch them fail, then change the call sites.

Add two focused tests:

1. In `tests/cli/commands/test_commit.py` — `execute_commit_auto` with a `project_dir` outside
   the CWD and no `--execution-dir` resolves the execution dir to that `project_dir`. Pins the
   reordered site.
2. In `tests/cli/test_shared_args.py` — the updated verbatim `_EXECUTION_DIR_HELP` assertion,
   plus keep `test_canonical_help` (`:161-165`) green.

`tests/integration/test_execution_dir_integration.py:234-281`
(`test_prompt_command_passes_execution_dir_to_subprocess`) already reaches the resolver through
`execute_prompt` and will emit the `DeprecationWarning` — expected, no action.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Because this is the behaviour-changing commit, also run the suite **without** the marker
exclusions once (`extra_args=["-n", "auto"]`) if the environment allows it — the integration
tests under `tests/integration/test_execution_dir_integration.py` are exactly the ones this
step moves.

Then `./tools/format_all.sh`, review the diff, commit.

## Commit message

```
Default the Claude subprocess cwd to project_dir (#1113)

All nine commands now pass their project_dir to resolve_execution_dir, so
headless runs launch Claude in the driven project instead of the shell's
working directory - which is where Claude discovers CLAUDE.md, since it has
no flag for it. commit.py, prompt.py and icoder.py needed statement
reordering to have project_dir in scope.

--execution-dir still wins when passed explicitly, with a deprecation
warning naming #1132.

Side effect, intended: Claude now also discovers <project_dir>/.claude/
settings.json and settings.local.json and merges them with the file passed
via --settings.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially "1. The anchor moves from the shell to the
> project" and "6. Side effects that are intended, not regressions") and
> `pr_info/steps/step_4.md`, then implement Step 4. This is the commit where behaviour actually
> changes.
>
> Pass `project_dir=` to `resolve_execution_dir` at all nine call sites. Six are one-line edits
> (`check_branch_status.py:331`, `create_plan.py:46`, `create_pr.py:46`, `implement.py:46`,
> `rebase.py:81`, `review.py:84`) — pass the already-resolved `project_dir` `Path`, not
> `args.project_dir`. Three need statement **reordering** because they resolve `execution_dir`
> first: `commit.py:74`, `prompt.py:48`, `icoder.py:51`. See the table in the step file for
> exactly where each block moves. In `commit.py`, keep `resolve_execution_dir` above
> `validate_git_repository` so a bad `--execution-dir` still errors first.
>
> Those three commands use their own `Path(args.project_dir) or Path.cwd()` rather than
> `resolve_project_dir`. Use each command's own `project_dir` — do **not** try to unify the
> three resolutions.
>
> Update `_EXECUTION_DIR_HELP` in `cli/shared_args.py:33-36` to state the new default and the
> deprecation. It must keep the substring "where Claude subprocess runs" so
> `tests/cli/test_shared_args.py:161-165` survives; update the verbatim assertion at `:198-203`.
>
> Follow TDD: update the call-argument assertions **first** (the step file lists 14 across
> `test_create_pr.py`, `test_implement.py`, `test_create_plan.py`, `test_review.py`), run the
> suite, watch them fail, then change the call sites. The issue's list is not exhaustive — also
> grep `tests/` for `assert_called` on `resolve_execution_dir` mocks; `test_check_branch_status.py`
> and `test_rebase.py` patch it too.
>
> Add a comment (no behaviour change) at `tests/cli/commands/test_commit.py:1099`, `:1129`,
> `:1158`, `:1183` noting they pass only because the `project_dir` default is not
> existence-validated. Rename or fix the stale comment at
> `tests/integration/test_execution_dir_integration.py:328`.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md), `run_mypy_check`. Fix
> everything before finishing. One commit.
