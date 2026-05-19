# Implementation Review Log — Issue #977

**Branch:** `977-unify-mcp-config-path-resolution-relative-paths-should-resolve-against-project-dir-not-cwd`
**Started:** 2026-05-19
**Implementation commit:** `fe0633e3` — fix(cli): resolve --mcp-config relative paths against project_dir (#977)

**Scope:** Unify `--mcp-config` path resolution across all four sources (CLI flag, env var, TOML config, auto-detect) so relative paths resolve against `project_dir` (with CWD fallback when `project_dir is None`). Normalize `project_dir` once, update CLI strict-error message to include both Project and Current directory, document the rule, expand tests.

**Files changed (diff vs main):**
- `src/mcp_coder/cli/utils.py` (+38, parts rewritten)
- `tests/cli/test_utils.py` (+140)
- `docs/configuration/config.md` (+16)

Note: `pr_info/` was empty at review start — no formal plan/summary/Decisions/TASK_TRACKER existed. Pre-flight task-tracker check vacuously passes. Review proceeds against the issue spec as the authoritative requirements list.

## Round 1 — 2026-05-19

**Findings:**
1. Misleading "sibling dir" comment in `test_relative_config_falls_back_to_cwd_when_no_project_dir` (`tests/cli/test_utils.py`) — the file is in the same dir under a different name, not a sibling.
2. `test_resolve_mcp_config_explicit_not_found` does not pin the new error-message content (spec req #5: must contain `Project directory:` and `Current directory:`).
3. `if project_dir` vs `if project_dir is not None` — speculative, empty string is unrealistic.
4. Nested `_resolve_relative` rebuilt per call — speculative micro-opt.
5. Stale comment `# Explicit path: resolve and validate` should mention `base_dir`.
6. (Positive) DRY refactor with `_resolve_relative` + single `base_dir` is the right shape.
7. Unrelated pre-existing black failure in `workflows/vscodeclaude/cleanup.py` — not in this PR's diff.
- Spec compliance #7: only 1 of 2 autodetect tests tightened; defensible because the other covers `project_dir=None → CWD` (where distinct dirs is impossible).

**Decisions:**
- 1, 2, 5 → **Accept** (Boy Scout + spec gap)
- 3, 4 → **Skip** (speculative)
- 6 → no action (positive)
- 7 → **Skip** (pre-existing, out of scope)
- Spec #7 deviation → **Skip** (defensible, new project_dir=None branch test covers the case)

**Changes:**
- `tests/cli/test_utils.py`: switched `test_resolve_mcp_config_explicit_not_found` to `excinfo` form and asserted both `Project directory:` and `Current directory:`.
- `tests/cli/test_utils.py`: replaced misleading "sibling dir" comment with a one-liner that accurately describes the layout.
- `src/mcp_coder/cli/utils.py:200`: comment now reads `# Explicit path: resolve relative to base_dir and validate`.

**Verification:** format clean (466 files unchanged), full pytest suite 3994 passed / 2 pre-existing skipped, pylint clean, mypy clean.

**Status:** committed (see next git log entry on this branch)

## Round 2 — 2026-05-19

**Findings:** zero new accepted items. Re-flags of round 1's skipped items (falsy `project_dir` check, nested closure), cosmetic notes on non-ASCII `→` arrows and test-name conventions, and a comment on the review log file itself being on the branch (expected per CLAUDE knowledge base — `pr_info/` is process scratch).

**Decisions:** all Skip. No code changes.

**Status:** loop terminates — round produced zero code changes.

## Final Status

**Spec compliance (7 requirements):** all PASS. Req #7 partial in the literal "tighten 2 autodetect tests" reading, but defensible — the second autodetect test exercises `project_dir=None → CWD`, where distinct CWD/project_dir is structurally impossible. The 8 new tests cover that branch explicitly.

**Quality checks:**
- pytest unit suite: 3994 passed, 2 pre-existing skipped
- pylint: clean
- mypy (strict): clean
- ruff: clean
- vulture: no output
- lint-imports: 23 contracts kept, 0 broken

**Commits added on this branch during review:**
- `392010a5` test(cli): pin error message content and clarify comments

**Verdict:** ready to merge.
