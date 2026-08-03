# Step 3 — `ReviewConfig`: add `strict_from_round` and `tie_break`

See `pr_info/steps/summary.md` (§"New `ReviewConfig` fields"). Adds the two per-lane fields
that both the severity backstop (Step 5) and the prompt substitution (Step 7) read, so the
enforced number and the stated number share one source.

## WHERE
- `src/mcp_coder/workflows/review/config.py`
- Tests: `tests/workflows/review/test_config.py`

## WHAT
Add two fields to the frozen dataclass, **at the end** (after `failure_labels`, which has
no default), each with a default so existing instantiations remain valid:
```python
strict_from_round: int = 3
tie_break: str = ""
```
Set explicit values on both real instances:
- `REVIEW_PLAN`: `strict_from_round=3`, `tie_break="default to simpler plans"`
- `REVIEW_IMPLEMENTATION`: `strict_from_round=3`, `tie_break="default to better code quality"`

## HOW
- Field order matters: placing them after `failure_labels` with defaults avoids the
  "non-default after default" dataclass error and keeps existing positional/test fixtures
  valid.
- **Do not** remove the `"rounds"` key from `failure_labels` yet — `core.py` still uses it
  at the cap until Step 6. Its removal lands in Step 8.
- Extend the field-list docstring with the two new attributes.

## ALGORITHM
_None._

## DATA
`ReviewConfig` gains `strict_from_round: int` (3 for both lanes) and `tie_break: str`
(per-lane sentence). No other structural change.

## TDD
In `test_config.py`, first assert:
- `REVIEW_PLAN.strict_from_round == 3` and `REVIEW_IMPLEMENTATION.strict_from_round == 3`;
- `REVIEW_PLAN.tie_break == "default to simpler plans"`;
- `REVIEW_IMPLEMENTATION.tie_break == "default to better code quality"`.
Any local `ReviewConfig(...)` fixtures in this module keep working via the defaults; only
add explicit values where the test asserts them.

## LLM PROMPT
> Implement Step 3 from `pr_info/steps/step_3.md` (see `pr_info/steps/summary.md`). Add
> `strict_from_round: int = 3` and `tie_break: str = ""` to the frozen `ReviewConfig`
> dataclass (at the end, after `failure_labels`), document them, and set explicit values on
> `REVIEW_PLAN` (`3` / `"default to simpler plans"`) and `REVIEW_IMPLEMENTATION` (`3` /
> `"default to better code quality"`). Do NOT touch the `failure_labels["rounds"]` key yet.
> Update `tests/workflows/review/test_config.py` (tests first). Run pylint, pytest
> (`-n auto` with integration exclusions), and mypy; all must pass. One commit.
