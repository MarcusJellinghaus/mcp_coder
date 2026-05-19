# Issue #979 Implementation Review Log — Run 1

**Issue**: Add --settings flag to specify .claude/settings.local.json (mirror --mcp-config)
**Branch**: 979-add-settings-flag-to-specify-claude-settings-local-json-mirror-mcp-config
**Commit under review**: ab6ddb3f
**Started**: 2026-05-20
**Supervisor**: Claude Code

---

## Round 1 — 2026-05-20

**Findings:**
- Critical: none.
- Accept (worth fixing now): none from the engineer's verdict.
- Skip: `--settings ""` edge case (pre-existing in `resolve_mcp_config_path`); `settings_file` pointing at a directory (same pre-existing pattern); pre-existing `claude_cli_integration` test breakage in `test_implement_workflow_passes_execution_dir_to_task_processing` (unrelated to #979).
- Boy Scout opportunities: resolver DRY refactor (skip — premature for 2 callers; YAGNI), schema placement (already fine).
- Coverage gaps:
  1. `TestResolveClaudeSettingsPath` missing `test_relative_env_falls_back_to_cwd_when_no_project_dir` (mcp variant has it).
  2. Missing `test_relative_config_falls_back_to_cwd_when_no_project_dir`.
  3. No direct autodetect assertion with `project_dir=None`.

**Decisions:**
- Skip resolver DRY refactor (engineer agreed; YAGNI/KISS; two callers).
- Skip end-to-end CLI smoke test (each link tested; `claude_cli_integration` markers cover full chain).
- Skip pre-existing test breakage (out of scope per software_engineering_principles.md).
- **Accept the three coverage gaps** — parity with `TestResolveMcpConfigPath` is the stated goal of #979's AC: "Unit-test parity with `TestResolveMcpConfigPath` (~14 scenarios)."

**Changes:**
- Added 3 tests to `TestResolveClaudeSettingsPath` in `tests/cli/test_utils.py`:
  1. `test_relative_env_falls_back_to_cwd_when_no_project_dir`
  2. `test_relative_config_falls_back_to_cwd_when_no_project_dir`
  3. `test_resolve_claude_settings_autodetect_no_project_dir`
- Class went from 17 → 20 tests.
- No production code changed.
- Pytest: 20 passed (class); mypy clean.

**Status**: committed.

## Round 2 — 2026-05-20

**Findings:**
- Round-1 fix verdict: 3 new tests are well-formed, exercise the intended code paths, use deterministic `tmp_path` + `monkeypatch.chdir`/`monkeypatch.setenv` patterns. The autodetect test even goes one better than the mcp variant by covering both `.local.json` and `.json` in a single test.
- Static checks: pylint / mypy / ruff all PASS.
- Anything missed: none.

**Decisions:** none — verdict is LGTM.

**Changes:** none.

**Status**: no code changes — exiting loop.

## Architectural checks (post-loop)

- `run_lint_imports_check`: **PASSED** — 23 contracts kept, 0 broken.
- `run_vulture_check`: 1 finding at 60% confidence — `_mock_resolve_claude_settings_path` in `tests/cli/commands/conftest.py:91`. Pytest autouse fixture; false positive. Whitelisted in `vulture_whitelist.py` (commit `8ca8e7c8`). Re-run: clean.

## Final Status

- **Rounds run:** 2 (round 1 = code review + 3 test additions; round 2 = verification, LGTM)
- **Code commits produced:** 2
  - `85571704` — `test(cli): add CWD-fallback parity tests for resolve_claude_settings_path`
  - `8ca8e7c8` — `chore: whitelist _mock_resolve_claude_settings_path in vulture`
- **Static checks (final):** pylint, mypy, ruff, vulture, lint-imports — all clean.
- **Critical findings:** 0
- **Accept findings carried forward:** 0
- **Skipped findings:** documented in round 1 (pre-existing edge cases; resolver DRY refactor deferred; end-to-end CLI smoke test out of scope).
- **Issue:** #979 — ready for branch-status check + PR.
