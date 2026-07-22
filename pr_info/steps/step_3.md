# Step 3 — Pure decision logic

Goal: the two pure functions at the heart of the exit-code contract — outcome
marker parsing and the worst-case-wins pre-push decision. No git, fully
unit-testable. One commit.

## WHERE
- CREATE `src/mcp_coder/workflows/rebase.py` (module docstring + these two
  functions only; more added in later steps).
- CREATE `tests/workflows/rebase/test_decision.py`.

Note: this is a new module `mcp_coder/workflows/rebase.py`, distinct from the
existing non-LLM `mcp_coder/workflow_steps/rebase.py`.

## WHAT
```python
def _parse_outcome_marker(response_text: str) -> tuple[str | None, str | None]:
    """Extract (outcome, reason) from the LLM response.

    outcome is "success" | "aborted" | None (unparseable).
    reason is the REBASE_REASON text, or None.
    """

def _evaluate_pre_push(
    *,
    mid_rebase: bool,
    marker_outcome: str | None,
    rebase_success_shape: bool,
) -> str:
    """Return "push" or "abort" (worst-case-wins, git is authoritative)."""
```

## HOW
- Consumed by the orchestrator in Step 6. No external imports beyond stdlib
  (`re`).

## ALGORITHM
```
_parse_outcome_marker:
  scan lines (last-match-wins) for "REBASE_OUTCOME:" -> value.lower() in {success,aborted}
  scan for "REBASE_REASON:" -> stripped text (None if absent/"n/a")
  return (outcome_or_None, reason_or_None)

_evaluate_pre_push:
  if mid_rebase: return "abort"          # unfinished / crashed session
  if marker_outcome == "aborted": return "abort"   # trust the self-report
  if not rebase_success_shape: return "abort"       # git can't corroborate success
  return "push"                          # marker success/unparseable AND git confirms
```

## DATA
- `_parse_outcome_marker` → `tuple[str | None, str | None]`.
- `_evaluate_pre_push` → `Literal["push", "abort"]` (typed as `str`).

## TESTS (write first)
`test_decision.py`:
- `_parse_outcome_marker`: success marker → `("success", None)` when reason is
  "n/a"; aborted marker with reason → `("aborted", "conflict in X")`; missing
  marker → `(None, None)`; case-insensitive `SUCCESS`; ignores unrelated text.
- `_evaluate_pre_push` truth table:
  - `mid_rebase=True` → `"abort"` (regardless of the other two).
  - `marker_outcome="aborted"`, `rebase_success_shape=True` → `"abort"`.
  - `marker_outcome="success"`, `rebase_success_shape=False` → `"abort"`.
  - `marker_outcome=None`, `rebase_success_shape=True` → `"push"`.
  - `marker_outcome="success"`, `rebase_success_shape=True` → `"push"`.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement Step 3
> (TDD). First write `tests/workflows/rebase/test_decision.py` covering
> `_parse_outcome_marker` and `_evaluate_pre_push` per the truth table in this
> step. Then create `src/mcp_coder/workflows/rebase.py` with a module docstring
> and exactly these two pure functions (stdlib only). Do not add git logic yet.
> Run pylint, pytest (`-n auto`, unit markers), mypy; fix everything. Exactly one
> commit.
