# Summary — Review workflow: pass `branch_name` to `prompt_llm` (#1270)

## Problem

Both `prompt_llm` calls in the review workflow omit `branch_name`, so every
review-plan / review-implementation session lands in MLflow with
`branch_name=null`:

- reviewer — `_run_reviewer` in `src/mcp_coder/workflows/review/reviewer.py`
- supervisor — `_get_verdict` in the same file (inside the verdict-repair loop)

All other workflow callers (implement, create-plan, create-pr, rebase,
`workflow_steps/ci.py`, `workflow_utils/commit_operations.py`) already pass it.

## Architectural / design changes

None structural. The review workflow adopts the existing convention every other
workflow uses:

- Each helper computes `branch_name = get_branch_name_for_logging(project_dir)`
  itself and passes `branch_name=branch_name` to `prompt_llm`.
- `_get_verdict` computes it **once, before** the repair `while` loop; every
  `prompt_llm` call (initial verdict + repair retries) reuses it.
- No signature changes to `_run_reviewer`, `_get_verdict` or `core.py` —
  computing inside the helpers avoids growing already long parameter lists.
- No `issue_id` fallback: review always runs on a checked-out feature branch.
- Import style: `from mcp_coder.utils.git_utils import get_branch_name_for_logging`
  (function import, like `prompt_llm`), so tests can monkeypatch
  `reviewer.get_branch_name_for_logging`.

Out of scope: `step_name` in MLflow (no `prompt_llm` parameter exists; handed to
#1057).

## Test isolation

Every fixture that mocks `reviewer.prompt_llm` also patches
`reviewer.get_branch_name_for_logging`, so unit tests stay git-free:

- `env` in `tests/workflows/review/conftest.py`
- `mock_llm` and `mock_supervisor_llm` in `tests/workflows/review/test_reviewer.py`

## Files modified

| File | Change |
|---|---|
| `src/mcp_coder/workflows/review/reviewer.py` | import; compute + pass `branch_name` in `_run_reviewer` and `_get_verdict` |
| `tests/workflows/review/conftest.py` | `env` patches `reviewer.get_branch_name_for_logging` |
| `tests/workflows/review/test_reviewer.py` | `BRANCH` constant; both fixtures patch the helper; 2 new tests |

No files or folders are created (apart from these plan files).

## Steps

1. [step_1.md](./step_1.md) — tests + implementation for both call sites (one commit).

A single step: the two call sites share the import and fixture patches and
form one atomic fix; splitting them would leave a commit with half the fix.
