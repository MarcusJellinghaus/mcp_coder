# Step 2 — Move commit / push / run_formatters into `workflow_steps`

**Goal:** Relocate the "commit / push (+ pre-commit format)" trio and the two commit
constants into `workflow_steps`, behavior-preserving. This is the foundation rebase
(Step 3) and CI (Step 4) depend on.

## WHERE

Create:
- `src/mcp_coder/workflow_steps/constants.py`
- `src/mcp_coder/workflow_steps/commit.py`
- `tests/workflow_steps/test_commit.py`

Modify:
- `src/mcp_coder/workflows/implement/constants.py` (remove the 2 constants; re-export them)
- `src/mcp_coder/workflows/implement/task_processing.py` (remove the 3 functions; keep the rest)
- `src/mcp_coder/workflows/implement/ci_operations.py` (import the 3 from `workflow_steps`)
- `src/mcp_coder/workflows/implement/rebase.py` (import `push_changes` from `workflow_steps`)
- `src/mcp_coder/workflows/implement/finalisation.py` (import `push_changes` from `workflow_steps`)
- `src/mcp_coder/workflows/implement/core.py` (import the 3 from `workflow_steps`)

Move test cases for these 3 functions out of `tests/workflows/implement/test_task_processing.py`
into `tests/workflow_steps/test_commit.py`.

## WHAT (signatures — unchanged)

In `workflow_steps/commit.py`:
```python
def run_formatters(project_dir: Path) -> bool
def commit_changes(project_dir: Path, provider: str = "claude") -> bool
def push_changes(project_dir: Path, force_with_lease: bool = False) -> bool
```

In `workflow_steps/constants.py`:
```python
PR_INFO_DIR = "pr_info"
COMMIT_MESSAGE_FILE = f"{PR_INFO_DIR}/.commit_message.txt"
```

## HOW (integration points)

- `commit.py` imports the same primitives the source used:
  `run_format_code` (mcp_tools_py), `commit_all_changes`, `git_push` (mcp_workspace_git),
  `generate_commit_message_with_llm`, `parse_llm_commit_response` (workflow_utils.commit_operations),
  and `COMMIT_MESSAGE_FILE` from `.constants` (the new `workflow_steps/constants.py`).
- `implement/constants.py`: delete the `PR_INFO_DIR` / `COMMIT_MESSAGE_FILE` definitions
  and add `from mcp_coder.workflow_steps.constants import COMMIT_MESSAGE_FILE, PR_INFO_DIR`.
  Every existing `from .constants import PR_INFO_DIR` line across `implement` keeps working.
- Update the 4 production consumers (`ci_operations`, `rebase`, `finalisation`, `core`)
  to import `commit_changes` / `push_changes` / `run_formatters` from
  `mcp_coder.workflow_steps.commit`.
- **Mandatory `task_processing.py` self-import (production, not reactive):**
  `process_single_task` (staying in `implement`) calls `run_formatters`,
  `commit_changes`, and `push_changes` (`task_processing.py:574/578/582`). After the
  three definitions move out, `task_processing.py` **requires**
  `from mcp_coder.workflow_steps.commit import commit_changes, push_changes, run_formatters`
  for its own remaining production body — add this unconditionally, independent of any
  test. (mypy/pytest would otherwise go RED on the missing names.)
- **Reactive shim:** this same import also serves as the `patch()` re-export target, so no
  separate shim is needed in `task_processing.py`. For any red
  `patch("…implement.task_processing.commit_changes")` (or push/run_formatters) target,
  the mandatory import above resolves it.

## ALGORITHM

Pure move — copy the three function bodies verbatim (preserving the commit-message-file
read → unlink → parse lifecycle in `commit_changes`), then repoint imports. No logic edits.

## DATA

`bool` returns as before. `workflow_steps/constants.py` holds two `str` constants.

## TDD

Move the existing `run_formatters` / `commit_changes` / `push_changes` test cases into
`tests/workflow_steps/test_commit.py`, updating patch targets to
`mcp_coder.workflow_steps.commit.*`. Confirm the **commit-message-file read/unlink
lifecycle** is covered (assert on the `project_dir / COMMIT_MESSAGE_FILE` read/unlink
path — NOT any substituted prompt string). If missing, add that characterization test
here before the move. Then perform the move and make the tests green.

## Checks / commit

`run_lint_imports_check` + `run_tach_check` (must stay green — `workflow_steps.commit`
only imports downward) + pylint / pytest / mypy. One commit:
`refactor(workflow_steps): move commit/push/run_formatters + commit constants`.

## LLM prompt

> Read `pr_info/steps/summary.md` (sections "What moves" and "Constants relocated by
> re-export") and `pr_info/steps/step_2.md`. Move `run_formatters`, `commit_changes`,
> and `push_changes` verbatim from `implement/task_processing.py` into a new
> `workflow_steps/commit.py`, and move `PR_INFO_DIR` / `COMMIT_MESSAGE_FILE` into a new
> `workflow_steps/constants.py`. Make `implement/constants.py` re-import those two
> constants. Repoint `ci_operations.py`, `rebase.py`, `finalisation.py`, and `core.py`
> to import the three functions from `mcp_coder.workflow_steps.commit`. Move the three
> functions' tests into `tests/workflow_steps/test_commit.py` with updated patch
> targets, ensuring the commit-message-file read/unlink lifecycle is characterized.
> Add a re-export shim in `task_processing.py` only if a test reveals a broken patch
> target. Do not change any logic. Verify all enforcers and the pylint/pytest/mypy
> trio are green, then produce one commit.
