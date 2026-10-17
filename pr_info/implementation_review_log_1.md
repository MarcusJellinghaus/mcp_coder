# Implementation Review Log 1 — Issue #1170

Branch: `1170-enable-ruff-s-flake8-bandit` (base `main`)
Scope: enable ruff `S` (flake8-bandit) with `S404`/`S603` ignored globally, `S101` ignored for `tests/**` only, `S105`/`S106`/`S108` ignored for tests; resolve the remaining findings with justified `noqa`.
Note: no `pr_info/steps/` plan exists for this branch; the issue text and the discussion in-session are the requirements.

## Round 1 — 2026-10-17
**Findings**:
- No Critical or Accept items.
- `# noqa: S101  # nosec B101` pairs in `cli/commands/rebase.py` and `workflows/rebase.py` are redundant for CI (no bandit run in `.github/`, pre-commit or tox); only the `run_bandit_check` tool could still read `nosec`.
- `_env.py` assert (`last_err is not None`) would fire only for `attempts <= 0`; `workflows/rebase.py` assert would fail only for an empty-string branch.
- Comment style mixes `--` (new) and `—` (pre-existing) in `noqa` reasons.
- Verified true: all 20 `src/` S101 noqas sit on the line ruff reports; reasons for `input_area.py`, `create_plan/core.py`, `_env.py`, `workflows/rebase.py` hold; both `S604` justifications are accurate; `skills.py:144` is correctly left alone; no behaviour change beyond comments/noqa/config.
**Decisions**:
- Skip `nosec` removal — harmless, cosmetic, and bandit consolidation is #1177's scope.
- Skip `_env.py` / `rebase.py` edge cases — speculative (only matters if a caller later passes invalid input).
- Skip comment-style unification — cosmetic.
**Changes**: none.
**Status**: no changes needed

## Final Status
- Rounds run: 1 (zero code changes → loop ended).
- Commits reviewed: `380b9eb`, `fbb0fbb`. No code commits produced by the review.
- `run_vulture_check`: clean. `run_lint_imports_check`: 21 contracts kept, 0 broken.
- Open issues: none.
