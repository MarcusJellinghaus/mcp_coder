# Step 1 — Split `test_sessions.py` into six files (tests only)

See [summary.md](./summary.md). Source is **not** touched in this step. One commit.

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`), then do this step exactly.
> This is a pure test-file split for issue #1319: move test classes verbatim with `mcp__mcp-tools-py__move_symbol` (dry run first) and never move code by hand. Hand edits are limited to import statements, merging duplicate imports, and the `.large-files-allowlist` entry. Use MCP tools only, no Bash for file work. Run all checks listed below, then make one commit.

## WHERE
- Source of the moves: `tests/workflows/vscodeclaude/test_sessions.py`
- New files, all in `tests/workflows/vscodeclaude/`: `test_detection_probes.py`, `test_sessions_lookup.py`, `test_sessions_active_fallback.py`, `test_sessions_active_grace.py`, `test_sessions_pid_identity.py`
- `.large-files-allowlist`

## WHAT
No new functions. These test classes move unchanged:

| `move_symbol` call (symbols in source order) | Destination |
|---|---|
| `TestVSCodeProcessNameMatching`, `TestWindowTitleMatching` | `test_detection_probes.py` |
| `TestGetSessionForIssueSoftDelete`, `TestWarnOrphanFolders` | `test_sessions_lookup.py` |
| `TestIsSessionActiveFallbackChain` | `test_sessions_active_fallback.py` |
| `TestLaunchGrace` | `test_sessions_active_grace.py` |
| `TestCreateTimeIdentityVerification` | `test_sessions_pid_identity.py` |

`_make_assessment`, `TestSessionManagement`, `TestSessionHasArtifacts` and `TestUpdateSessionStatus` stay in `test_sessions.py`.

## HOW
- **Imports.** The new files import from `mcp_coder.workflows.vscodeclaude.sessions` as the originals did. In this step every name still lives in `sessions`, so **no** import or patch target is re-pointed to `detection`; step 2 does that.
- **Patch-target strings:** no change in this step.
- **TDD:** not applicable (pure move). The moved tests are the safety net and must pass unchanged at their new locations.

## ALGORITHM
```
baseline = collect-only counts (test_sessions.py, ::TestIsSessionActiveFallbackChain, test_detection.py, dir total)
for each row in the WHAT table:
    move_symbol(dry_run=True) -> files touched must be exactly test_sessions.py + destination
    move_symbol(dry_run=False); read destination and check decorators/method-local imports
run_ruff_fix(select=["F401"]) on tests/workflows/vscodeclaude; merge duplicate import lines by hand
remove the allowlist entry (match by path); run checks; compare counts; commit
```

## Procedure
1. **Baseline** (no marker filter). Run each with `run_pytest_check(extra_args=["--collect-only", "-q", <path>])`:
   - `tests/workflows/vscodeclaude/test_sessions.py` → expect 68
   - `tests/workflows/vscodeclaude/test_sessions.py::TestIsSessionActiveFallbackChain` → expect 10
   - `tests/workflows/vscodeclaude/test_detection.py` → expect 13
   - `tests/workflows/vscodeclaude/` → record the number N (686 at planning time)

   If the first three differ from what is expected: write one line to `pr_info/.blocked.txt` and stop.

   Then run `run_pytest_check(extra_args=["-q", "tests/workflows/vscodeclaude/test_sessions.py", "tests/workflows/vscodeclaude/test_detection.py"])` → expect 81 passed.
2. **Five moves.** Use `mcp__mcp-tools-py__move_symbol` with `source_file="tests/workflows/vscodeclaude/test_sessions.py"`, a dry run first for each.
   - If a dry run lists any file other than `test_sessions.py` and its destination: write one line to `pr_info/.blocked.txt` and stop.
3. **Check each new file after its move:**
   - `@pytest.mark.parametrize` (two ids) is still on `test_guard_none_falls_through_to_pid_check` in `test_sessions_active_fallback.py`
   - in `TestWindowTitleMatching`, the method-local `from mcp_coder.workflows.vscodeclaude.sessions import (_get_vscode_window_titles, clear_vscode_window_cache)` is still inside its method
   - in `TestCreateTimeIdentityVerification`, the method-local `import psutil` and `from ...helpers import build_session` are still inside their methods
   - `_started_at` is still a `@staticmethod` of `TestLaunchGrace`

   If any of these was hoisted, dropped or changed: write one line to `pr_info/.blocked.txt` and stop. Don't reorder classes by hand.
4. **Imports.** Run `mcp__mcp-tools-py__run_ruff_fix(select=["F401"], target_directories=["tests/workflows/vscodeclaude"])`, then merge any duplicate import lines by hand. Expected module-level imports at the end of this step:
   - `test_sessions.py`: `json`, `Path`, `pytest`, `build_active_session_set`; from `sessions`: `add_session, check_vscode_running, get_session_for_issue, get_sessions_file_path, load_sessions, remove_session, save_sessions, session_has_artifacts, update_session_pid, update_session_status`; the 10 `types` names
   - `test_sessions_lookup.py`: `json`, `logging`, `Path`, `pytest`, `get_session_for_issue, warn_orphan_folders` from `sessions`
   - `test_sessions_active_fallback.py`: `logging`, `UTC, datetime, timedelta`, `Path`, `MagicMock`, `pytest`, `is_session_active, is_vscode_window_open_for_folder` from `sessions`, `VSCodeClaudeSession` from `types`
   - `test_sessions_active_grace.py`: `UTC, datetime, timedelta`, `Path`, `pytest`, `is_session_active` from `sessions`, `VSCodeClaudeSession` from `types`
   - `test_sessions_pid_identity.py`: `json`, `Path`, `MagicMock`, `pytest`, `check_vscode_running, load_sessions, update_session_pid` from `sessions`
   - `test_detection_probes.py`: `MagicMock, patch`, `pytest`, `VSCODE_PROCESS_NAMES, _get_vscode_processes, check_vscode_running, clear_vscode_process_cache, is_vscode_window_open_for_folder` from `sessions`

   ruff's F401 result is authoritative for what's unused; the lists above are a cross-check. Add nothing beyond imports.
5. **Allowlist.** Delete the line `tests/workflows/vscodeclaude/test_sessions.py` from `.large-files-allowlist`, matching by path. Leave every other line, including `test_session_restart.py`.

## DATA
Expected `--collect-only -q` counts after the step:

| File | Tests |
|---|---:|
| `test_sessions.py` | 23 |
| `test_sessions_lookup.py` | 7 |
| `test_sessions_active_fallback.py` | 10 |
| `test_sessions_active_grace.py` | 5 |
| `test_sessions_pid_identity.py` | 7 |
| `test_detection_probes.py` | 16 |
| `test_detection.py` | 13 |
| `tests/workflows/vscodeclaude/` | N (unchanged from baseline) |

If any count differs: write one line to `pr_info/.blocked.txt` and stop.

## Checks (all must pass before committing)
- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_ruff_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-q", <the 7 files from the DATA table>]` → 81 passed. If a test that passed at baseline now fails: write one line to `pr_info/.blocked.txt` and stop. Don't add patches, fixtures or conftest entries.
- `mcp__mcp-workspace__check_file_size`: passes, with no stale allowlist entries
- Compact diff (`mcp__mcp-workspace__git` `diff`, `compact=true`): only moved blocks, import lines, new-file headers and the allowlist line

## Commit
`test(vscodeclaude): split test_sessions.py by concern (#1319)`
