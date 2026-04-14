# Plan Review Log — Issue #648

Review of plan for "Support standard prompts (system prompt + project prompt)".

## Round 1 — 2026-04-14
**Findings**:
- Missing `src/mcp_coder/prompts/__init__.py` in Step 1 new files list
- Step 1 should reuse `find_data_file()` from `data_files.py` instead of direct importlib.resources
- Step 4: ValueError for mutually exclusive `append_system_prompt`/`system_prompt_replace` marked optional — should be required
- Step 4: `_is_claude_md()` only checks `.claude/CLAUDE.md` — should check all known Claude Code CLAUDE.md locations
- Step 7: `_is_claude_md` is private but imported cross-module — should be public in `prompt_loader.py`
- Step 7: verify.py re-derives `project_dir` instead of reusing existing variable

**Decisions**:
- All findings accepted as straightforward improvements
- User chose option D for CLAUDE.md detection: check all known locations (root, .claude/, parent directories)

**User decisions**:
- CLAUDE.md redundancy detection scope → option D (all known locations)

**Changes**: Steps 1, 4, 7, and summary.md updated
**Status**: Committed (5c581dd)

## Round 2 — 2026-04-14
**Findings**:
- Missing `mcp_coder.prompts` in `.importlinter` layered architecture contract — lint-imports would fail
- Missing `tests.prompts` in test module independence contract
- Summary.md described Claude provider params as `system_prompt: str | None + system_prompt_replace: bool` — should be two string params
- Step 2 uses `_build_claude_prompt` but Step 4 defines `_build_claude_system_prompts` — naming inconsistency

**Decisions**: All accepted as straightforward fixes
**User decisions**: None needed
**Changes**: Steps 1, 2, and summary.md updated
**Status**: Committed (dfaae9c)

## Round 3 — 2026-04-14
**Findings**:
- Step 2 algorithm assigns `_build_claude_system_prompts()` return to single variable instead of destructuring tuple — replace mode would silently break

**Decisions**: Accepted
**User decisions**: None needed
**Changes**: Step 2 updated
**Status**: Committed (2588582)

## Round 4 — 2026-04-14
**Findings**: None — plan is clean
**Status**: No changes needed

## Final Status

Plan review complete. 4 rounds run, 3 commits produced. All steps are internally consistent, cross-referenced correctly, and aligned with the issue requirements and codebase structure. Plan is ready for approval.
