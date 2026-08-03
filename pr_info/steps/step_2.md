# Step 2 — Relocate PR-feedback note helpers into `reviewer.py`

See `pr_info/steps/summary.md` (§"Module layout"). A behaviour-preserving refactor that
moves the prompt-input framing helpers out of `core.py` (part of getting `core.py` under
600). Their natural home is `reviewer.py`, which already owns the reviewer/supervisor turn
helpers and the prompt substitution.

## WHERE
- From: `src/mcp_coder/workflows/review/core.py`
- To: `src/mcp_coder/workflows/review/reviewer.py`
- Symbols moved: `_QUOTE_FENCE`, `_quote_pr_feedback`, `_pr_feedback_note`.
- Tests: `tests/workflows/review/test_reviewer.py` (move/keep the note-framing unit tests
  if any live in `test_core.py`; otherwise add small direct unit tests here).

## WHAT
Unchanged signatures, now in `reviewer.py`:
```python
_QUOTE_FENCE = "`````"
def _quote_pr_feedback(pr_feedback_text: str) -> str: ...
def _pr_feedback_note(pr_feedback_text: str | None) -> str | None: ...
```

## HOW
- Cut the three symbols (and their comments/docstrings verbatim) from `core.py` into
  `reviewer.py`.
- In `core.py`, replace the two use sites — building `pr_note` and building
  `supervisor_report` — with `reviewer._pr_feedback_note(...)` and
  `reviewer._quote_pr_feedback(...)`.
- No behaviour change. No public API change.

## ALGORITHM
_None — pure relocation._

## DATA
Identical strings returned; only the defining module changes.

## TDD
- These are pure string helpers; assert `test_reviewer.py` covers: `None`/empty →
  `None` note; non-empty → data-framing sentence + 5-backtick fence.
- The full `test_core.py` suite must stay green unchanged (behaviour identical).

## LLM PROMPT
> Implement Step 2 from `pr_info/steps/step_2.md` (see `pr_info/steps/summary.md`). Move
> `_QUOTE_FENCE`, `_quote_pr_feedback`, and `_pr_feedback_note` verbatim from
> `workflows/review/core.py` into `workflows/review/reviewer.py`, and update the two call
> sites in `core.py` to call them via the `reviewer` module. This is a behaviour-preserving
> refactor: the existing `test_core.py` must pass unchanged. Add/relocate direct unit tests
> in `tests/workflows/review/test_reviewer.py`. Run pylint, pytest (`-n auto` with the
> integration exclusions), and mypy; all must pass. One commit.
