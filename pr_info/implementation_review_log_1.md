# Implementation Review Log — Issue #885

**Issue:** install-from-github not auto-detected from pyproject.toml
**Branch:** 885-bug-vscodeclaude-install-from-github-not-auto-detected-from-pyproject-toml
**Date:** 2026-04-27

## Round 1 — 2026-04-27

**Findings:**
1. Leftover `"install_from_github": True` in test mock dict (`tests/cli/commands/coordinator/test_commands.py:366`) — dead data from removed TypedDict field
2. Stale test class/method names referencing old `--install-from-github` flag (`tests/cli/commands/coordinator/test_commands.py:266-340`) — `TestInstallFromGithubWiring` and methods
3. Stale test class name `TestInstallFromGithubThreading` (`tests/workflows/vscodeclaude/test_session_launch.py:176-177`)
4. Correctness of `regenerate_session_files` defaulting to auto-detect — verified correct by design
5. All source references to old `install_from_github` parameter properly removed — verified clean
6. Test coverage is thorough — auto-detect, opt-out, threading all covered

**Decisions:**
- Finding 1: **Accept** — misleading dead data, simple removal
- Finding 2: **Accept** — Boy Scout Rule, names should match current naming
- Finding 3: **Accept** — consistency with finding 2
- Findings 4-6: **Skip** — verified clean, no action needed

**Changes:**
- Removed `"install_from_github": True` from mock return dict in test_commands.py
- Renamed `TestInstallFromGithubWiring` → `TestSkipGithubInstallWiring`, updated method names and docstrings
- Renamed `TestInstallFromGithubThreading` → `TestSkipGithubInstallThreading`, updated docstring

**Status:** Committed (80dc583)

## Round 2 — 2026-04-27

**Findings:** None — round 1 fixes verified correct, no stale references remain.

**Decisions:** N/A

**Changes:** None

**Status:** No changes needed

## Final Checks

- **vulture:** Clean (no output)
- **lint-imports:** Clean (22/22 contracts kept)

## Final Status

Review complete. 2 rounds, 1 commit produced. All findings addressed. No remaining issues. Implementation is correct and matches issue requirements.
