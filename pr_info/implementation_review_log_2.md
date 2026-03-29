# Implementation Review Log — Run 2

**Branch:** 613-chore-align-launcher-and-install-scripts-with-environment-model
**Issue:** #613 — chore: align launcher and install scripts with environment model
**Date:** 2026-03-29

## Round 1 — 2026-03-29

**Findings:**
- F1 (Critical): `environments.md` entry point matrix still says `claude.bat` and `claude_local.bat` are not two-env aware, with "(to be fixed in #613)" markers — but this PR implemented the fix
- F2 (Skip): `MCP_CODER_VENV_DIR` set by `env.py` points to project env — `PYTHONPATH` in `.mcp.json` may resolve wrong for programmatic launch
- F3 (Skip): Duplicated discovery logic between `claude.bat` and `claude_local.bat`
- F4 (Skip): `reinstall.bat` endlocal/activate edge case with `deactivate` not clearing `VIRTUAL_ENV`
- F5 (Accept): `.mcp.json` inconsistent path separators — `workspace` uses forward slash, `tools-py` uses backslash
- F6 (Skip): `reinstall_local.bat` installs langchain/mlflow unconditionally

**Decisions:**
- F1: Accept — docs should reflect completed work, bounded fix
- F2: Skip — explicitly out of scope per issue ("env.py has a known limitation but it's out of scope")
- F3: Skip — already accepted in plan review as acceptable for batch scripts
- F4: Skip — speculative edge case
- F5: Accept — Boy Scout fix, file was touched in this PR, one-line change
- F6: Skip — design decision following reference template, out of scope

**Changes:**
- `docs/environments/environments.md`: Updated entry point matrix to show `claude.bat` and `claude_local.bat` as two-env aware (Yes), removed "(to be fixed in #613)" markers, renamed "Current -- Broken" section headers to reflect new state
- `.mcp.json`: Standardized `workspace` server command to use backslashes matching `tools-py`

**Status:** Committed (1a35e11)

## Round 2 — 2026-03-29

**Findings:**
- F1 (Skip): `MCP_CODER_VENV_DIR` set to project env in `templates.py`/`env.py` — pre-existing, out of scope
- F2 (Accept): Docs say "registry" but scripts use `where mcp-coder` (PATH lookup)
- F3 (Skip): Inconsistent PYTHONPATH separators in `.mcp.json` — pre-existing
- F4 (Skip): Trailing backslash on workspace PYTHONPATH — pre-existing
- F5 (Skip): Self-hosting edge case with pipx global installs — speculative
- F6 (Skip): Subprocess spawning in pip show parsing — acceptable for startup script

**Decisions:**
- F1: Skip — pre-existing issue, explicitly out of scope per issue
- F2: Accept — incorrect text introduced in round 1 doc fix, quick correction
- F3-F6: Skip — pre-existing or speculative

**Changes:**
- `docs/environments/environments.md`: Corrected "registry" to "PATH lookup" in entry point matrix and prose

**Status:** Committed (0b3f5fe)

## Round 3 — 2026-03-29

**Findings:** None. All prior fixes verified correct. No new issues.
**Decisions:** N/A
**Changes:** None
**Status:** No changes needed

## Final Status

- **Rounds:** 3
- **Commits:** 2 (1a35e11, 0b3f5fe)
- **All checks pass:** pylint, pytest (2925), mypy, ruff
- **No remaining issues**
