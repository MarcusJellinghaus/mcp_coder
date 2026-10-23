# review-plan review log 1

## Round 1 — 2026-10-23
**Findings**:
Plan's file list matches the 191 `locked` sites. Now spot-checking the helpers and test names the plan refers to.pr_info/steps/step_8.md:24 — high — The `_make_pr_issue` snippet `labels=labels or []` doesn't match the current helper at `tests/workflows/vscodeclaude/test_checks.py:73`, which uses `labels if labels is not None else ["status-10:pr-created"]`. The snippet drops the `"status-10:pr-created"` default for `labels=None`, so tests that rely on it would change behaviour, and the "(keep existing None handling)" note contradicts the snippet it sits next to. Replace the snippet with `labels=labels if labels is not None else ["status-10:pr-created"]`, plus `title="PR Created Issue"` and `assignees=["testuser"]` as the non-defaults.
pr_info/steps/step_9.md:15 — low — When `_issue` is retyped to return `IssueData`, `tests/services/test_branch_info.py` needs `IssueData` imported from `mcp_coder.mcp_workspace_github`; the file has no such import today. The step doesn't say to add it or where it comes from.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_8.md:24, change the `_make_pr_issue` snippet so it keeps the current default from tests/workflows/vscodeclaude/test_checks.py:73. Use `labels=labels if labels is not None else ["status-10:pr-created"]`, with `title="PR Created Issue"` and `assignees=["testuser"]` as the non-default fields. Remove or reword the \'(keep existing None handling)\' note so it agrees with the snippet.', 'In pr_info/steps/step_9.md near line 15, add an instruction to put `from mcp_coder.mcp_workspace_github import IssueData` in tests/services/test_branch_info.py when `_issue` is retyped to return `IssueData`.'], escalate_reason=None)
**Changes**:
applied
