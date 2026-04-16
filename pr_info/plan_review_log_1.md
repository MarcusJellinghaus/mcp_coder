# Plan Review Log — Issue #830

Branch: 830-cli-verify-prompt-misleading-winerror-2-diagnostics-on-windows
Plan files reviewed: summary.md, step_1.md, step_2.md, step_3.md

## Round 1 — 2026-04-16

**Findings**
- Step 2 wrap scope is ambiguous at both sites — "the body" wording could lead implementer to miss `__aenter__` failures.
- Step 2 — existing test `test_hard_fails_on_mcp_server_error` uses `ConnectionError`, should be explicitly noted as unchanged.
- Step 3 — `Path.exists()` gives false-positive "binary not found" for PATH-resolved bare executables (`python`, `npx`).
- Step 3 — `_preflight_mcp_server(name, cfg)` receives `name` but doesn't use it.
- Step 3 — pseudocode for `${VAR}` scan referenced `match.group(0)` without naming the Match variable.
- Step 3 — missing imports `import re` and (if needed) `from pathlib import Path` not explicitly listed.
- Step 3 — missing test for the case "pre-flight passes, launch still fails" (FileNotFoundError at `__aenter__` with a valid resolved path).
- Step 1 — `_models.py` has 3 pre-existing single-quoted `pip install 'mcp-coder[langchain]'` ImportError hints, out of scope but worth flagging.
- Minor formatting — approximate line-number annotations (`~line 233`, `~line 383`) in step_2.md.
- TimeoutError exclusion from narrowed `CONNECTION_ERRORS` — confirm no existing test relies on this classification.

**Decisions**
- Accept (autonomous): Step 2 wrap-scope wording clarification — important for correctness.
- Accept (autonomous): Step 2 note about `test_hard_fails_on_mcp_server_error` remaining green.
- Ask user: pre-flight check — `Path.exists()` vs `shutil.which()` — reverses an explicit decision in summary.md.
- Accept (autonomous): use `name` in pre-flight messages (repurpose, not drop).
- Accept (autonomous): tighten pseudocode with named `m = pattern.search(...)`.
- Accept (autonomous): explicit new-imports section in step_3.md.
- Accept (autonomous): add new TDD test `test_launch_error_filenotfound_after_preflight_passes`.
- Accept (autonomous): flag `_models.py` quote sites as out-of-scope in step_1.md.
- Accept (autonomous): remove approximate line-number annotations.
- Verify (engineer): grep tests for `TimeoutError` — no action needed if clean.
- Skip: Step 1 test rename already correct; Step 2 "no existing test changes" confirmed; Step 3 `_mcp_client_cache` note — no change needed.

**User decisions**
- Q: Pre-flight check — `Path.exists()` vs `shutil.which()` vs hybrid?
- A: Switch to `shutil.which()`. Update summary.md decisions table and step_3.md accordingly.

**Changes**
- `summary.md`: pre-flight switched to `shutil.which`; TimeoutError note — grep confirmed 0 test matches.
- `step_1.md`: Boy Scout / out-of-scope callout for `_models.py` single-quoted pip hints.
- `step_2.md`: removed line-number annotations; rewrote both wrap-site descriptions to explicitly cover `async with client.session(...) as session:` line (for `__aenter__` exceptions); added TDD bullet noting `test_hard_fails_on_mcp_server_error` remains green.
- `step_3.md`: pre-flight uses `shutil.which`; helper `name` parameter now used in messages (`unresolved placeholder ... in {name}.{field}`, `binary not found at ... (server {name})`); new imports listed explicitly; tightened `${VAR}` pseudocode; updated `test_server_failure` bullet for `shutil.which` return shape; added new TDD bullet `test_launch_error_filenotfound_after_preflight_passes`.

**Status**: Changes applied. Ready to commit.


## Round 2 — 2026-04-16

**Findings**
- `test_mixed_servers` — after switching to `shutil.which`, `bad.command="nonexistent"` short-circuits in pre-flight and the mocked `ConnectionError` at `__aenter__` is never reached.
- Missing "remains green" note for existing `test_server_failure_has_no_tool_names` (mirrors round 1 pattern for `test_hard_fails_on_mcp_server_error`).
- Brittle coupling: `_check_servers` derives `error` category via `msg.startswith("unresolved placeholder")`. Implicit string-prefix contract between helper and caller.
- Test name `test_connection_errors_contains_oserror` stays stale after Step 1 semantics flip (assertion now says `OSError not in ...`).

**Decisions**
- Accept (autonomous): rewrite `test_mixed_servers` — drop `ConnectionError` mock, assert `error == "FileNotFoundError"` from pre-flight. Launch-error path already covered by `test_hard_fails_on_mcp_server_error` and the new `test_launch_error_filenotfound_after_preflight_passes`.
- Accept (autonomous): add "remains green" note for `test_server_failure_has_no_tool_names`.
- Skip (YAGNI): keep the 2-tuple `(ok, msg)` helper signature. Helper and caller share the same short span in the same file; rewording can be updated together. A 3-tuple or enum adds complexity without meaningful robustness gain.
- Accept (autonomous): rename `test_connection_errors_contains_oserror` → `test_connection_errors_excludes_oserror`.

**User decisions**
- None — no design questions escalated this round.

**Changes**
- `step_1.md`: renamed `test_connection_errors_contains_oserror` → `test_connection_errors_excludes_oserror`.
- `step_3.md`: rewrote `test_mixed_servers` TDD bullet — bad server fails in pre-flight (`shutil.which` returns None), asserts `error == "FileNotFoundError"`, dropped launch-mock side_effect; added "remains green" bullet for `test_server_failure_has_no_tool_names`.

**Status**: Changes applied. Ready to commit.
