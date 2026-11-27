# Step 3 — Supervisor file-change rule and PR-state line (`supervisor_input`)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **this step only** (`pr_info/steps/step_3.md`).
> TDD: write the tests first, then the code. Run pylint, the fast pytest set and mypy; all
> must pass. Run the formatter before committing. One commit.

## WHERE

- `src/mcp_coder/prompts/prompts.md` — `### Review Supervisor` block
- `src/mcp_coder/workflows/review/reviewer.py` — new `_pr_state_line`, `supervisor_input`
- `src/mcp_coder/workflows/review/core.py` — replace the inline `supervisor_report` block
- `tests/workflows/review/conftest.py` — `_status` gains PR defaults
- `tests/workflows/review/test_reviewer.py`, `tests/prompts/test_prompt_loader.py`,
  `tests/workflows/review/test_core_round_outcomes.py` — tests

## WHAT

```python
def _pr_state_line(status: BranchStatusReport) -> str:
    """One line saying whether a PR exists for the branch."""

def supervisor_input(report: str, status: BranchStatusReport | None) -> str:
    """Build the supervisor's input: the report, PR feedback and review state.

    ``status`` is ``None`` in the plan lane: no PR feedback, no PR-state line.
    """
```

## HOW

- Prompt: add one triage rule to the `Review Supervisor` header, worded for both lanes
  (plan files or code), e.g.:
  `- Tasks are file changes: every task must be a change to files on the branch. Do not issue
  a task for anything else (PR text, labels, other GitHub state, rewriting history). If such a
  finding needs a human, escalate and put the reason in escalate_reason.`
  The verdict format is unchanged. Do not start any body line with `#`.
- `reviewer.py`: import `BranchStatusReport, CIStatus` from `mcp_coder.checks.branch_status`
  (core already imports from there).
- `core.py`: replace

  ```python
  supervisor_report = report
  if status is not None and status.pr_feedback_text:
      supervisor_report = (...)
  ```

  with `supervisor_report = reviewer.supervisor_input(report, status)`. The existing
  undeterminable warning branch stays unchanged.
- `conftest.py` `_status(...)`: add params `pr_found: bool = False`,
  `pr_number: int | None = None` and set both on the `SimpleNamespace`.

## ALGORITHM

```
_pr_state_line:
  if status.pr_feedback_undeterminable or status.ci_status is CIStatus.UNKNOWN:
      return "PR: PR state unknown (status collection failed)."
  if status.pr_found: return f"PR: PR #{status.pr_number} exists for this branch."
  return "PR: no PR exists yet for this branch."
supervisor_input:
  parts = [report]
  if status and status.pr_feedback_text: parts.append("## PR review feedback\n\n" + _quote_pr_feedback(text))
  if status: parts.append("## Review state\n\n" + _pr_state_line(status))
  return "\n\n".join(parts)
```

The `## PR review feedback` section text must stay byte-identical to today's.

## DATA

- Plan lane: returns `report` unchanged.
- Impl lane, no PR, no feedback: `"<report>\n\n## Review state\n\nPR: no PR exists yet for this branch."`

## Tests (write first)

`test_prompt_loader.py`: the `Review Supervisor` prompt contains `files on the branch` and
`escalate_reason`.

`test_reviewer.py` (use `SimpleNamespace` statuses):
- `pr_found=False` → contains `no PR exists yet`.
- `pr_found=True, pr_number=12` → contains `PR #12`.
- `pr_feedback_undeterminable=True` → `PR state unknown`; `ci_status=CIStatus.UNKNOWN` →
  `PR state unknown` (both even when `pr_found=True`).
- `status=None` → returns the report unchanged.
- feedback text present → `## PR review feedback` before `## Review state`; neither inside
  the report text.

`test_core_round_outcomes.py`: implementation-lane dismiss run with default `_status()` →
supervisor prompt (`call_args_list[1].args[0]`) contains `no PR exists yet`; with
`collect_branch_status` returning `_status(pr_found=True, pr_number=7)` → contains `PR #7`.
Plan lane (`config=REVIEW_PLAN`) → supervisor prompt has no `## Review state`.
