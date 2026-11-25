# Step 2 — Move `checks.py` to the new package `workflows/pr_health/` (move only)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`), plus
> `.claude/knowledge_base/refactoring_principles.md`. Implement step 2 only: move
> `src/mcp_coder/workflows/vscodeclaude/checks.py` to `src/mcp_coder/workflows/pr_health/checks.py`
> and its tests to `tests/workflows/pr_health/`. No behaviour change. Remove the `check_pr_health`
> re-export from `workflows/vscodeclaude/__init__.py` to avoid an import cycle. Run all checks from
> the summary (pylint's cyclic-import check must pass); produce exactly one commit.

## WHERE

- New package: `src/mcp_coder/workflows/pr_health/__init__.py`, `src/mcp_coder/workflows/pr_health/checks.py`
- Modified: `src/mcp_coder/workflows/vscodeclaude/__init__.py`,
  `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py`
- New test package: `tests/workflows/pr_health/__init__.py` (empty)
- Moved tests (from `tests/workflows/vscodeclaude/` to `tests/workflows/pr_health/`, same file names):
  `test_checks.py`, `test_checks_alerts.py`, `test_checks_pr_cache.py`,
  `test_checks_review_comments.py`, `test_checks_review_comments_trust.py`, `_review_comments_helpers.py`
- New: `tests/workflows/pr_health/test_checks_rate_limit.py`
- Modified: `tests/workflows/vscodeclaude/test_rate_limit_reraise.py`,
  `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py`, `vulture_whitelist.py`

## WHAT

```python
# src/mcp_coder/workflows/pr_health/__init__.py
"""PR-health checks for status-10 issues."""
from .checks import check_pr_health
__all__ = ["check_pr_health"]
```

`pr_health/checks.py` = the old `vscodeclaude/checks.py`, unchanged except relative imports:
`from ..vscodeclaude.config import get_github_username, get_repo_full_name` and
`from ..vscodeclaude.issues import _filter_eligible_vscodeclaude_issues` (both removed in step 3).
`...workflow_utils.issue_helpers` / `...mcp_workspace_github` etc. keep the same depth (`...`).

## HOW

1. Move the module: `mcp__mcp-tools-py__move_module` (or `move_file` + import fixes) to
   `src/mcp_coder/workflows/pr_health/checks.py`; create `pr_health/__init__.py` as above.
2. `workflows/vscodeclaude/__init__.py`: delete the `# PR-health checks` import block and
   `"check_pr_health"` (with its comment) from `__all__`. `move_module` rewrites that import instead
   of removing it — remove it by hand.
3. `commands_vscodeclaude.py`: drop `check_pr_health` from the `....workflows.vscodeclaude` import;
   add `from ....workflows.pr_health import check_pr_health`. Call site unchanged in this step.
4. Tests — move the 6 files with `mcp__mcp-workspace__move_file`, then update:
   - `CHECKS = "mcp_coder.workflows.pr_health.checks"` in `test_checks.py` and `_review_comments_helpers.py`;
   - imports `from tests.workflows.vscodeclaude.test_checks` / `._review_comments_helpers` →
     `tests.workflows.pr_health...`; `from mcp_coder.workflows.vscodeclaude.checks` →
     `mcp_coder.workflows.pr_health.checks`.
5. `tests/workflows/pr_health/test_checks_rate_limit.py`: move class `TestCheckPrHealthRateLimit`
   (all 3 tests, unchanged) out of `tests/workflows/vscodeclaude/test_rate_limit_reraise.py`. Give the
   new file its own copies of `_rate_limit()` and `_wrapped_rate_limit()` and
   `CHECKS = "mcp_coder.workflows.pr_health.checks"`; import `REPO_CONFIG`, `_make_pr_issue`,
   `_setup` from `tests.workflows.pr_health.test_checks`.
6. `test_rate_limit_reraise.py` (remaining): remove the `check_pr_health` import, the
   `from tests.workflows.vscodeclaude.test_checks import (...)` block and the now unused `CHECKS`
   constant. Keep `_rate_limit` and `_wrapped_rate_limit` (other classes use them).
7. `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py`: `_CHECKS =
   "mcp_coder.workflows.pr_health.checks"` and the in-function import
   `from mcp_coder.workflows.pr_health.checks import check_pr_health`. Its other patches
   (`commands_vscodeclaude.check_pr_health`) keep working.
8. `vulture_whitelist.py` (`_no_allowlist` comment, around line 544): replace the stale paths
   `tests/workflows/vscodeclaude/test_checks_review_comments.py and test_checks_review_comments_trust.py`
   with `tests/workflows/pr_health/...`.

## ALGORITHM

None (pure move).

## DATA

Unchanged.

## Verify

- Test count unchanged (all moved tests collected under `tests/workflows/pr_health/`).
- Moved tests did not rely on `tests/workflows/vscodeclaude/conftest.py` (its autouse `_trusted_body`
  only patches `session_launch`). If a moved test fails only because it lost a fixture from that
  conftest, write one line to `pr_info/.blocked.txt` and stop.
- `run_pylint_check` reports no `cyclic-import` (R0401).
- `mcp__mcp-workspace__search_files` for `vscodeclaude.checks` / `vscodeclaude\.checks` finds only
  docs (fixed in step 6).
