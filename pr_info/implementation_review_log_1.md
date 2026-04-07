# Implementation Review Log — Issue #336

Branch: `336-create-plan-workflow-failure-handling-mirror-implement-pattern`
Started: 2026-04-07


## Round 1 — 2026-04-07

**Findings**:
1. Success-path `update_workflow_label` missing `validated_issue_number=issue_number` (medium)
2. Stale `(unused currently)` qualifier in `post_issue_comments` docstring (low)
3. Duplicate `is_working_directory_clean` check in orchestrator + `check_prerequisites` (low)
4. Stage label `"Prompt 1 (empty response)"` reused for the no-session_id branch (low)
5. `Commit failed: None` rendered when `commit_result["error"]` absent (low)
6. `_format_failure_comment` omits `### Uncommitted Changes` section when diff empty (informational — divergence from implement)
7. `WorkflowFailure` duplication local vs shared (informational)

**Decisions**:
- Accept #1, #2, #3, #4, #5 — all worth fixing.
- Skip #6 — intentional, plan workflow has no partial progress to show.
- Skip #7 — informational only, no action needed.

**Changes**:
- #1: success-path `update_workflow_label` now passes `validated_issue_number=issue_number`.
- #2: reworded `post_issue_comments` docstring to clarify it enables posting failure comments on the issue.
- #3: removed the duplicate `is_working_directory_clean` block from `check_prerequisites`; tests in `test_prerequisites.py` updated (dirty-repo / git-error tests removed since orchestrator owns that check now).
- #4: stage label changed from `"Prompt 1 (empty response)"` to `"Prompt 1 (no session_id)"` for the no-session_id branch; matching test assertion updated.
- #5: commit/push failure messages now use `commit_result.get("error") or "unknown error"` (and analogous for push) — no more `"None"` rendering.
- Files changed:
  - `src/mcp_coder/workflows/create_plan/core.py`
  - `src/mcp_coder/workflows/create_plan/prerequisites.py`
  - `tests/workflows/create_plan/test_prerequisites.py`
  - `tests/workflows/create_plan/test_prompt_execution.py`

**Status**: committed. Quality: pylint, mypy, lint-imports, vulture clean; 3268 tests passed.


## Round 2 — 2026-04-07

**Findings**:
1. M1 (minor): `except ValueError` after `is_working_directory_clean` in the orchestrator labels failures as `"Prerequisites (git working directory not clean)"`, but `ValueError` is actually raised when the path is *not a git repo at all*. Branch is effectively dead because the CLI layer validates `.git` via `resolve_project_dir`.
2. M2 (informational): `pr_info/steps/Decisions.md` says `_handle_workflow_failure` drops the `issue_number` parameter, but commit `31f249d` correctly re-added it for early-failure paths. Plan doc is now stale; code is correct.

**Decisions**:
- Skip M1 — explicitly non-blocking, branch is unreachable in practice. Not worth the churn.
- Skip M2 — stale plan doc, code is correct. Plan artifacts are historical.

**Changes**: none (no code changes this round).

**Status**: review approved. Quality: 185 scoped tests passed. Loop complete.

## Final Status

- **Rounds run**: 2
- **Code commits produced this review**: 1 (`efb75b6` — round-1 review fixes)
- **Outstanding issues**: none blocking. Two minor observations from round 2 (M1 dead branch, M2 stale plan doc) intentionally skipped.
- **Result**: Implementation approved.
