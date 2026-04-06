# Plan Review Log — Run 1

Issue: #463 — Split up test files for vscodeclaude orchestrator after source split (#458)
Date: 2026-04-06

## Round 1 — 2026-04-06
**Findings**:
- `test_session_restart.py` will exceed 750 lines (~980 with imports) — plan claimed all files under 750
- Missing vulture & lint_imports checks in LLM prompts (only mentioned pytest, pylint, mypy)
- Step 1 LLM prompt referenced `move_file` instead of being tool-agnostic
- Step 2 missing ruff_check.sh in verification
- Missing format_code step before commit in both steps
- Step sizing is appropriate (positive)
- Summary/issue alignment is good (positive)

**Decisions**:
- `test_session_restart.py` over 750 lines: **ask user** → user chose option A (add to allowlist, further splitting is separate issue)
- Missing checks in prompts: **accept** — updated to reference all CLAUDE.md checks
- Tool name in step 1: **accept** — simplified to "Rename these files"
- Missing ruff: **accept** — folded into full check list
- Missing format_code: **accept** — added to both prompts

**User decisions**:
- Q: `test_session_restart.py` exceeds 750 lines. Options: (A) add to allowlist, (B) split class further, (C) other?
- A: Option A — add to allowlist, further splitting is a separate issue.

**Changes**:
- `pr_info/steps/summary.md`: updated constraints to note allowlist exception for `test_session_restart.py`
- `pr_info/steps/step_1.md`: updated HOW section, ALGORITHM comment, and LLM prompt with full check list and format_code
- `pr_info/steps/step_2.md`: updated WHERE (allowlist add), ALGORITHM, DATA section, and LLM prompt with allowlist, full checks, format_code

**Status**: ready to commit
