# Step 7 — Round context + prompt rules (supervisor + reviewers)

See `pr_info/steps/summary.md` (§"Round context by substitution only"). The advisory
prompt layer, threaded entirely by substitution so the stated `strict_from_round` matches
the enforced one (AC: "the value the prompt states is the same value the backstop
enforces"). Changes 2 and 3 are layers, not alternatives — this reduces how often the cap
is reached; Step 5 is the guarantee for when the LLM ignores it.

## WHERE
- `src/mcp_coder/workflows/review/reviewer.py` — `_run_reviewer`, `_get_verdict` gain
  round-context params + substitution.
- `src/mcp_coder/workflows/review/core.py` — pass `round_number` / `REVIEW_MAX_ROUNDS`
  into both calls; extend `_CI_NOTE`.
- `src/mcp_coder/prompts/prompts.md` — §Review Supervisor, §Review Plan Reviewer,
  §Review Implementation Reviewer.
- Tests: `tests/workflows/review/test_reviewer.py`.

## WHAT
```python
def _run_reviewer(..., round_number: int, max_rounds: int, ...) -> LLMResponseDict: ...
def _get_verdict(..., round_number: int, max_rounds: int, ...) -> tuple[Verdict | None, str | None]: ...
```

## HOW
- **Reviewer prompt (fresh only):** after the existing `{issue_number}` / `{base_branch}`
  replacements, also `.replace("{round_number}", str(round_number))`,
  `.replace("{max_rounds}", str(max_rounds))`, and
  `.replace("{strict_from_round}", str(config.strict_from_round))`.
- **Supervisor header:** in `_get_verdict`, after `get_prompt(...)` and before appending the
  report, substitute `{round_number}`, `{max_rounds}`, `{strict_from_round}`, and
  `{tie_break}` (from `config.tie_break`). The header is rebuilt every turn (including
  resumed ones), so round-varying substitution needs no new session plumbing.
- **core:** pass `round_number=round_number, max_rounds=REVIEW_MAX_ROUNDS` into the fresh
  `_run_reviewer` call and the `_get_verdict` call (the task-application resume needs no
  round context). Extend `_CI_NOTE` with: "Treat this CI failure as `critical` severity in
  your structured report."
- **prompts.md — §Review Supervisor**, add to the triage rules (all via placeholders):
  - Severity floor: "Findings carry a severity (`critical`/`high`/`medium`/`low`). Accept
    `critical`/`high` in any round. This is round `{round_number}` of `{max_rounds}`; from
    round `{strict_from_round}` onward do NOT accept `medium`/`low`-only findings — if
    nothing `critical`/`high` remains, dismiss."
  - Final round: "On the final round, dismiss unless a `critical`/`high` finding remains;
    escalate only if one does and it needs a human."
  - Re-litigation: "Do not re-accept a finding you already dismissed, or already had fixed,
    in an earlier round."
  - Tie-break: "When the call is borderline, {tie_break} rather than asking."
- **prompts.md — both reviewer sections**, add: "This is round `{round_number}` of
  `{max_rounds}`. From round `{strict_from_round}` onward only `critical`/`high` findings
  will be acted on — spend your effort there rather than cataloguing new `low`/`medium`
  nitpicks." (Reviewer severity floor derives from the same substituted
  `{strict_from_round}`, never restated free text.)

## ALGORITHM
_None — substitution + prompt text._

## DATA
Prompt strings gain round/threshold/tie-break context. `_run_reviewer` / `_get_verdict`
return types unchanged.

## TDD
- `test_reviewer.py`: the built supervisor prompt contains `str(config.strict_from_round)`
  and `config.tie_break`, and contains the round/max numbers passed in (AC: prompt value ==
  backstop value — assert the same `strict_from_round` int appears).
- The built fresh-reviewer prompt contains the substituted round/max/threshold values, and
  no unresolved `{round_number}` / `{max_rounds}` / `{strict_from_round}` / `{tie_break}`
  placeholders remain.
- Existing `_get_verdict` / `_run_reviewer` tests updated for the new required params.

## LLM PROMPT
> Implement Step 7 from `pr_info/steps/step_7.md` (see `pr_info/steps/summary.md`). Add
> `round_number` / `max_rounds` params to `_run_reviewer` and `_get_verdict` in
> `reviewer.py` and substitute `{round_number}`, `{max_rounds}`, `{strict_from_round}` (and
> `{tie_break}` in the supervisor header) using the existing `.replace` plumbing; pass
> `REVIEW_MAX_ROUNDS` and the loop's `round_number` from `core.py`. Extend `_CI_NOTE` to say
> the CI failure is `critical`. Update `prompts.md` §Review Supervisor (severity floor,
> final-round rule, re-litigation sentence, tie-break) and both reviewer sections (round
> context + threshold), using placeholders only — never restated free-text numbers. Write
> the substitution tests first (assert the enforced `strict_from_round` value appears and no
> placeholders remain). Run pylint, pytest (`-n auto` with integration exclusions), and mypy.
> One commit.
