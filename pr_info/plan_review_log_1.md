# Plan Review Log — Run 1

**Issue:** [#937](https://github.com/MarcusJellinghaus/mcp_coder/issues/937) — Wire `verify_git` into `mcp-coder verify`
**Branch:** `937-mcp-coder-wire-verify-git-into-mcp-coder-verify` (base: `main`, up-to-date)
**Plan files reviewed:** `pr_info/steps/summary.md`, `pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`
**Started:** 2026-05-04

## Round 1 — 2026-05-05

**Findings (from `/plan_review` engineer subagent):**
- Critical 1: `_mock_git` fixture placement too narrow — would cause ~6 other test files to hit real `verify_git` in CI. Existing `_mock_verify_github` pattern is an autouse fixture in `conftest.py`.
- Critical 2: Integration test snippet references helpers (`_claude_ok`, `_mlflow_not_installed`, `_minimal_llm_response`) that don't exist in `test_verify_integration.py`; actual helpers are `_make_claude_result`, `_make_mlflow_result`, `_MOCK_LLM_RESPONSE`.
- Critical 3: Integration assertion `"Signing key" in output or "signing_key" in output` is brittle when gpg isn't installed (Windows CI).
- Improvement: Step 1 should mirror `mcp_workspace_github.py` `# Verification` group placement at end of `__all__`, not append-after-`detect_parent_branch_via_merge_base`.
- Improvement: Add unit tests for `_compute_exit_code(git_result=…)` parity with existing GitHub-branch tests.
- Improvement: Add ordering assertion `PROJECT < GIT < GITHUB` to pin Decision #2.
- Improvement: Assert `verify_git` is called with `actually_sign=True` to pin Decision #3.
- Improvement: Rename fixture `_mock_git` → `_mock_verify_git`; update `_compute_exit_code` docstring summary line.
- Improvement: Make `# Git failure …` comment style match the existing `# GitHub failure …` style exactly.

**Decisions:**
- Critical 1, 2, 3 → accept (correctness fixes).
- All improvements → accept (parity with existing patterns; small, bounded).
- Engineer's Q1 (test placement) → autonomously pinned to `test_verify_integration.py` with the actual local helper names (smaller diff, respects file purpose).
- Engineer's Q3 (test platform) → escalated to user.
- Engineer's Q4 (`actually_sign=True` assertion) → autonomously accepted as a one-line defensive test.

**User decisions:**
- Q: Integration test platform/gpg handling? A/B/C → User chose **A. Run on all platforms** with relaxed assertions (`=== GIT` rendered + `exit_code != 0`).

**Changes (via `/plan_update`):**
- `pr_info/steps/summary.md` — file list updated: `conftest.py — _mock_verify_git autouse fixture` replaces the per-class fixture line.
- `pr_info/steps/step_1.md` — `__all__` placement guidance updated to "end under `# Verification` group" mirroring `mcp_workspace_github.py`.
- `pr_info/steps/step_2.md` — §5 fixture moved to `conftest.py`; §6 gains `test_git_section_appears_between_project_and_github` and `test_verify_git_called_with_actually_sign_true`; TDD order gains exit-code unit tests as step 1.5; §7 pinned to `test_verify_integration.py` with correct helper names and relaxed assertions; §3 docstring guidance expanded; comment-style note added.

**Status:** Plan files changed; suggested commit `Refine verify_git wiring plan after review (#937)` — commit agent invoked next.

## Round 2 — 2026-05-05

**Findings (from `/plan_review` round 2):**
- Critical: TDD §1.5 referenced `test_github_failure_causes_exit_1` in `test_verify_orchestration.py` (orchestration-style test) instead of the actual unit-test file `tests/cli/commands/test_verify_exit_codes_github.py`. The new git tests must mirror the unit tests there, not the orchestration ones.
- Critical: §6 `TestGitLabelMappings` placed two new tests (`test_git_section_appears_between_project_and_github`, `test_verify_git_called_with_actually_sign_true`) in `test_verify_format_section_basic.py`, but those tests reference `execute_verify`/`_make_args`/`_VERIFY` which don't exist in that file.
- Critical: `mock.assert_called_once_with(project_dir, actually_sign=True)` referenced an undefined `project_dir` variable.
- Improvement: Step 1 `__all__` placement guidance was self-contradictory — the github shim has its `# Verification` group near the top, not the end, and `mcp_workspace_git.py` has no `__all__` category comments at all.
- Improvement: summary.md conftest line wording could be tighter ("auto-mocks verify_git" vs "don't hit real git").
- Improvement: §3 docstring summary update lacked a concrete before/after snippet.

**Decisions:** all findings → accept (correctness fixes for round-1-introduced inconsistencies; no design questions).

**User decisions:** none required.

**Changes (via `/plan_update`):**
- `pr_info/steps/step_2.md` — TDD §1.5 now points to a new file `tests/cli/commands/test_verify_exit_codes_git.py` with `TestGitExitCode` mirroring `TestGitHubExitCode`'s three direct-call unit tests; §6 split into 6a (format-section file: rendering tests only) and 6b (orchestration file: new `TestGitWiring` class for ordering + `actually_sign=True`); §3 gains concrete before/after docstring text.
- `pr_info/steps/step_1.md` — `__all__` instruction simplified: append `"verify_git"` at the end of the existing flat `__all__` with no category comment; the `# Verification` comment block applies only to the imports area (matching the file's existing per-group import style).
- `pr_info/steps/summary.md` — file list updated to add `tests/cli/commands/test_verify_exit_codes_git.py` (Created) and split the `test_verify_orchestration.py` entry to mention the new `TestGitWiring` class; conftest fixture wording tightened.
- `actually_sign=True` assertion pinned to `mock.call_args.kwargs["actually_sign"] is True` (kwargs-only check).

**Status:** Plan files changed; suggested commit `Plan round 2: pin exit-code unit tests, split format vs orchestration tests` — commit agent invoked next.

## Round 3 — 2026-05-05

**Findings (from `/plan_review` round 3):**
- None — plan is ready for approval.
- Two borderline cosmetic polish items flagged (TDD-Order ↔ LLM-Prompt step-numbering parity for the new orchestration tests; one stitch-sentence in step_1.md). Engineer marked both "not blocking".

**Decisions:** skip both polish items per "default to simpler plans" guidance. Loop exit condition met (zero plan changes this round).

**User decisions:** none.

**Changes:** none.

**Status:** no plan changes — loop terminates.

## Final Status

**Outcome:** Plan is ready for approval after 2 rounds of review.

**Rounds run:** 3 review passes (2 produced changes, 1 confirmed clean).

**Plan-refinement commits:**
- `04e99bb` — Refine verify_git wiring plan after review (#937)
- `d87bc41` — Plan round 2: pin exit-code unit tests, split format vs orchestration tests

**Net plan changes:**
- New unit-test file `tests/cli/commands/test_verify_exit_codes_git.py` added to scope (mirrors `test_verify_exit_codes_github.py`).
- New `TestGitWiring` class in `test_verify_orchestration.py` added to scope (ordering test + `actually_sign=True` test).
- Autouse `_mock_verify_git` moved from per-class to `tests/cli/commands/conftest.py` (mirrors `_mock_verify_github`).
- Integration test pinned to `tests/cli/commands/test_verify_integration.py` with correct local helper names (`_make_claude_result`, `_make_mlflow_result`, `_MOCK_LLM_RESPONSE`); assertions relaxed to `=== GIT` + `exit_code != 0` (env-resilient).
- Step 1 simplified: append `"verify_git"` at the end of the flat `__all__`; `# Verification` comment lives in imports area only.
- `_compute_exit_code` docstring summary line gains concrete before/after text and "when git verification failed" insertion.
- `actually_sign=True` assertion pinned to `mock.call_args.kwargs["actually_sign"] is True` (avoids brittle `project_dir` reference).
- Comment style for new exit-code block matches existing `# GitHub failure …` phrasing exactly.

**Acceptance criteria coverage:** the four issue-level acceptance criteria (GIT section between PROJECT and GITHUB; "not configured" rendering; broken-signing exit non-zero; Tier 3 sign test row when intent detected) are all covered by the tests now described in the plan.

**No outstanding user questions.** Plan is ready for the next status transition.
