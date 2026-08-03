# Step 5 — Severity backstop: downgrade `tasks` → `dismiss`

See `pr_info/steps/summary.md` (§"Backstop realized as a verdict transform"). The
deterministic half of change 1: at/after the lane's `strict_from_round`, a `tasks` verdict
with no `critical`/`high` finding is rewritten to `dismiss`. Realised as a small transform
right after the verdict is parsed, so the existing dismiss branch does the rest.

## WHERE
- `src/mcp_coder/workflows/review/core.py` (inside `run_review_workflow.body`, immediately
  after `last_verdict = verdict`, before the `verdict.decision == "dismiss"` dispatch).
- Import: `from .severity import max_severity` (Step 1).
- Tests: `tests/workflows/review/test_core.py` (plan lane) and
  `tests/workflows/review/test_core_after_steps.py` (impl lane / CI exemption).

## WHAT
No new function — an inline transform:
```python
verdict = _apply_severity_floor(verdict, report, round_number, config, pending_ci_note)
```
Either inline the ~5 lines directly, or add a tiny module-level pure helper in `core.py`:
```python
def _apply_severity_floor(verdict, report, round_number, config, pending_ci_note) -> Verdict:
```

## HOW
- Runs only when `verdict.decision == "tasks"`.
- Skipped entirely when `pending_ci_note` is set (AC: a CI-noted round is never
  downgraded — red CI is a must-fix, exempt from the floor).
- Uses `max_severity(report)` on the reviewer report (not the supervisor text).
- Log the downgrade at INFO so the review log/console records why the round became a
  dismiss.

## ALGORITHM
```
if verdict.decision != "tasks": return verdict
if pending_ci_note is not None: return verdict          # CI exemption
if round_number < config.strict_from_round: return verdict
top = max_severity(report)
if top is None: return verdict                          # fail open
if top in ("critical", "high"): return verdict
log("severity floor: downgrading tasks -> dismiss (max=%s)", top)
return Verdict("dismiss")
```

## DATA
Returns a `Verdict`: unchanged, or `Verdict("dismiss")`. When it returns `dismiss`, the
existing dismiss branch runs `_after_steps(is_dismiss=True)`, writes the round log and sets
the success label (terminal — dismiss is not a skip).

## TDD (mocked LLM)
- **AC1**: plan lane, `round_number >= 3`, supervisor returns `tasks`, reviewer report all
  `low`/`medium` → run returns `0` with the **success** label, no failure. (Drive rounds 1–2
  as `tasks` with a `high` present so they are not downgraded, round 3 all-`low`.)
- **AC1 negative**: report contains a `high` at round 3 → stays `tasks` (loop continues).
- **AC2 fail-open**: report with no severity token at round 3 → stays `tasks`.
- **Below floor**: all-`low` at round 2 → stays `tasks` (not downgraded before round 3).
- **AC6 CI exemption** (impl lane, `test_core_after_steps.py`): `pending_ci_note` set,
  round `>= 3`, report `medium` → **not** downgraded; the round still issues fix tasks.

## LLM PROMPT
> Implement Step 5 from `pr_info/steps/step_5.md` (see `pr_info/steps/summary.md`). In
> `workflows/review/core.py`, immediately after the verdict is parsed and stored, apply a
> severity floor that rewrites a `tasks` verdict to `Verdict("dismiss")` when
> `round_number >= config.strict_from_round`, `pending_ci_note` is None, and
> `max_severity(report)` is a non-None value not in `{"critical","high"}`; otherwise leave
> the verdict unchanged (fail open on `None`). Log the downgrade. Import `max_severity` from
> `.severity`. Write the mocked-LLM tests listed in the step first (plan lane in
> `test_core.py`; the CI-exemption case in `test_core_after_steps.py`), then implement. Run
> pylint, pytest (`-n auto` with integration exclusions), and mypy. One commit.
