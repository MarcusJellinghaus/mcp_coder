# Step 2 — Remove the PID refresh

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`), then implement Step 2 only. Remove the PID refresh entirely: `pid_needs_refresh`, the top-level `SessionAssessment.found_pid`, and the refresh branch in `apply_assessments`. Keep `DetectionSignals.found_pid`. Write the new test first, then the implementation. Run the checks from the summary, then make one commit.

## Rationale

The command-line scan only ever finds VSCode's shared main process, so copying its PID into a session never tracks that session's window. Removing the refresh before the additions in Steps 3–5 avoids adapting refresh tests that would be deleted anyway.

## WHERE / WHAT

**`src/mcp_coder/workflows/vscodeclaude/types.py`**
- `SessionAssessment`: delete the fields `pid_needs_refresh: bool` and `found_pid: int | None`.
- `_flatten()`: delete the top-level keys `"pid_needs_refresh"` and `"found_pid"`. Keep `signals.found_pid`.
- `to_explain()`: delete the two lines printing `pid_needs_refresh` and `found_pid`.

**`src/mcp_coder/workflows/vscodeclaude/assessment.py`**
- `assess_session`: drop the `pid_needs_refresh` computation and stop passing `pid_needs_refresh=` / `found_pid=` to `SessionAssessment`.
- `apply_assessments`: the loop body becomes only:
  ```python
  session["last_active"] = assessment.verdict.active
  session["last_active_rule"] = assessment.verdict.rule.value
  ```
- Drop `get_pid_create_time` from the `.detection` import.
- Docstrings:
  - `apply_assessments`: summary line becomes "Apply-only: advance ``last_active``, write the audit."; drop "PID refresh" from the body.
  - `build_active_session_set`: "the ``last_active`` advance lives in :func:`apply_assessments`".

**`src/mcp_coder/workflows/vscodeclaude/sessions.py`**
- `update_session_pid` docstring: drop "the field self-populates on the first cmdline-match refresh after launch". Keep "This is the only populator of ``vscode_pid_create_time``".

**Wording only**
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py` around line 287: "(PID refresh + last_active advance)" → "(last_active advance)".
- Same file around line 488: "no PID refresh or" → drop the PID-refresh part, keep the rest of the sentence.
- `src/mcp_coder/workflows/vscodeclaude/status.py` around line 279: "(the PID refresh + ``last_active`` advance live in …)" → "(the ``last_active`` advance lives in ``apply_assessments``)".

## Tests (write first)

**New test**, in `test_assessment_orchestration.py`: `test_apply_never_changes_vscode_pid`.
- Store one session with `vscode_pid=111`, `vscode_pid_create_time=1.0`.
- Assessment: active verdict, `signals.found_pid=222`.
- After `apply_assessments(..., write_audit=False)`, the stored session still has `vscode_pid == 111` and `vscode_pid_create_time == 1.0`, and `last_active is True`.
- Use the same store fixture / patching style as the neighbouring tests.

**Remove**
- The refresh tests in `test_assessment_layers.py` (`test_pid_needs_refresh_on_active_cmdline_match` and its `pid_needs_refresh is False` sibling, around lines 278–302).
- The refresh tests in `test_assessment_orchestration.py`, including any `get_pid_create_time` patch target in that file.

**Adapt**
- Drop `pid_needs_refresh=` / top-level `found_pid=` from every `SessionAssessment(...)` constructor: `conftest.py` (`make_assessment`, `make_sample_assessment`), `test_audit.py`, `test_cleanup.py`, `test_closed_issues_integration.py`, `test_status_display_scenario.py`, plus any other file `search_files` finds.
- Remove assertions on those keys in `test_audit.py` / `test_explain.py` / `test_types.py`.
- Stale wording:
  - `test_assessment_orchestration.py`: refresh mentions.
  - `test_explain.py`: "no PID refresh".
  - `test_sessions.py`: "PID refresh moved into apply_assessments".
  - `test_status_display_assessment_consumer.py`: "would trigger a PID refresh".

## Commit

`refactor(vscodeclaude): remove PID refresh from assessment apply`
