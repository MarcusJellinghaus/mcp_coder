# Plan Review Log — Run 1

**Issue:** #597 — Fix session log files stored in target project instead of mcp-coder directory
**Date:** 2026-03-26
**Branch:** 597-fix-session-log-files-stored-in-target-project-instead-of-mcp-coder-directory

## Round 1 — 2026-03-26
**Findings**:
- [CRITICAL] `generate_pr_summary()` in `create_pr/core.py` calls `prompt_llm()` without `env_vars` — won't benefit from fix
- [IMPROVEMENT] Path construction uses string concatenation instead of `pathlib`
- [IMPROVEMENT] Test assertion guidance should explicitly cover `env_vars` dicts without `MCP_CODER_PROJECT_DIR`
- [OK] `MCP_CODER_PROJECT_DIR` reliably present in `env_vars` for most callers
- [OK] `ask_claude_code_cli()` already accepts `logs_dir` parameter
- [OK] Step scoping is appropriate (one step, one commit)
- [QUESTION] Langchain provider doesn't get `logs_dir` — skipped (YAGNI, no NDJSON logging)

**Decisions**:
- `generate_pr_summary()` gap: **ask user** → user chose option B (fix in this step)
- Path concatenation: **accept** — use `Path(...) / "logs"` instead
- Test assertion clarity: **accept** — add explicit note
- Langchain question: **skip** — YAGNI

**User decisions**:
- Q: `generate_pr_summary()` doesn't pass `env_vars`. (A) Document as gap, (B) Fix in this step, (C) Investigate first? → **User chose B**: fix it in this step

**Changes**:
- `summary.md`: Added `create_pr/core.py` to modified files, updated "not modified" count
- `step_1.md`: Added `create_pr/core.py` fix, changed path construction to `pathlib`, clarified test assertions, updated checklist

**Status**: Committed (97fd842)

## Round 2 — 2026-03-26
**Findings**:
- [OK] Plan accurately describes `prompt_llm()` structure
- [OK] `ask_claude_code_cli` already accepts `logs_dir`
- [OK] `create_pr/core.py` fix correctly specified
- [IMPROVEMENT] `verify.py` also calls `prompt_llm()` without `env_vars` (lines 141, 327) — diagnostic commands, fallback is acceptable
- [OK] `pathlib` import noted correctly
- [OK] Test assertions match current code
- [OK] Consistency between `summary.md` and `step_1.md`
- [OK] No other workflow callers missing `env_vars`

**Decisions**:
- `verify.py` gap: **accept** — add note to summary.md, no code change needed
- All other findings: OK, no action

**User decisions**: None needed this round

**Changes**:
- `summary.md`: Added note about `verify.py` under "Files NOT Modified"

**Status**: Changes made, pending commit

## Final Status
- **Rounds**: 2
- **Plan is ready for approval**
- Changes: fixed missing `create_pr/core.py` caller, improved path construction (pathlib), clarified test assertions, documented `verify.py` gap
- No open questions remain
