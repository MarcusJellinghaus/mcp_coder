# Step 2 — Migrate `implement` onto `run_guarded` (pure refactor)

**Reference:** `pr_info/steps/summary.md` §implement. Depends on Step 1. `implement`'s
externally observable behavior must be **unchanged** — the existing failure-path tests
(`tests/workflows/implement/test_core*.py`, `test_failure_reporting.py`) are the regression
guard. One commit.

## WHERE

- Modify `src/mcp_coder/workflows/implement/failure_reporting.py`
- Modify `src/mcp_coder/workflows/implement/core.py`
- Modify `src/mcp_coder/workflows/implement/constants.py` (delete enum + private dataclass)
- Modify `src/mcp_coder/workflows/implement/__init__.py` (drop the `FailureCategory` /
  `WorkflowFailure` re-export)
- Modify `src/mcp_coder/workflows/implement/task_processing.py` (import move)
- Delete `src/mcp_coder/workflows/implement/llm_failures.py`
- Delete `tests/workflows/implement/test_llm_failures.py`
- Delete `tests/workflows/implement/test_constants.py`

## WHAT

`failure_reporting.py`:

```python
FAILURE_LABELS: dict[str, str] = {
    "general": "implementing_failed",
    "timeout": "llm_timeout",
    "mcp_unavailable": "mcp_unavailable",
    "task_tracker_prep_failed": "task_tracker_prep_failed",
    "no_changes_after_retries": "no_changes_after_retries",
    "ci_fix_exhausted": "ci_fix_needed",
}

@dataclass
class Progress:            # mutable holder read by the net's build_comment
    completed: int = 0
    total: int = 0

def format_failure_comment(stage, message, *, completed, total,
                           elapsed, build_url, diff_stat) -> str: ...

def _fail(project_dir, reason, *, stage, message, progress, start_time, build_url,
          update_issue_labels, post_issue_comments) -> int: ...
```

## HOW

- `format_failure_comment` reproduces the current `_format_failure_comment` output (header
  `## Implementation Failed`, Category = title-cased reason, Stage, Error, optional Progress /
  Elapsed / Build, and the `### Uncommitted Changes` block). Category text now derives from the
  `reason` string, not an enum name.
- `_fail`: `category = FAILURE_LABELS.get(reason, FAILURE_LABELS["general"])`; build comment via
  `format_failure_comment`; call shared `handle_workflow_failure(WorkflowFailure(category, stage,
  message, elapsed), comment, project_dir, from_label_id="implementing", …)`; `return 1`.
- `core.py`: keep the three prereq checks + `_attempt_rebase_and_push` **before** the guard
  (unlabeled, unchanged). Wrap the rest (config read → task loop → final mypy → finalisation →
  CI → success label) in a nested `def body() -> int:`. Define `progress = Progress()` and a
  local `fail = partial(...)` binding `project_dir/progress/start_time/build_url/flags`. Replace
  every `_handle_workflow_failure(WorkflowFailure(...)); reached_terminal_state = True; return 1`
  with `return fail(reason, stage=..., message=...)`. Update `progress.completed` /
  `progress.total` where `completed_tasks` / `total_tasks` were mutated. The final
  `return 0` stays.
- Deliberate LLM reasons unchanged: `process_task_with_retry` still returns `timeout` /
  `mcp_unavailable` / `no_changes_after_retries` / `error`(→`general`); final-mypy and CI use
  `llm_failure_reason(exc) or "general"`.
- `build_comment` closure for `run_guarded` reads `progress` + `outcome` and reuses
  `format_failure_comment`, so the SIGTERM/unexpected comment is byte-identical to today.
- `task_processing.py`: change `from .llm_failures import llm_failure_reason` →
  `from mcp_coder.workflow_utils.failure_handling import llm_failure_reason`.
- `constants.py`: delete `FailureCategory` and the private `WorkflowFailure` (and now-unused
  `Enum`/`dataclass` imports). Keep every other constant.
- `__init__.py`: remove `FailureCategory` / `WorkflowFailure` from the `from .constants import …`
  line (`__init__.py:13`) and drop their two entries from `__all__` (`__init__.py:29-30`). Without
  this, `import mcp_coder.workflows.implement` raises `ImportError` after the constants deletion.

## ALGORITHM — `run_implement_workflow` skeleton

```
if not check_git_clean/main_branch/prerequisites: return 1   # unchanged, unlabeled
_attempt_rebase_and_push(project_dir)
progress = Progress(); start = time.time(); build_url = env["BUILD_URL"]
fail = partial(_fail, project_dir, progress=progress, start_time=start, build_url=build_url, ...)
def body() -> int:  ... uses fail(...) at each deliberate failure; returns 0 on success
def build_comment(o): return format_failure_comment(o.stage, o.message, completed=progress.completed, ...)
return run_guarded(body, project_dir=project_dir, from_label_id="implementing",
                   general_category="implementing_failed", comment_header="## Implementation Failed",
                   build_comment=build_comment, update_issue_labels=..., post_issue_comments=...)
```

## DATA

- `FAILURE_LABELS: dict[str, str]` — full implement taxonomy (reason → label id).
- `_fail` / `run_guarded` → `int` (`1` deliberate, body's code on success/guard).
- `Progress` — mutable `(completed, total)` holder bridging body → net comment.

## TESTS (write/adjust first)

- Delete `test_llm_failures.py` (classifier now covered in `test_failure_handling.py`).
- Delete `test_constants.py` — it imports and directly tests the now-deleted `FailureCategory`
  enum and private `WorkflowFailure` dataclass, so it cannot be "updated to label-string
  assertions"; leaving it would fail pytest collection. (The enum-value↔label coupling it checked
  is now expressed by the `FAILURE_LABELS` dict; no replacement test is required for this step.)
- Keep all `test_core*` / `test_failure_reporting` behavior assertions; update imports/patch
  targets from `FailureCategory`/local `WorkflowFailure` to label-string / new helper names.
  Assert the deliberate paths still label `llm_timeout` / `mcp_unavailable` /
  `no_changes_after_retries` / `ci_fix_needed` / `implementing_failed`, and the net path
  (SIGTERM/unexpected) still labels `implementing_failed` with the progress-bearing comment.

## Verify

`run_pylint_check`, `run_pytest_check` (`-n auto` + unit-exclusion markers), `run_mypy_check`,
`run_lint_imports_check`.

## LLM Prompt

> Implement Step 2 of `pr_info/steps/summary.md` per `pr_info/steps/step_2.md`. Migrate the
> `implement` workflow onto `run_guarded` and a `FAILURE_LABELS` reason→label dict: add
> `FAILURE_LABELS`, `Progress`, `format_failure_comment`, and `_fail` to `failure_reporting.py`;
> rewrite `core.py`'s guarded region as a `body()` closure + local `fail` partial + `Progress`
> holder + `build_comment` closure; delete the `FailureCategory` enum and private
> `WorkflowFailure` from `constants.py`; repoint `task_processing.py`'s `llm_failure_reason`
> import to `workflow_utils.failure_handling`; delete `llm_failures.py` and its test. This is a
> **pure refactor** — keep implement's externally observable behavior (labels + comment content)
> identical; the existing implement failure-path tests are the regression guard (update only
> imports/patch targets). Run pylint, pytest (`-n auto` with unit-exclusion markers), mypy, and
> lint-imports. Produce exactly one commit.
