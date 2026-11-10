# Step 1 — Delete unused legacy detection code (pure deletion)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`), then implement Step 1 only. It is a pure deletion: remove the unused legacy liveness code and its tests, fix the comments that mention it, and change no behaviour. Run the checks from the summary, then make one commit.

## Precondition

Search `src/` (`mcp__mcp-workspace__search_files`) for `is_session_active`, `session_has_artifacts`, `is_vscode_window_open_for_folder` and `is_vscode_open_for_folder`. If any call site outside their own definitions, the `sessions.py` imports or the `__init__.py` re-exports remains, write one line to `pr_info/.blocked.txt` and stop.

## WHERE / WHAT

**`src/mcp_coder/workflows/vscodeclaude/sessions.py`**
- Delete `session_has_artifacts(folder)` and `is_session_active(session)`.
- From the `.detection` import, remove `HAS_WIN32GUI`, `LAUNCH_GRACE_SECONDS`, `check_vscode_running`, `is_vscode_open_for_folder` and `is_vscode_window_open_for_folder`. Keep `get_pid_create_time`: `update_session_pid` uses it. Keep `UTC, datetime`: `save_sessions` uses them.
- Module docstring: `Handles JSON file I/O for session tracking.` (drop "and VSCode process checking").
- Keep `update_session_pid` unchanged.

**`src/mcp_coder/workflows/vscodeclaude/detection.py`**
- Delete `is_vscode_window_open_for_folder` and `is_vscode_open_for_folder`.
- Window-cache comment above `_vscode_window_cache`: drop the sentence naming `is_vscode_window_open_for_folder`. Keep "Each entry is (pid, title) where pid is the PID of the process that owns the window."
- `_title_binds` docstring: drop the "Ports … from `is_vscode_window_open_for_folder`" wording and describe it directly ("Reads window titles from the frozen snapshot …"). The title-format sentence is fixed in Step 7.

**`src/mcp_coder/workflows/vscodeclaude/__init__.py`**
- Remove `is_vscode_open_for_folder` and `is_vscode_window_open_for_folder` from the `.detection` import and from `__all__`.

**`src/mcp_coder/workflows/vscodeclaude/cleanup.py`**
- `_retry_to_be_deleted` docstring: replace "replacing the cmdline-only `is_vscode_open_for_folder` check and closing the second #38 door" with "the assessment, not a cmdline-only check, decides liveness".

## Tests

1. **Port first.** Read `test_sessions_active_fallback.py` and `test_sessions_active_grace.py`. For each scenario, check whether an `assess_liveness` / `gather_signals` test in `test_assessment_layers.py` / `test_detection.py` already covers it under today's rules:
   - title match → active
   - within grace + pid → active
   - within grace + cmdline → active
   - folder missing → inactive
   - unparsable `started_at` → age `inf`

   Port any that are missing into those files (pin `HAS_WIN32GUI`). Do **not** port the "title miss after grace → inactive" scenarios; Step 5 adds them under the new rule.
2. Delete `tests/workflows/vscodeclaude/test_sessions_active_fallback.py` and `tests/workflows/vscodeclaude/test_sessions_active_grace.py`.
3. `test_detection_probes.py`: move `test_get_vscode_window_titles_returns_pid_title_tuples` out of class `TestWindowTitleMatching` (module level, or its own small class), then delete `TestWindowTitleMatching`. Keep the `check_vscode_running` and `_get_vscode_processes` tests. Remove imports that become unused.
4. `test_sessions.py`: remove the `session_has_artifacts` import and its test class.
5. Search `tests/` for the four deleted names (including patch-target strings such as `"...sessions.is_vscode_open_for_folder"`) and remove or adapt every remaining use.

## Verification

- `mcp__mcp-tools-py__run_vulture_check`: nothing newly reported in `detection.py`, `sessions.py` or `__init__.py`.
- Checks from the summary.

## Commit

`refactor(vscodeclaude): delete unused legacy liveness detection`
