# Step 3 — Details for the three "general" failures without an exception

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only.
> TDD: write the tests first, then the code. Run pylint, mypy and pytest
> (`-n auto`, fast unit markers); all must pass. Format, then make exactly one commit.

## Precondition

If `tests/workflows/review/test_core_failure_detail.py` does not exist (Step 2 not
done), write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/review/core.py`
- `tests/workflows/review/test_core_failure_detail.py`

## WHAT / HOW

Add a `details=` keyword to three existing `_fail(..., "general", ...)` calls:

| Site | Condition | `details=` |
|------|-----------|------------|
| ~236 | `for … else:` empty report after retries | `f"Reviewer returned an empty report {EMPTY_REPORT_RETRIES} times"` |
| ~281 | `if verdict is None:` | `"Supervisor verdict could not be parsed after repair retries"` |
| ~429 | `if reviewer_sid is None:` | `"Reviewer returned no session id"` |

No other change; the round-log writes at these sites stay as they are.

## ALGORITHM

None — keyword argument additions only.

## DATA

The comment's `**Error:**` field shows the given sentence (existing `details`
semantics in `_fail`).

## Tests

One parametrized test in `test_core_failure_detail.py` (`config=REVIEW_PLAN`),
asserting `f"**Error:** {expected}"` is a line of the comment body:
- empty report: `prompt_llm.side_effect = [_reviewer("   ")] * EMPTY_REPORT_RETRIES`
  → `f"Reviewer returned an empty report {EMPTY_REPORT_RETRIES} times"`
- unparseable verdict: `[_reviewer()] + [_resp("no verdict here")] * (1 + VERDICT_REPAIR_RETRIES)`
  → `"Supervisor verdict could not be parsed after repair retries"`
  (`reviewer._get_verdict` makes `1 + VERDICT_REPAIR_RETRIES` supervisor calls)
- no session id: `[_reviewer(session_id=None), _resp(_TASKS)]`
  → `"Reviewer returned no session id"`
