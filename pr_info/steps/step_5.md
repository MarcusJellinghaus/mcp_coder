# Step 5 — No-op note to the supervisor and severity-floor exemption

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **this step only** (`pr_info/steps/step_5.md`).
> TDD: write the tests first, then the code. Run pylint, the fast pytest set and mypy; all
> must pass. Run the formatter before committing. One commit.

## WHERE

- `src/mcp_coder/workflows/review/reviewer.py` — new `noop_note`; `supervisor_input` gains
  `noop_note`
- `src/mcp_coder/workflows/review/core.py` — `pending_noop_note` state, two call sites
- `src/mcp_coder/workflows/review/severity.py` — docstring of `pending_ci_note` only
- `tests/workflows/review/test_reviewer.py`,
  `tests/workflows/review/test_core_round_outcomes.py` — tests

## WHAT

```python
def noop_note(tasks: list[str], outcomes: list[str]) -> str:
    """Tell the supervisor that last round's tasks changed nothing.

    Lists the tasks and the reviewer's outcome lines, states that the tasks
    were NOT applied (so they are not "already fixed"), and asks for each to be
    re-issued as a file change, escalated, or dropped on purpose.
    """

def supervisor_input(
    report: str, status: BranchStatusReport | None, noop_note: str | None = None
) -> str: ...
```

## HOW

- `supervisor_input`: the `## Review state` section holds the PR-state line (when `status`
  is set) and the no-op note (when set), joined by a blank line; the section is emitted when
  either exists. So the plan lane gets the note but no PR line.
- `core.py`:
  - add `pending_noop_note: str | None = None` next to `pending_ci_note` and to the
    `nonlocal` line.
  - `supervisor_report = reviewer.supervisor_input(report, status, pending_noop_note)`.
  - `_apply_severity_floor(verdict, report, round_number, config, pending_ci_note or pending_noop_note)`.
  - at the backstop, after `outcomes` is known:
    `pending_noop_note = None if applied else reviewer.noop_note(verdict.tasks, outcomes)`.
    No other reset is needed: dismiss/escalate are terminal and every `tasks` round reaches
    the backstop again.
  - Update the backstop comment: the note, not the next reviewer, carries the finding.
- `severity.py`: the `pending_ci_note` arg doc says it is also the pending no-op note; any
  non-`None` value exempts the round. No signature change.
- Check `core.py` stays under 750 lines.

## ALGORITHM

```
lines = ["Last round's tasks were NOT applied: the round changed no file on the branch.",
         "They are not already fixed. Tasks:", *[f"- {t}" for t in tasks], "",
         "Reviewer outcome:", *(outcomes or ["(none reported)"]), "",
         "For each task: re-issue it as a change to files on the branch, escalate it if it "
         "needs a human, or drop it on purpose."]
return "\n".join(lines)
```

## DATA

- `noop_note(["Add a PR section"], ["not applied: no PR exists"])` → string containing
  `NOT applied`, `- Add a PR section`, `not applied: no PR exists`, `re-issue`,
  `escalate`, `drop`.

## Tests (write first)

`test_reviewer.py`:
- the DATA example; empty `outcomes` → `(none reported)`.
- `supervisor_input(report, None, "NOTE")` → `## Review state` with `NOTE`, no PR line.
- `supervisor_input(report, _status, "NOTE")` → PR line and `NOTE` in `## Review state`.

`test_core_round_outcomes.py`:
- round 1 `tasks` (`env.round_applied.side_effect = [False, True]`), apply reply
  `"not applied: no PR exists"`; round 2 dismisses. Round 2's supervisor prompt
  (`call_args_list[4].args[0]`) contains round 1's task text, `NOT applied` and
  `not applied: no PR exists`, outside `## Reviewer report` (after `## Review state`).
- after an applied round (`round_applied` True) the next supervisor prompt has no
  `NOT applied`.
- floor exemption (model on `test_pending_ci_note_exempts_round_from_severity_floor` in
  `test_core_after_steps.py`): `round_applied` False for rounds 1-2, round 3
  (`strict_from_round`) has a `_REPORT_MEDIUM` report and a `_TASKS` verdict → round 3
  still runs its apply-tasks resume (not downgraded to dismiss).
