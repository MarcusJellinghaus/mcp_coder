# Step 4 — Add `make_sample_assessment` and use it in explain and types tests

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` exactly. Steps 1–3 are done. This is a test-only refactor. Asserted values must not change; only the unasserted pid and age in `test_explain.py` change (4321 becomes 1234, 42.5 becomes 12.5). Follow the summary's "Shared per-step check procedure". Produce exactly one commit.

## WHERE
- `tests/workflows/vscodeclaude/conftest.py`
- `tests/workflows/vscodeclaude/test_explain.py`
- `tests/workflows/vscodeclaude/test_types.py`

## WHAT
```python
def make_sample_assessment(folder: str = "/path/to/folder") -> SessionAssessment:
    """A rich, active sample assessment for serializer and explain output tests."""
```
`folder` stays positional-or-keyword, because `test_explain.py` passes it positionally.

## HOW
**`conftest.py`:**
- Add `make_sample_assessment` directly after `make_assessment` in the "Shared builders" section.
- The `types` imports stay unchanged.

**`test_explain.py`:**
- Delete `def _make_assessment(...)`.
- Import `make_sample_assessment` from `tests.workflows.vscodeclaude.conftest`.
- Replace `_make_assessment(` with `make_sample_assessment(` (`replace_all`). There are 4 sites: one with no argument, two positional (`"/a"` and `"/b"`), and one `s["folder"]`.

**`test_types.py`:**
- Delete `def _make_signals()` and `def _make_assessment()`.
- Add `from tests.workflows.vscodeclaude.conftest import make_sample_assessment, make_signals`.
- `test_detection_signals_frozen`: `signals = make_signals(title_match=True)`.
- Replace the other 4 `_make_assessment()` calls with `make_sample_assessment()`.

Then run `run_ruff_fix(select=["F401"], target_directories=["tests/workflows/vscodeclaude"])` and check the `types` imports that remain:

| File | Expected `types` import |
|---|---|
| `test_explain.py` | only `VSCodeClaudeSession` |
| `test_types.py` | everything except `DetectionSignals` and `SessionAssessment` (`Decision`, `IssueState`, `LivenessRule`, `LivenessVerdict`, `SessionAction`, `Transition` remain, because the frozen tests use them) |

## ALGORITHM
```
return SessionAssessment(
    folder=folder,
    signals=make_signals(title_match=True, pid_alive=True, found_pid=1234, age_seconds=12.5),
    verdict=LivenessVerdict(active=True, rule=LivenessRule.TITLE),
    issue_state=IssueState(is_open=True, is_stale=False, is_blocked=False,
                           is_unassigned=False, is_eligible=True, stale_target=None),
    transition=Transition(flipped_to_inactive=False),
    decision=Decision(action=SessionAction.KEEP_ACTIVE, reason="vscode running", destructive=False),
    pid_needs_refresh=False, found_pid=1234)
```

## DATA
- The output is identical to the old `test_types._make_assessment()`.
- Compared with the old `test_explain._make_assessment()`, only `found_pid` (signal and top level) and `age_seconds` differ. No test asserts on them.

## Done when (full issue verification)
- `search_files(pattern="def _make_assessment|def _make_signals|def _assessment\\(folder: str, \\*, active", glob="tests/workflows/vscodeclaude/*.py")` → 0 hits.
- `search_files(pattern="_make_assessment", glob="tests/**/*.py")` → 0 hits.
- `search_files(pattern="def _assessment", glob="tests/workflows/vscodeclaude/*.py")` → exactly 2 hits (`test_cleanup.py`, `test_audit.py`).
- ruff is clean (F401, F811, F821), and pylint, mypy and `run_format_code` pass.
- The shared check procedure passes and the counts are unchanged.
- Commit: `test(vscodeclaude): add shared make_sample_assessment for explain and types tests`
