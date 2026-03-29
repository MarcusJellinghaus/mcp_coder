# Implementation Review Log — Run 1

**Issue:** #609 — feat(vscodeclaude): add --from-github option
**Date:** 2026-03-29

## Round 1 — 2026-03-29

**Findings:**
- C1: Misleading `from_github` docstring in `build_session()` says "triggered from GitHub" instead of describing the install-from-GitHub behavior
- C2: Inconsistent `.get()` vs direct `session["from_github"]` access between `session_restart.py` and `session_launch.py`
- C3: (Not applicable — no `__main__` tests in this PR)
- C4: File split coupled unrelated test classes (pre-existing structural issue)
- S1: `open(pyproject_path, "rb")` should use `Path.open("rb")` for codebase consistency
- S2: Weak test assertion with `or` in `test_from_github_only_packages` — trivially true
- S3: No error handling for malformed TOML in `_build_github_install_section`
- S4: Location-dependent test path in `test_pyproject_config.py`

**Decisions:**
- C1: **Accept** — incorrect docs, simple fix
- C2: **Accept** — use `.get("from_github", False)` in both places for safety with old sessions
- C3: **Skip** — not applicable
- C4: **Skip** — pre-existing/structural, not blocking
- S1: **Accept** — Boy Scout fix, consistent with codebase
- S2: **Accept** — real logic bug in test
- S3: **Skip** — speculative (YAGNI), missing file/section already handled
- S4: **Skip** — minor, common pattern

**Changes:**
- Fixed docstring in `helpers.py` (`build_session` `from_github` param)
- Changed direct access to `.get("from_github", False)` in `session_launch.py`
- Changed `open()` to `pyproject_path.open()` in `workspace.py`
- Replaced weak `or`-based assertion with focused single assertion in test

**Status:** Committed as `65c6a88`

## Round 2 — 2026-03-29

**Findings:**
- 1: No error handling for malformed TOML (re-raised from round 1 S3)
- 2: Missing test for absent `pyproject.toml` when `from_github=True`
- 3: `open()` vs `Path.open()` in test file
- 4: `tomllib` import at module level but only used by one function

**Decisions:**
- 1: **Skip** — already triaged as YAGNI in round 1, pyproject.toml comes from git clone
- 2: **Accept** — real untested code path, bounded effort
- 3: **Skip** — cosmetic, test code
- 4: **Skip** — style preference, module-level imports are standard Python

**Changes:**
- Added `test_from_github_missing_pyproject_toml` test covering the absent-file guard path

**Status:** Committed as `2582306`

## Round 3 — 2026-03-29

**Findings:**
- 3a: `open()` in test file (re-raised)
- 3b: Commit message narrative slightly misleading (not actionable)
- 3c: Inline imports in test file

**Decisions:**
- All **Skip** — cosmetic/not actionable, no code changes warranted

**Changes:** None

**Status:** No changes needed

## Final Status

**Rounds:** 3
**Commits produced:** 2 (`65c6a88`, `2582306`)
**Remaining issues:** None — all critical and accepted findings resolved
**Branch status:** CI pending, may need rebase onto main
