# Step 3 — Review workflow reads PR review feedback

Depends on Step 1 (shim). Independent of Step 2. One commit.

## WHERE

- `src/mcp_coder/workflows/review/reviewer.py` — new `pr_note` kwarg on
  `_run_reviewer` (parallel to the existing `ci_note`).
- `src/mcp_coder/workflows/review/core.py` — per-round `collect_branch_status`,
  a `_pr_feedback_note` helper, and threading into both feed targets.
- `tests/workflows/review/` — `_pr_feedback_note` unit test + a core threading
  test.

## WHAT

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
  the reviewer turn, fetch fresh status (so resolved comments drop out):
  ```python
  status = collect_branch_status(project_dir)
  pr_note = _pr_feedback_note(status.pr_feedback_text)
  ```
- Fresh reviewer call gets the note (alongside the existing `ci_note`):
  `reviewer._run_reviewer(..., ci_note=pending_ci_note, pr_note=pr_note)`.
  The task-application resume call keeps `ci_note=None` and passes no `pr_note`
  (default `None`).
- Supervisor gets the **raw** feedback appended to the reviewer report (None-guarded):
  ```python
  supervisor_report = report
  if status.pr_feedback_text:
      supervisor_report = (
          f"{report}\n\n## Open PR review feedback\n\n{status.pr_feedback_text}"
      )
  verdict, supervisor_sid = reviewer._get_verdict(..., supervisor_report)
  ```
  (Name the status object `status` to avoid colliding with `report`, which is the
  reviewer's findings *text*.)

## ALGORITHM (per round, additions only)

```
status  = collect_branch_status(project_dir)          # fresh each round
pr_note = _pr_feedback_note(status.pr_feedback_text)   # None if no/empty feedback
run fresh reviewer with ci_note=pending_ci_note, pr_note=pr_note
supervisor_report = report (+ raw pr_feedback_text section if present)
get verdict from supervisor_report
```

## DATA

- `status.pr_feedback_text`: `Optional[str]` — `None` when no PR or the fetch was
  undeterminable. Both feed targets guard on it.
- `_pr_feedback_note` returns `Optional[str]`.
- `_run_reviewer` signature gains `pr_note: str | None = None`; return type
  unchanged (`LLMResponseDict`).

## TESTS (TDD — write first)

`_pr_feedback_note` unit:
- `None` in → `None` out; `""` in → `None` out.
- non-empty text → wrapped string containing the framing preamble AND the raw text.

`_run_reviewer` unit (mock `prompt_llm`):
- fresh review with `pr_note="X"` → prompt passed to `prompt_llm` ends with `"X"`;
- `pr_note` present together with `ci_note` → both appended;
- task-application resume (`tasks=[...]`) ignores `pr_note`.

Core threading (extend `tests/workflows/review/test_core.py`, mock
`collect_branch_status`, `_run_reviewer`, `_get_verdict`):
- `collect_branch_status` is called once per round;
- when `pr_feedback_text` is set, `_run_reviewer` receives a non-None `pr_note`
  and `_get_verdict` receives a report containing the raw feedback section;
- when `pr_feedback_text is None`, `pr_note` is `None` and the supervisor report
  is the bare reviewer report (no `## Open PR review feedback` section).

## CHECKS

pylint / pytest (parallel, unit-only exclusions) / mypy — all pass.

## LLM PROMPT

> Implement **Step 3** of `pr_info/steps/summary.md` (issue #1068): feed PR review
> feedback into the review workflow, per `pr_info/steps/step_3.md`.
>
> 1. In `workflows/review/reviewer.py`, add a `pr_note: str | None = None` kwarg
>    to `_run_reviewer`, appended to the fresh reviewer prompt exactly like the
>    existing `ci_note` (ignored on the task-application resume).
> 2. In `workflows/review/core.py`, add the `_pr_feedback_note` framing helper
>    (None-guarded). In the round loop, call `collect_branch_status(project_dir)`
>    once before the reviewer turn (fresh per round), pass the wrapped note to the
>    fresh `_run_reviewer` via `pr_note=`, and append the raw
>    `status.pr_feedback_text` (None-guarded) to the report handed to
>    `_get_verdict`. Import `collect_branch_status` from
>    `mcp_coder.checks.branch_status`.
> 3. Write the tests listed in the step (helper unit, `_run_reviewer` prompt
>    assertions, core threading with both `pr_feedback_text` set and `None`). TDD:
>    tests first.
>
> Do NOT feed feedback via `collect_pr_feedback` directly — route through
> `collect_branch_status` (one door). Use MCP tools only. Run pylint, pytest
> (parallel, unit-only exclusions), mypy; all must pass. Produce exactly one commit.
