# Implementation Review Log — Run 1 (#926)

Issue: feat(icoder): show mcp-coder-utils version on startup
Branch: 926-feat-icoder-show-mcp-coder-utils-version-on-startup
Date: 2026-04-29

## Round 1 — 2026-04-29

**Findings:**
- [Skip] `app.py` `_get_version()` still uses `importlib.metadata.version("mcp-coder")` directly without `_get_package_version`. Pre-existing fallback path (only hit when `runtime_info is None`); plan did not require touching it.
- [Accept] `info.py:46` — docstring `"All values re-read live."` is now stale: `mcp-coder` and `mcp-coder-utils` versions come from `runtime_info`. The PR migrated to runtime_info but left the docstring claiming live re-read.
- [Skip] `test_env_setup.py:78-81` — module-level mock of `importlib.metadata.version` returns `"0.42.0"` for any package, so both fields assert the same value. Issue explicitly accepted this pattern; strengthening would be YAGNI.
- [Skip] Mojibake in `pr_info/TASK_TRACKER.md` and `plan_review_log_1.md`. `pr_info/` is deleted later in the process.

**Decisions:**
- Fix the stale docstring in `info.py:46` (Boy Scout, file already touched by PR).
- Skip everything else (pre-existing, YAGNI, or out-of-scope).

**Quality checks (engineer's run):** pylint PASS, mypy PASS, pytest 259/259 PASS.

**Changes:** Updated `_format_info` docstring in `src/mcp_coder/icoder/core/commands/info.py` to clarify that versions come from `runtime_info` while other values are re-read live. Quality checks PASS for the change (pre-existing unrelated failures in `tests/cli/commands/test_prompt.py::test_continue_from_*` and an unreachable warning in `utils/tui_preparation.py:121` noted but out of scope).

**Status:** Committed as 83084a3. Branch ahead of origin by 1 commit (not pushed).

## Round 2 — 2026-04-29

**Findings:** None. Re-check after the Round 1 docstring fix.

**Decisions:** No changes needed.

**Quality checks:** pylint PASS, mypy PASS (only a pre-existing unreachable warning in `utils/tui_preparation.py:121`), pytest 375/375 PASS in `tests/icoder/`. One pre-existing flaky timing test (`test_show_busy_preserves_start_time`) — passed on rerun, unrelated to this PR.

**Status:** No code changes — exit loop, proceed to vulture + lint-imports.

## Final Status

- **Rounds:** 2 (Round 1 produced one commit; Round 2 clean).
- **Commits added by review:** 1 (`83084a3` — `docs(icoder): clarify /info docstring after runtime_info migration`).
- **Vulture:** Clean.
- **Lint-imports:** 22 contracts kept, 0 broken (including `MCP Coder Utils Isolation`, which is the relevant one for this issue).
- **Implementation matches plan:** Yes — `_get_package_version` helper present, `RuntimeInfo.mcp_coder_utils_version` field added, banner placement correct, `/info` reads both versions from `runtime_info`, unused `importlib.metadata` import dropped.
- **Outcome:** Ready to ship.

