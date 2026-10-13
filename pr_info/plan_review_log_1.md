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

## Round 2 — 2026-10-13
**Findings**:
I'll gather the knowledge base principles, the issue context, and the plan files.No existing test asserts the old guard's `False` return, so removing it is safe. The round-1 critical finding is properly fixed in this round's plan. Let me check the step_2 low finding (branch_name not passed) — it was marked "applied" in decisions but let me verify if step_2.md still omits it.Confirmed counts match (27, 23) current baseline. Let me check `dispatch_workflow` to confirm `next_label` transition semantics and the `branch_strategy` field validity.Confirmed — dispatch_workflow handles the 71→72 transition itself. Plan is consistent with actual code.

Everything checks out: the round-1 critical finding is properly fixed, and the plan's technical claims against the codebase (signatures, dispatch mechanism, label counts, bypass patterns) all verify correctly.Confirmed accurate. The plan checks out against the actual codebase.

The round-1 critical finding (repo_url-mode label writes always failing) is correctly fixed in step_5.md: the guard in `label_transitions.py` is removed, `get_labels_config_path(None)` behavior is used as designed, and tests are updated to exercise the real path rather than mocking `update_workflow_label`. All structural assumptions (precondition checks, dispatch mechanism, template placeholders, label/command counts) verify against the actual source.

The round-1 low finding (`step_2.md`'s `update_workflow_label` calls not passing `branch_name=branch`) remains unaddressed — minor, not tasked last round.

NO FINDINGS

(The one remaining item is the previously-reported low-severity redundancy in step_2.md — repeating it below since it's still present.)

`pr_info/steps/step_2.md:82` — low — `update_workflow_label(IssueManager(project_dir), ...)` calls omit `branch_name=branch` even though `branch` is already resolved earlier in the algorithm, causing a redundant re-detection of the current branch inside `update_workflow_label`. Harmless but duplicated work.
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
