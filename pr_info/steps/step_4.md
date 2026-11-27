# Step 4 — Task outcomes: prompt, `delete_this_file`, outcome lines in **Changes**

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **this step only** (`pr_info/steps/step_4.md`).
> TDD: write the tests first, then the code. Run pylint, the fast pytest set and mypy; all
> must pass. Run the formatter before committing. One commit.

## WHERE

- `src/mcp_coder/workflows/review/reviewer.py` — task prompt text in `_run_reviewer`; new
  `parse_task_outcomes`
- `src/mcp_coder/prompts/prompts.md` — both reviewer headers' **Fixes** paragraph
- `src/mcp_coder/workflows/review/core.py` — keep the task reply; backstop `changes=`
- `tests/workflows/review/test_reviewer.py`, `tests/prompts/test_prompt_loader.py`,
  `tests/workflows/review/test_core_round_outcomes.py` — tests

## WHAT

```python
def parse_task_outcomes(text: str) -> list[str]:
    """Return the leading per-task outcome lines of a task-application reply.

    Reads lines from the start (blank lines skipped) while each matches
    ``applied`` or ``not applied: <reason>``, optionally after a ``-``, ``*`` or
    ``1.`` marker; stops at the first other line. Returned lines are stripped
    and without the marker.
    """
```

## HOW

- Task prompt (the `else` branch of `_run_reviewer`), e.g.:
  `"Apply the following fixes now with the mcp-workspace tools (edit_file, save_file,
  delete_this_file). After the edits, begin your final message with one line per task, in
  order: `applied` or `not applied: <reason>`. Then re-emit your structured report:\n"` +
  task lines.
- `prompts.md`: in both `Review Implementation Reviewer` and `Review Plan Reviewer`, the
  tool list `(`edit_file`, `save_file`)` becomes `(`edit_file`, `save_file`,
  `delete_this_file`)`.
- `core.py`:
  - `reviewer._run_reviewer(..., tasks=verdict.tasks, ...)` → assign the result to
    `apply_response`.
  - After it, `outcomes = reviewer.parse_task_outcomes(reviewer.report_text(apply_response))`.
  - Only the backstop write changes:
    `changes="\n".join(["applied" if applied else "no-op", *outcomes])`.
  - Commit-failed, push-failed, rebase-needed and terminal after-steps writes are untouched.

## ALGORITHM

```
_OUTCOME_RE = re.compile(r"^(?:[-*]|\d+[.)])?\s*((?:not applied:.*\S)|applied)$", re.IGNORECASE)
outcomes = []
for line in text.splitlines():
    if not line.strip(): (continue if not outcomes else break)
    m = _OUTCOME_RE.match(line.strip()); if not m: break
    outcomes.append(m.group(1))
return outcomes
```

## DATA

- `"applied\nnot applied: no PR exists\n\nfoo.py:1 — high — x"` →
  `["applied", "not applied: no PR exists"]`
- `"- applied\n- not applied: n/a"` → `["applied", "not applied: n/a"]`
- `"NO FINDINGS"` → `[]`
- **Changes** body: `"no-op\nnot applied: no PR exists"` (plain lines, not a list).

## Tests (write first)

`test_reviewer.py`:
- the DATA examples for `parse_task_outcomes`.
- task-resume prompt (`_call(session_id="rev-1", tasks=[...])`) contains `delete_this_file`,
  `applied`, `not applied: <reason>` and asks for them at the start of the final message,
  after the edits.

`test_prompt_loader.py`: both reviewer headers contain `delete_this_file`.

`test_core_round_outcomes.py`:
- round 1 `tasks`, `env.round_applied.return_value = False`, apply reply text
  `"not applied: no PR exists\nfoo.py:1 — high — x"`; round 2 dismisses. Round 1's
  **Changes** in the log is `no-op\nnot applied: no PR exists`.
- commit-failed (`env.commit_changes.return_value = False`) and push-failed
  (`env.push_changes.return_value = False`) rounds whose apply reply has outcome lines →
  **Changes** is still exactly `commit-failed` / `push-failed`.
