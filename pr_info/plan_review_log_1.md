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
