# review-plan review log 1

## Round 1 — 2026-09-06
**Findings**:
I'll gather context now.`pr_info/steps/step_4.md:84` — high — `_find_section_array` matches *any* depth-1 string equal to the section name, but `defaultMode` is a top-level key whose schema enum is exactly `"allow"|"ask"|"deny"` (`loader.py:146`); `{"defaultMode": "allow", ...}` therefore hits the match, the "expect `:` then `[`" walk fails, and the pseudo-code specifies no continue-scanning fallback — the locator returns `None` and `_insert_section` writes a duplicate top-level `"allow"` key, corrupting the file. No test in the table covers a file containing `defaultMode`.

`pr_info/steps/step_4.md:122` — high — `write_rule` does `json.loads(_strip_jsonc(text))` with no stated failure behaviour; a hand-edited/malformed `settings.local.json` raises `JSONDecodeError` (a `ValueError`) and a non-object root raises `AttributeError` on `data.get(section, [])`. `step_5.md:50` catches only `OSError`, so the exception escapes on the UI thread, `resolve_pending` is never called, and the parked interceptor wedges the turn permanently — the exact failure the step-5 degrade branch exists to prevent.

`pr_info/steps/step_3.md:154` — medium — `test_session_grant_absent_from_a_reloaded_config` is vacuous as specified: `tmp_path` has no `.icoder/`, so `load_permission_config(tmp_path)` returns an empty config and "contains no `runtime`-layer rule" holds whether or not the grant was applied. It needs an authored `.icoder/settings.json` on disk to be a real assertion.

`pr_info/steps/step_3.md:153` — medium — `test_session_grant_is_honoured_by_resolve` hand-builds `PermissionConfig` from the `Rule` captured by the `add_runtime_rule` spy, so the gateway's real runtime-layer store (`gateway.py::add_runtime_rule`, which rebinds the frozen config) is never exercised; the AC "honoured by `resolve()` on a *subsequent* turn this process" is only proved for the rule shape, not the store.

`pr_info/steps/summary.md:5` — medium — step 1 implements issue #1154 in full (its own summary, ACs, tests and commit message `fix(permissions): ... (#1154)`) inside the #1046 PR; #1154 is a separate open issue still at `status-01:created` and has not been through its own plan/review cycle.

`pr_info/steps/step_3.md:110` — low — `_persist_target` falls back to `Path.cwd()` when `runtime_info` is `None`, so a persist grant can write `.icoder/settings.local.json` into a directory unrelated to the project whose config was loaded; skipping the disk write is the safer degrade.

`pr_info/steps/step_2.md:170` — low — acceptance says "All seven tests pass" (repeated at `:187`) but the TDD table at `:159`–`:166` lists six tests.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_4.md around line 84, fix `_find_section_array` so a depth-1 string equal to the section name is only accepted when it is followed by `:` then `[`; on failure the locator must continue scanning for a later match rather than returning `None`. Add a test to the step-4 table covering a settings file containing a top-level `"defaultMode": "allow"` alongside (and without) an `allow` array, asserting no duplicate top-level key is written.', "In pr_info/steps/step_4.md around line 122, specify `write_rule` failure behaviour for malformed input: catch `json.JSONDecodeError`/`ValueError` from `json.loads(_strip_jsonc(text))` and a non-object root, and surface them as the same failure type the caller already degrades on. Update step_5.md:50 so the caller's except clause covers that type, guaranteeing `resolve_pending` is still called and the interceptor cannot wedge the turn. Add a test for a malformed `settings.local.json` and for a non-object root."], escalate_reason=None)
**Changes**:
applied
