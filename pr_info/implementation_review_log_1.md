# Implementation Review Log — Issue #701

## Round 1 — 2026-04-07

**Findings**:
- F1 (Critical): Fix #3 from issue #701 not implemented — redundant status cache call remains in coordinator status flow (commands.py:665 calls both `_build_cached_issues_by_repo` and `build_eligible_issues_with_branch_check`, latter re-fetches per repo).
- F2 (Critical): `_list_issues_no_error_handling()` silently returns `[]` when `_get_repository()` returns None — defeats Fix #1.
- F3 (Minor): Broad `except Exception` in `get_all_cached_issues`.
- F4 (Minor): `is_full_refresh` condition retains `not last_checked` guard.
- F5 (Minor): Snapshot restore assigns to ephemeral `cache_data["issues"]`.
- F6 (Minor): Tests use `CacheData` literals without `last_full_refresh` (valid per NotRequired).
- F7 (Minor): `test_list_issues_github_error_handling` docstring slightly misleading.
- F8 (Out of scope): `_fetch_additional_issues` still uses decorator-wrapped `get_issue`.
- F9 (Pre-existing): `test_issue_cache.py` exceeds 750-line guideline.

**Decisions**:
- F1 Accept: Explicitly required by issue #701 Decision #4. Not a major refactor; pattern exists in session_launch.
- F2 Accept: Defeats Fix #1 — must raise instead.
- F3 Skip: Broad catch is intentional for "any non-auth failure" case; documented with pylint disable.
- F4 Skip: Harmless historic guard; removing risks subtle bugs.
- F5 Skip: Correct as-is; current form is self-documenting.
- F6 Skip: Valid per TypedDict NotRequired.
- F7 Skip: Coverage adequate via sibling test.
- F8 Skip: Out of scope for #701.
- F9 Skip: Pre-existing.

**Changes**:
- `manager.py`: `_list_issues_no_error_handling()` raises `RuntimeError` on None repo.
- `workflows/vscodeclaude/issues.py`: `build_eligible_issues_with_branch_check()` accepts optional `cached_issues_by_repo` to skip redundant fetch.
- `cli/commands/coordinator/commands.py`: status flow passes pre-fetched dict.
- Tests added/updated in `test_issue_manager_core.py`, `test_issue_cache.py`, `test_core.py`, `test_vscodeclaude_cli.py`.
- All 5 quality checks pass (pylint, pytest, mypy, lint-imports, vulture).

**Status**: Committed (pending commit agent).


## Round 2 — 2026-04-07

**Findings**:
- Broad `except Exception` in cache.py (may mask programmer errors).
- `RuntimeError` is a weak exception type (vs domain-specific).
- Snapshot restore doesn't persist additional_dict to disk on failure.
- `last_full_refresh` `NotRequired` field is always normalized to present.
- `_filter_eligible_vscodeclaude_issues` reloads labels config per repo (pre-existing).
- Pr_info artifacts committed.
- `DUPLICATE_PROTECTION_SECONDS` not touched (consistent with plan).

**Decisions**: All Accept/Skip — zero critical findings. Broad exception matches existing codebase pattern. RuntimeError adequate given the broad catch in cache.py. Additional_dict persistence is correct-by-design. NotRequired is lenient for callers. Labels reload is pre-existing. Pr_info artifacts are expected deliverables.

**Changes**: None — no code changes required.

**Status**: No changes needed.

## Final Status

- **Rounds**: 2
- **Commits produced**: 1 (`5b6a3e2` — fix: propagate repo lookup failure and drop redundant status cache call)
- **Quality checks**: All 5 MCP checks pass (pylint, pytest, mypy, lint-imports, vulture) + ruff docstrings
- **Issue #701 coverage**: Fix #1 (propagate list_issues failures), Fix #2 (last_full_refresh field + threshold), Fix #3 (eliminate redundant status cache call) — all implemented and tested.
- **Outstanding issues**: None.
