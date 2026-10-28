# Step 6 — Final label helper: retry once, then non-zero exit (all six workflows)

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_6.md`).
> Implement only Step 6. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/workflow_utils/label_transitions.py`
- `src/mcp_coder/workflows/create_plan/prerequisites.py` (`update_success_label`) and `create_plan/core.py` (~line 696)
- `src/mcp_coder/workflows/implement/core.py` (~lines 370-397)
- `src/mcp_coder/workflows/create_pr/core.py` (`phase_b`, ~lines 683-709)
- `src/mcp_coder/workflows/fix_ci/core.py` (~line 129)
- `src/mcp_coder/workflows/fix_conflict/core.py` (~line 102)
- `src/mcp_coder/workflows/review/handoff.py` (`_set_label`, ~line 401) and `review/core.py` (~line 381)
- tests: `tests/workflow_utils/test_final_label.py` (new), `tests/workflow_utils/test_label_transitions.py`,
  and the workflow tests listed in the summary that patch `update_workflow_label`.

## WHAT
1. `update_workflow_label`: first line of the final `except Exception as e:` is
   `raise_if_rate_limited(e)` (import from `mcp_coder.workflow_utils.rate_limit`).
   Update the docstring ("Non-blocking except for rate limits, which raise
   `GitHubRateLimitError`").
2. New function in the same module (add to `__all__`):
   ```python
   FINAL_LABEL_RETRY_DELAY_SECONDS = 30

   def apply_final_label(
       project_dir: Path,
       from_label_id: str,
       to_label_id: str,
       issue_number: int | None = None,
   ) -> int:
       """Apply the workflow's final label; retry once after ~30 s.

       Returns 0 on success, 1 after the retry failed. Never raises or exits,
       so run_guarded's safety net is not triggered.
       """
   ```
3. Call sites — each returns the helper's code from `body()` / `phase_b()`:
   - create_plan: `update_success_label(...) -> int` keeps the
     `auto_review_plan` choice and returns `apply_final_label(project_dir, "planning", to_label_id, issue_number)`;
     `core.py`: `if update_issue_labels: rc = update_success_label(...); if rc: return rc`.
   - implement: `rc = apply_final_label(project_dir, "implementing", to_label_id)` when
     `update_issue_labels`, else 0; keep the summary logs; `return rc`.
   - create_pr `phase_b`: `rc = apply_final_label(project_dir, "pr_creating", label, cached_issue_number)`
     inside the existing `if update_issue_labels and cached_issue_number:`; keep the
     success log when `rc == 0`; `return rc` at the end.
   - fix_ci: `if update_issue_labels: return apply_final_label(project_dir, "fixing_ci", "pr_created")`.
   - fix_conflict: `return apply_final_label(project_dir, "fixing_merge_conflict", "pr_created")`
     replaces only the `else` (no-verdict) branch at `fix_conflict/core.py:102`
     (labels are hard-coded on, so no `update_issue_labels` check). The
     `if verdict:` branch keeps calling `_fail` and returning 0.
   - review: `_set_label(...) -> int` returns 0 when `update_issue_labels` is False,
     else `apply_final_label(project_dir, config.busy_label_id, to_label_id)`;
     `core.py:381` → `return _set_label(...)`; `handoff.py:401` → `return _set_label(...)`
     (update the handoff docstring "Always 0").
   - Remove the now-unused `update_workflow_label` / `IssueManager` imports and the
     old `try/except` wrappers at these sites.

## ALGORITHM
```
for attempt in (1, 2):
    if attempt == 2: time.sleep(FINAL_LABEL_RETRY_DELAY_SECONDS)
    try: if update_workflow_label(IssueManager(project_dir), from, to, validated_issue_number=issue_number): return 0
    except Exception as exc: logger.warning("Final label update failed (attempt %d): %s", attempt, exc)
number = issue_number or extract_issue_number_from_branch(get_current_branch_name(project_dir) or "")
logger.error("Final label update failed for issue #%s: intended label '%s'", number or "?", to)
return 1
```

## HOW
- `failure_handling.py:295` already wraps its own `update_workflow_label` call; no change.
- Tests (TDD), `tests/workflow_utils/test_final_label.py` (patch
  `label_transitions.update_workflow_label`, `label_transitions.IssueManager`,
  `label_transitions.time.sleep`):
  - success first try → 0, no sleep;
  - `False` then `True` → 0, one sleep of 30;
  - `False` twice → 1, exactly one ERROR naming the issue and `to_label_id`;
  - `GitHubRateLimitError` twice → 1;
  - issue number derived from branch when not given.
- `test_label_transitions.py`: a rate-limit `GithubException` from
  `transition_issue_label` now raises `GitHubRateLimitError`; other errors still → `False`.
- Workflow tests: patch `<module>.apply_final_label` instead of
  `update_workflow_label`. Per workflow add one test: helper returns 1 → workflow
  returns 1 **and** `handle_workflow_failure` (the `run_guarded` net) is not called.

## DATA
`apply_final_label -> int` (0 / 1). `update_success_label -> int`, `_set_label -> int`.
