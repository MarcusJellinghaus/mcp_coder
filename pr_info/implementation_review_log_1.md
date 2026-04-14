# Implementation Review Log — Run 1
## Round 1 — 2026-04-14

**Findings:**
1. No validation of `claude_system_prompt_mode` value — typos silently fall through to append
2. `is_claude_md` calls `.resolve()` without OSError handling — broken symlinks could raise
3. Decision #6 langchain concatenation fallback not implemented
4. No path traversal protection in `_resolve_and_read`
5. `is_claude_md` performance: resolves every candidate in loop
6. `load_system_prompt()`/`load_project_prompt()` independently call `get_prompts_config()`
7-16. Verified correct: section headers, project_dir usage, CLAUDE.md detection, importlinter, CLI flags, test coverage
17. Package-relative path resolution omitted (intentional)

**Decisions:**
- Accept #1: Add warning log for invalid `claude-system-prompt-mode` values
- Accept #2: Wrap `is_claude_md` body in try/except OSError returning False
- Skip #3: YAGNI — no known backend needs concatenation fallback
- Skip #4: Trust boundary correct — project owners control pyproject.toml
- Skip #5-6: Negligible / not a real issue
- Skip #7-16: Confirmed correct, no action needed
- Skip #17: Intentional simplification

**Changes:**
- `src/mcp_coder/utils/pyproject_config.py`: Added validation warning for invalid `claude-system-prompt-mode`
- `src/mcp_coder/prompts/prompt_loader.py`: Wrapped `is_claude_md` in try/except OSError
- `tests/prompts/test_prompt_loader.py`: Added tests for both fixes

**Status:** Committed

## Round 2 — 2026-04-14

**Findings:** None — round 2 clean.
**Decisions:** N/A
**Changes:** None
**Status:** No changes needed

## Final Status

- **Rounds:** 2 (1 with fixes, 1 clean)
- **Commits:** 1 (`cbec8fa` — validate claude_system_prompt_mode + OSError handling)
- **Quality checks:** All pass (pylint clean, 3604 tests pass, mypy clean except pre-existing)
- **Open issues:** None

---

**Issue:** #648 — Support standard prompts (system prompt + project prompt)
**Date:** 2026-04-14
**Branch:** 648-support-standard-prompts-system-prompt-project-prompt

