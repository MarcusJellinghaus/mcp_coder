# review-implementation review log 1

## Round 1 — 2026-11-27
**Findings**:
Reviewing the #1487 diff against main; now checking how `write_round_log` renders the multi-line Changes field and the new tests.src/mcp_coder/workflows/review/reviewer.py:193 — low — `_OUTCOME_RE` only accepts a bare `applied`. A slightly different first line such as `applied: edited foo.py` or `applied.` stops `parse_task_outcomes` at line 222, and every outcome line for the round is lost, including any `not applied: <reason>` lines after it. **Changes** then shows only the token, and the no-op note says `(none reported)`. Accepting `applied` followed by optional punctuation or a short detail would keep the reasons.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/workflows/review/reviewer.py, loosen _OUTCOME_RE (line ~193) so an `applied` outcome line also matches when trailing punctuation or a short detail follows (e.g. `applied.`, `applied: edited foo.py`), while `not applied: <reason>` still parses as not-applied. parse_task_outcomes (line ~222) must keep the later outcome lines and their reasons, so they reach **Changes** and the no-op note. Add tests for `applied.`, `applied: <detail>`, and a mixed list where `not applied: <reason>` comes after an `applied: <detail>` line.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-27
**Findings**:
Reviewing the #1487 diff; now checking the reviewer unit tests, then I'll emit the report.src/mcp_coder/workflows/review/reviewer.py:222 — low — `parse_task_outcomes` stops at the first blank line once it has found an outcome. If the reviewer puts a blank line between its outcome lines (`applied\n\nnot applied: no PR exists`), only the first line is kept, so the `not applied` reason never reaches **Changes** or the no-op note. The docstring (line 204) says "blank lines skipped", which does not match the code. Fix: skip blank lines between outcome lines and stop only at the first non-outcome line; add a test case for this.
src/mcp_coder/workflows/review/reviewer.py:196 — low — `_OUTCOME_RE` accepts a `not applied` line only in the exact form `not applied: <reason>`. Round 1 loosened the same check for `applied`; this is the not-applied side of it. A first line such as `not applied — no PR exists` or a bare `not applied` stops parsing, and every outcome line for the round is lost. The no-op note then says `(none reported)`, and that no-op case is the one the reason matters for. Fix: accept the same punctuation-led separators as for `applied`, and allow `not applied` without a reason.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/workflows/review/reviewer.py, change parse_task_outcomes (around line 222) to skip blank lines between outcome lines. It should stop only at the first non-blank line that is not an outcome, which is what the docstring at line 204 says. Add a test where `applied`, a blank line, then `not applied: no PR exists` keeps both outcomes, including the not-applied reason.', 'In src/mcp_coder/workflows/review/reviewer.py, loosen the `not applied` branch of _OUTCOME_RE (around line 196). It should accept the same punctuation-led separators that the `applied` branch now accepts (e.g. `not applied — no PR exists`, `not applied. reason`), and also a bare `not applied` with no reason. Keep the reason text when one is given. Add tests for the dash-separated form, the bare form, and a bare `not applied` as the first line followed by more outcome lines.'], escalate_reason=None)
**Changes**:
applied
