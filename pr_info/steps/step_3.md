# Step 3 — Replace the SKIP-action copies with `make_assessment(..., action=SKIP)`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly. Steps 1–2 are done: `make_assessment` exists in `tests/workflows/vscodeclaude/conftest.py`. This is a test-only refactor. Every call site must pass `action=SessionAction.SKIP` explicitly. Follow the summary's "Shared per-step check procedure". Produce exactly one commit.

## Precondition
`conftest.py` defines `def make_assessment(`. If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE
- `tests/workflows/vscodeclaude/test_sessions.py`: local `_make_assessment(folder, *, active)`, 2 call sites (about lines 261–262)
- `tests/workflows/vscodeclaude/test_active_set_invariant.py`: local `_assessment(folder, *, active)`, 1 call site (inside `_patch_common`'s `build_mock`)

## WHAT
- No new functions. Both local builders are deleted.

## HOW
**`test_sessions.py`:**
- Delete `def _make_assessment(...)`.
- Import `make_assessment` from `tests.workflows.vscodeclaude.conftest`.
- Change the calls to:
  ```python
  folder_a: make_assessment(folder_a, active=True, action=SessionAction.SKIP),
  folder_b: make_assessment(folder_b, active=False, action=SessionAction.SKIP),
  ```

**`test_active_set_invariant.py`:**
- Delete `def _assessment(...)`.
- Import `make_assessment`.
- Change the call to:
  ```python
  s["folder"]: make_assessment(s["folder"], action=SessionAction.SKIP) for s in sess
  ```

Then run `run_ruff_fix(select=["F401"], target_directories=["tests/workflows/vscodeclaude"])` and check the `types` imports that remain:

| File | Expected `types` import |
|---|---|
| `test_sessions.py` | `SessionAction`, `SessionAssessment` (annotation at about line 259), `VSCodeClaudeSession`, `VSCodeClaudeSessionStore` |
| `test_active_set_invariant.py` | `SessionAction`, `VSCodeClaudeSession` |

## ALGORITHM
```
for file in (test_sessions.py, test_active_set_invariant.py):
    delete local builder
    add conftest import of make_assessment
    rewrite each call: make_assessment(<same args>, action=SessionAction.SKIP)
ruff fix F401; verify the types imports match the table
```

## DATA
- Each call returns the same `SessionAssessment` as before, with `decision.action == SKIP`.

## Done when
- `search_files(pattern="make_assessment\\(", glob="tests/workflows/vscodeclaude/test_sessions.py")` → 2 hits, both containing `action=SessionAction.SKIP`.
- `search_files(pattern="make_assessment\\(", glob="tests/workflows/vscodeclaude/test_active_set_invariant.py")` → 1 hit, containing `action=SessionAction.SKIP`.
- `search_files(pattern="def _assessment", glob="tests/workflows/vscodeclaude/*.py")` → exactly 2 hits (`test_cleanup.py`, `test_audit.py`).
- The shared check procedure passes and the counts are unchanged.
- Commit: `test(vscodeclaude): use shared make_assessment with explicit SKIP action`
