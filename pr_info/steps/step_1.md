# Step 1 — Rename the conftest builder to `make_assessment`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly. This is a test-only refactor: no new tests and no production changes. Follow the summary's "Shared per-step check procedure" (baseline before editing, checks after). Produce exactly one commit.

## WHERE
- `tests/workflows/vscodeclaude/conftest.py`
- `tests/workflows/vscodeclaude/test_session_restart_lifecycle.py`
- `tests/workflows/vscodeclaude/test_session_restart_issue_status.py`

## WHAT
```python
def make_assessment(
    folder: str,
    *,
    active: bool = False,
    action: SessionAction = SessionAction.RESTART,
) -> SessionAssessment:
```

## HOW
**`conftest.py`:**
- Delete `_make_assessment` from the top of the file.
- Add `make_assessment` in the "Shared builders" section, directly after `make_signals`.
- Docstring: "Build a minimal :class:`SessionAssessment` for assessment consumer tests." Keep the note that consumers read `verdict.active` and `decision.action`, and that the rest is filled with neutral defaults.
- Reword the section comment so it no longer lists only the three `test_assessment_*` modules. For example: "Shared builders for the vscodeclaude test modules. Plain helpers, imported directly."
- Do not change the `types` import. Every name is still used.

**`test_session_restart_lifecycle.py` and `test_session_restart_issue_status.py`:**
- Change `from tests.workflows.vscodeclaude.conftest import _make_assessment` to `... import make_assessment`.
- Rename the calls with `edit_file(old_string="_make_assessment(", new_string="make_assessment(", replace_all=True)`. Leave the arguments unchanged.

## ALGORITHM
```
rule = TITLE if active else NO_MATCH
return SessionAssessment(
    folder, signals=make_signals(title_match=active),
    verdict=LivenessVerdict(active, rule),
    issue_state=IssueState(is_open=True, is_stale=False, is_blocked=False, is_unassigned=False, is_eligible=True),
    transition=Transition(flipped_to_inactive=False),
    decision=Decision(action=action, reason="", destructive=False),
    pid_needs_refresh=False, found_pid=None)
```

## DATA
- Returns a frozen `SessionAssessment` whose fields are identical to the old `_make_assessment` output.

## Done when
- `search_files(pattern="_make_assessment", glob="tests/workflows/vscodeclaude/conftest.py")` → 0 hits.
- `search_files(pattern="_make_assessment", glob="tests/workflows/vscodeclaude/test_session_restart_lifecycle.py")` → 0 hits.
- `search_files(pattern="_make_assessment", glob="tests/workflows/vscodeclaude/test_session_restart_issue_status.py")` → 0 hits.
- The shared check procedure passes and the collect-only and pass counts are unchanged.
- Commit: `test(vscodeclaude): rename conftest _make_assessment to make_assessment`
