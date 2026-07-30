# Step 3 — Review workflow reads PR review feedback (implementation lane only)

Depends on Step 1 (shim). Independent of Step 2. One commit.

PR-feedback threading is gated to the **implementation lane** via a new
`ReviewConfig` flag — aligned with the existing `inject_base_branch` /
`run_after_steps` split. The **plan lane** skips the `collect_branch_status`
GitHub call entirely.

## WHERE

- `src/mcp_coder/workflows/review/config.py` — new `thread_pr_feedback: bool`
  field on `ReviewConfig` (mirrors `inject_base_branch`): `True` for
  `REVIEW_IMPLEMENTATION`, `False` for `REVIEW_PLAN`.
- `src/mcp_coder/workflows/review/reviewer.py` — new `pr_note` kwarg on
  `_run_reviewer` (parallel to the existing `ci_note`).
- `src/mcp_coder/workflows/review/core.py` — a `_pr_feedback_note` helper, a
  per-round `collect_branch_status` call **gated on `config.thread_pr_feedback`**,
  and threading into both feed targets.
- `tests/workflows/review/test_reviewer.py` — `_run_reviewer` `pr_note` kwarg
  tests (tests mirror src).
- `tests/workflows/review/test_config.py` — assert the new flag per lane.
- `tests/workflows/review/test_core.py` (plan lane, `REVIEW_PLAN`) and
  `test_core_after_steps.py` (implementation lane, `REVIEW_IMPLEMENTATION`) —
  `_pr_feedback_note` unit + lane-gated core threading tests.

## WHAT

`config.ReviewConfig` — add a `thread_pr_feedback: bool` field (mirrors the
existing `inject_base_branch` / `run_after_steps` behaviour booleans), set
`True` in `REVIEW_IMPLEMENTATION` and `False` in `REVIEW_PLAN`. Only the
implementation lane fetches branch status and threads PR feedback; the plan lane
makes no GitHub call.

`reviewer._run_reviewer` — add `pr_note: str | None = None`, appended to a
**fresh** reviewer prompt the same way `ci_note` is (ignored on a
task-application resume):

```python
if ci_note:
    prompt = f"{prompt}\n\n{ci_note}"
if pr_note:
    prompt = f"{prompt}\n\n{pr_note}"
```

`core._pr_feedback_note` — framing wrapper (None-guarded):

```python
def _pr_feedback_note(pr_feedback_text: str | None) -> str | None:
    """Wrap PR review feedback as an actionable-findings note for the reviewer."""
    if not pr_feedback_text:
        return None
    return (
        "NOTE — open PR review feedback: the following unresolved threads / "
        "changes-requested / alerts were posted on this PR. Treat each as a "
        "finding: verify it, then address or justify dismissing it in your "
        f"report.\n\n{pr_feedback_text}"
    )
```

## HOW (integration points)

- `core.py` imports `collect_branch_status`:
  `from mcp_coder.checks.branch_status import collect_branch_status`.
- Inside `run_review_workflow`'s `for round_number in range(...)` loop, **before**
  the reviewer turn, fetch fresh status **only in the implementation lane** (so
  the plan lane makes no GitHub call, and resolved comments drop out per round):
  ```python
  status = None
  pr_note = None
  if config.thread_pr_feedback:
      status = collect_branch_status(project_dir)
      pr_note = _pr_feedback_note(status.pr_feedback_text)
  ```
- Fresh reviewer call gets the note (alongside the existing `ci_note`); on the
  plan lane `pr_note` is `None`, so nothing is appended:
  `reviewer._run_reviewer(..., ci_note=pending_ci_note, pr_note=pr_note)`.
  The task-application resume call keeps `ci_note=None` and passes no `pr_note`
  (default `None`).
- Supervisor gets the **raw** feedback appended to the reviewer report, guarded
  on both the flag (via `status is not None`) and non-empty text:
  ```python
  supervisor_report = report
  if status is not None and status.pr_feedback_text:
      supervisor_report = (
          f"{report}\n\n## Open PR review feedback\n\n{status.pr_feedback_text}"
      )
  verdict, supervisor_sid = reviewer._get_verdict(..., supervisor_report)
  ```
  (Name the status object `status` to avoid colliding with `report`, which is the
  reviewer's findings *text*.)

## ALGORITHM (per round, additions only)

```
if config.thread_pr_feedback:                         # implementation lane only
    status  = collect_branch_status(project_dir)      # fresh each round
    pr_note = _pr_feedback_note(status.pr_feedback_text)  # None if no/empty feedback
else:                                                 # plan lane: no GitHub call
    status, pr_note = None, None
run fresh reviewer with ci_note=pending_ci_note, pr_note=pr_note
supervisor_report = report (+ raw pr_feedback_text section if status present)
get verdict from supervisor_report
```

## DATA

- `config.thread_pr_feedback`: `bool` — gates the whole block. `False` on the
  plan lane keeps `status`/`pr_note` at `None` and makes no `collect_branch_status`
  call.
- `status.pr_feedback_text`: `Optional[str]` — `None` when no PR or the fetch was
  undeterminable. Both feed targets guard on it (and on `status is not None`).
- `_pr_feedback_note` returns `Optional[str]`.
- `_run_reviewer` signature gains `pr_note: str | None = None`; return type
  unchanged (`LLMResponseDict`).

## TESTS (TDD — write first)

Config (`tests/workflows/review/test_config.py`, extend `test_behaviour_flags`):
- `REVIEW_IMPLEMENTATION.thread_pr_feedback is True`;
- `REVIEW_PLAN.thread_pr_feedback is False`.

`_pr_feedback_note` unit:
- `None` in → `None` out; `""` in → `None` out.
- non-empty text → wrapped string containing the framing preamble AND the raw text.

`_run_reviewer` unit — in **`tests/workflows/review/test_reviewer.py`** (tests
mirror src; mock `prompt_llm`):
- fresh review with `pr_note="X"` → prompt passed to `prompt_llm` ends with `"X"`;
- `pr_note` present together with `ci_note` → both appended;
- task-application resume (`tasks=[...]`) ignores `pr_note`.
- Optional: backfill matching `ci_note` coverage while here if it is missing —
  not required scope.

Core threading / gating (mock `collect_branch_status`, `_run_reviewer`,
`_get_verdict`):
- **Plan lane** (`tests/workflows/review/test_core.py`, `REVIEW_PLAN`): assert
  `collect_branch_status` is **never called**, `_run_reviewer` receives
  `pr_note=None`, and the supervisor report is the bare reviewer report (no
  `## Open PR review feedback` section).
- **Implementation lane** (`tests/workflows/review/test_core_after_steps.py`,
  `REVIEW_IMPLEMENTATION`): assert `collect_branch_status` is called once per
  round; when `pr_feedback_text` is set, `_run_reviewer` receives a non-None
  `pr_note` and `_get_verdict` receives a report containing the raw feedback
  section; when `pr_feedback_text is None`, `pr_note` is `None` and the
  supervisor report has no `## Open PR review feedback` section.

## CHECKS

pylint / pytest (parallel, unit-only exclusions) / mypy — all pass.

## LLM PROMPT

> Implement **Step 3** of `pr_info/steps/summary.md` (issue #1068): feed PR review
> feedback into the review workflow — **implementation lane only** — per
> `pr_info/steps/step_3.md`.
>
> 1. In `workflows/review/config.py`, add a `thread_pr_feedback: bool` field to
>    `ReviewConfig` (mirroring `inject_base_branch`), set `True` in
>    `REVIEW_IMPLEMENTATION` and `False` in `REVIEW_PLAN`.
> 2. In `workflows/review/reviewer.py`, add a `pr_note: str | None = None` kwarg
>    to `_run_reviewer`, appended to the fresh reviewer prompt exactly like the
>    existing `ci_note` (ignored on the task-application resume).
> 3. In `workflows/review/core.py`, add the `_pr_feedback_note` framing helper
>    (None-guarded). In the round loop, **guarded on `config.thread_pr_feedback`**,
>    call `collect_branch_status(project_dir)` once before the reviewer turn
>    (fresh per round), pass the wrapped note to the fresh `_run_reviewer` via
>    `pr_note=`, and append the raw `status.pr_feedback_text` (None-guarded) to
>    the report handed to `_get_verdict`. On the plan lane the block is skipped
>    entirely (`pr_note=None`, no GitHub call). Import `collect_branch_status`
>    from `mcp_coder.checks.branch_status`.
> 4. Write the tests listed in the step: the config-flag assertions, the helper
>    unit, the `_run_reviewer` `pr_note` prompt assertions in
>    `tests/workflows/review/test_reviewer.py`, and the lane-gated core threading
>    tests (plan lane asserts `collect_branch_status` is NOT called; the
>    implementation lane asserts it IS called and the note is threaded). TDD:
>    tests first.
>
> Do NOT feed feedback via `collect_pr_feedback` directly — route through
> `collect_branch_status` (one door). Use MCP tools only. Run pylint, pytest
> (parallel, unit-only exclusions), mypy; all must pass. Produce exactly one commit.
