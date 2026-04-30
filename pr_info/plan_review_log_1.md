# Plan Review Log — Issue #933

**Issue**: verify: render API base URL and token fingerprint in GITHUB section (consumes mcp-workspace#176)
**Branch**: 933-verify-render-api-base-url-and-token-fingerprint-in-github-section-consumes-mcp-workspace-176
**Started**: 2026-04-30

---

## Round 1 — 2026-04-30

### Findings

- F1 (no-op): Step granularity correct — one step / one commit aligns with KISS. The plan groups two trivial additive changes (`_LABEL_MAP` entry + 3-line suffix extension) into a single TDD step.
- F2 (no-op): TDD ordering explicit — red → green → checks → format → commit. DoD lists pylint/pytest/mypy as exit criteria.
- F3 (accept): Brittle "absent fingerprint" assertion in Test 3 — the nested `split`/list-comp is harder to read than the property it expresses. Replace with an anchored one-liner asserting the literal expected suffix line is present and `"config.toml ("` is not in `output`.
- F4 (accept): `expected_in_suffix` for `"****"` and `"ghp_...a3f9"` cases is not anchored to the suffix line. Tighten to full-line anchored form: `assert "from ~/.mcp_coder/config.toml (****)" in output` (and similarly for the fingerprint case).
- F5 (accept): The fallback severity case in `test_api_base_url_value_cases` carries an inline tuple comment that formatters may strip. Promote to an explicit `pytest.param(..., id="fallback-severity-warning-renders-err")` so failure output makes the intent obvious.
- F6 (accept): DoD item 6 and the LLM Prompt section reference `./tools/format_all.sh`. Per CLAUDE.md, the formatter must be invoked via `mcp__tools-py__run_format_code`. Replace both occurrences.
- F7 (accept): DoD item 4 pytest exclusion list is missing `copilot_cli_integration`, `jenkins_integration`, `llm_integration`, `textual_integration` versus the canonical CLAUDE.md fast-mode invocation. Align verbatim.
- F8 (no-op): Orchestration test correctly uses `with patch(f"{_VERIFY}.verify_github", return_value=...)` to override the autouse `_mock_github` fixture for that test body.
- F9 (accept): No test asserts `api_base_url` renders before `Authenticated user` / `Token configured`, despite dict insertion order being load-bearing per the issue body and `_format_section`. Add one cheap position assertion (e.g. `api_idx < token_idx`) in Test 2 or Test 4.
- F10 (skip): No dedicated backward-compat test for "older mcp-workspace, no `api_base_url`, no `token_fingerprint`" — already decided in the issue Decisions table; existing fixtures cover it implicitly.
- F11 (accept): `_LABEL_MAP` placement guidance ("no specific position required") is too permissive — the existing dict groups by section with a `# GitHub section` comment. Tighten the plan to "place at the top of the `# GitHub section` block, before `token_configured`" to mirror data-shape ordering and keep the diff readable.
- F12 (skip): Ruff is not listed in DoD. Low impact for a 4-line patch; pylint catches most issues.
- F13 (skip): `token_fingerprint` set without `token_source` is impossible-by-construction — the outer `if entry.get("token_source")` gate means a stray fingerprint without a source produces no output. Testing it would test the producer, not the consumer.
- F14 (no-op): Format-string ownership boundary correctly drawn — tests assert substring presence rather than literal format-shape contracts, matching the issue's "No format string drift" constraint.
- F15 (skip): LLM Prompt section duplicates earlier WHAT/HOW content — intentional repo pattern (the prompt is meant to be self-contained for a sub-agent).

### Decisions

Auto-accept F3, F4, F5, F6, F7, F9, F11 — all mechanical edits to `pr_info/steps/step_1.md`. Skip F10, F12, F13, F15 per the issue Decisions table or low-impact rationale above. F1, F2, F8, F14 are positive observations with no action.

### User decisions

None — no design or requirements questions raised.

### Changes

Updated `pr_info/steps/step_1.md` only: tightened the Test 3 "absent fingerprint" assertion and the Test 3 success-case suffix assertion to anchor on the full `from ~/.mcp_coder/config.toml (...)` line (F3, F4); promoted the severity-ignored parametrize case to a `pytest.param(..., id=...)` (F5); replaced `./tools/format_all.sh` with `mcp__tools-py__run_format_code` in DoD item 6 and in the LLM Prompt (F6); aligned the DoD pytest marker exclusions verbatim with the CLAUDE.md fast-mode block (F7); added a position assertion that `api_base_url` precedes `token_configured` (F9); and tightened `_LABEL_MAP` placement guidance to "top of the `# GitHub section` block, before `token_configured`" (F11). `summary.md` unchanged.

### Status

Pending commit.

---

## Round 2 — 2026-04-30

### Findings

- F16 (no-op): Round 1 fix F3 applied correctly. `step_1.md` lines 187-194 now use the anchored negative assertion `assert "from ~/.mcp_coder/config.toml (" not in output` for the `fingerprint-absent` case — clean and intent-revealing.
- F17 (no-op): Round 1 fix F4 applied correctly. `step_1.md` lines 156-159 and 161-164 anchor `expected_in_suffix` on the full suffix line: `"from ~/.mcp_coder/config.toml (ghp_...a3f9)"` and `"from ~/.mcp_coder/config.toml (****)"`. No accidental substring leakage possible.
- F18 (no-op): Round 1 fix F5 applied correctly. Test 2 has `id="success-renders-ok"` and `id="fallback-severity-warning-renders-err"`; Test 3 has `id="normal-token"`, `id="short-token-sentinel"`, `id="fingerprint-absent"`. All five pytest.param ids are descriptive and align with the test cases.
- F19 (no-op): Round 1 fix F6 applied correctly. DoD item 6 (line 316) and LLM Prompt step 7 (line 356) both reference `mcp__tools-py__run_format_code`. No `format_all.sh` references remain.
- F20 (no-op): Round 1 fix F7 applied correctly. DoD item 4 (line 314) marker exclusion list matches the CLAUDE.md fast-mode invocation verbatim, including `copilot_cli_integration`, `jenkins_integration`, `llm_integration`, `textual_integration`.
- F21 (no-op): Round 1 fix F9 applied correctly. Test 2 lines 130-135 add `api_idx = output.find("API base URL")` / `token_idx = output.find("Token configured")` / `assert 0 <= api_idx < token_idx` — guards both presence and ordering with one cheap check.
- F22 (no-op): Round 1 fix F11 applied correctly. Line 31 prescribes "top of the `# GitHub section` block ... before `token_configured`" with rationale (mirror data-shape ordering, keep diff readable).
- F23 (no-op): The Test 2 fallback case expected value `"https://api.github.com (fallback - identifier unresolved) (Could not determine repository URL from git remote)"` assumes `_format_section`'s existing value+error concatenation pattern. Consistent with how other rows render today; not a plan defect.
- F24 (no-op): Test 2's position assertion fixture (`{"token_configured": {"ok": True, "value": "configured"}}`, no `token_source`) is a minimal but valid configuration — the row label `"Token configured"` will still render via `_LABEL_MAP`, satisfying the position check.
- F25 (no-op): No new gap surfaced by the position assertion — the dict in Test 2 only contains `api_base_url` + `token_configured` + `overall_ok`, so the assertion targets exactly the two relative positions that matter.

### Decisions

All round 2 findings are no-op observations. No plan changes warranted. Round 1's seven mechanical fixes (F3, F4, F5, F6, F7, F9, F11) are all applied correctly and produce the intended tightening.

### User decisions

None — no design or requirements questions surfaced this round.

### Changes

No plan changes — round 1 fixes verified clean. Plan is ready for user approval.

### Status

Ready for approval. No further plan-update rounds needed.


## Final Status

**Rounds run**: 2
**Plan changes**: Round 1 — 6 mechanical fixes applied to `step_1.md` (F3, F4, F5, F6, F7, F9, F11). Round 2 — zero changes (round 1 fixes verified clean).
**Commits produced**: 1 (round 1 plan fixes — `ebc29bb`). The Final Status / round 2 log update is a separate trailing commit on top of this.
**Approval status**: Ready for user approval.
**Open questions**: None — all design and requirements decisions remain consistent with the issue's Decisions table; no questions were raised in either round.
