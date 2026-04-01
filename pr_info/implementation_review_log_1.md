# Implementation Review Log — Issue #657

**Feature**: Soft-delete mechanism for undeletable session folders
**Date**: 2026-04-01

## Round 1 — 2026-04-01

**Findings**:
1. Critical — Temp files (tmp_extract.py, tmp_extract2.py, tmp_grep_helper.sh, tmp_node_extract.js) committed to branch
2. Accept — Broad exception handler in delete_session_folder skips soft-delete when was_clean=True
3. Accept — load_to_be_deleted only catches FileNotFoundError, not OSError/UnicodeDecodeError
4. Accept — warn_orphan_folders re-reads sessions.json and .to_be_deleted on every call
5. Skip — Retry loop re-reads .to_be_deleted per removal (fine at expected scale)
6. Skip — Race condition in add_to_be_deleted (already acknowledged as out of scope)
7. Skip — get_working_folder_path doesn't check sessions.json (caller flow prevents collision)
8. Skip — Bad commit message on f84864b (will be squashed in PR)

**Decisions**:
- Accept 1: Must remove temp files before merge
- Accept 2: Real bug — workspace file deleted but folder neither deleted nor soft-deleted
- Accept 3: Defensive robustness at system boundary, simple fix
- Accept 4: Easy parameter threading, avoids unnecessary I/O
- Skip 5-8: YAGNI, pre-existing, cosmetic, or handled by PR process

**Changes**:
- Removed 4 temp files
- Added soft-delete logic in broad exception handler of delete_session_folder
- Broadened load_to_be_deleted to catch OSError and UnicodeDecodeError
- Changed warn_orphan_folders to accept pre-loaded session_folders and to_be_deleted params
- Updated caller in cleanup.py and tests in test_sessions.py

**Status**: Committed as b23150c

## Round 2 — 2026-04-01

**Findings**:
1. Accept — Redundant `workspace_base is not None` check in broad exception handler (workspace_base is required str)
2. Skip — Unnecessary monkeypatch in warn_orphan_folders tests (harmless, pre-existing)
3. Skip — Missing encoding param in file I/O (cosmetic, ASCII-only content)

**Decisions**:
- Accept 1: Inconsistent with primary failure path, trivial fix
- Skip 2-3: Harmless/cosmetic

**Changes**:
- Removed redundant `and workspace_base is not None` from exception handler guard

**Status**: Committed as 08b33a7

## Round 3 — 2026-04-01

**Findings**: None
**Decisions**: N/A
**Changes**: None
**Status**: No changes needed — review complete

## Final Status

- **Rounds**: 3 (2 with code changes, 1 clean)
- **Commits produced**: 2 (b23150c, 08b33a7)
- **All quality checks pass**: Pylint, Mypy, Pytest (3121 tests), Ruff
- **Remaining issues**: None
