# review-plan review log 1

## Round 1 — 2026-10-13
**Findings**:
Precondition shapes match reality; the plan's technical assumptions are accurate. Checking the `log_level` placeholder used in step 4's template and the `--log-level` kwarg contract against existing formatting test.Found the critical issue at line 86-87. Finalizing the report now.

## Findings

`pr_info/steps/step_5.md:86` — critical — `update_workflow_label(issue_manager, ...)` will always return `False` (logged, swallowed) here: `issue_manager` is built via `IssueManager(repo_url=repo_url)` (confirmed in `session_launch.py`'s `process_eligible_issues`), so `issue_manager.project_dir is None`. `update_workflow_label` (`src/mcp_coder/workflow_utils/label_transitions.py`) unconditionally returns `False` with "Label update is not supported for repo_url mode" when `project_dir is None`, even when `validated_issue_number` is supplied — that check happens after the issue-number resolution, not gated on it. The detection step therefore can never actually set `status-71:merge-conflict`, which defeats the issue's core requirement. Step 5's planned tests mock `update_workflow_label` directly, so this never surfaces in the test suite as specified — the plan needs either a project_dir-independent label-transition path for the detection step, or a different mechanism for repo_url-mode label writes.

`pr_info/steps/step_2.md:—` (ALGORITHM section) — low — `update_workflow_label(...)` is called without `branch_name=branch` even though `branch` was already resolved earlier in `run_fix_conflict_workflow`; this makes `update_workflow_label` redundantly re-detect the current branch via `get_current_branch_name`. Harmless but duplicated work.

No other substantive gaps found — label counts (27→29 human_action, 23→24 CLI commands), the `PullRequestManager`/`IssueBranchManager` bypass pattern, `WORKFLOW_MAPPING`/`WORKFLOW_TEMPLATES` wiring, and `find_pull_request_by_head`'s `List[PullRequestData]` return type all check out against the actual codebase.
**Decisions**:
Verdict(decision='tasks', tasks=["Fix step_5.md's detection step: update_workflow_label(issue_manager, ...) always returns False in repo_url mode because IssueManager(repo_url=repo_url) leaves project_dir None, and label_transitions.py's project_dir is None check returns False before using validated_issue_number. Give the detection step a project_dir-independent way to write status-71:merge-conflict (e.g. pass project_dir through, or use a label-write path that works in repo_url mode), and update step 5's tests so they exercise the real label-write path instead of only mocking update_workflow_label."], escalate_reason=None)
**Changes**:
applied
