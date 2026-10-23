# review-plan review log 1

## Round 1 — 2026-10-23
**Findings**:
Plan's file list matches the 191 `locked` sites. Now spot-checking the helpers and test names the plan refers to.pr_info/steps/step_8.md:24 — high — The `_make_pr_issue` snippet `labels=labels or []` doesn't match the current helper at `tests/workflows/vscodeclaude/test_checks.py:73`, which uses `labels if labels is not None else ["status-10:pr-created"]`. The snippet drops the `"status-10:pr-created"` default for `labels=None`, so tests that rely on it would change behaviour, and the "(keep existing None handling)" note contradicts the snippet it sits next to. Replace the snippet with `labels=labels if labels is not None else ["status-10:pr-created"]`, plus `title="PR Created Issue"` and `assignees=["testuser"]` as the non-defaults.
pr_info/steps/step_9.md:15 — low — When `_issue` is retyped to return `IssueData`, `tests/services/test_branch_info.py` needs `IssueData` imported from `mcp_coder.mcp_workspace_github`; the file has no such import today. The step doesn't say to add it or where it comes from.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_8.md:24, change the `_make_pr_issue` snippet so it keeps the current default from tests/workflows/vscodeclaude/test_checks.py:73. Use `labels=labels if labels is not None else ["status-10:pr-created"]`, with `title="PR Created Issue"` and `assignees=["testuser"]` as the non-default fields. Remove or reword the \'(keep existing None handling)\' note so it agrees with the snippet.', 'In pr_info/steps/step_9.md near line 15, add an instruction to put `from mcp_coder.mcp_workspace_github import IssueData` in tests/services/test_branch_info.py when `_issue` is retyped to return `IssueData`.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-23
**Findings**:
Plan and issue read; now checking the plan's file list and named tests against the code.`pr_info/steps/step_6.md:22` — medium — The sentinel list names only `test_failure_handling.py` (~186) and `test_prerequisites.py` (~55). It leaves out the third "not found" sentinel at `tests/workflows/create_plan/test_main.py:131` (`empty_issue_data = IssueData(number=0, title="", state="", url="", ...)`). Line 25 then sends "all other literals" to `make_issue_data(...)`, which contradicts issue item 4 for that site. Add `test_main.py` `empty_issue_data` (~line 131) to the list of sites that use `create_empty_issue_data()`.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_6.md:22, add the `empty_issue_data` sentinel in tests/workflows/create_plan/test_main.py (around line 131) to the list of sites that use `create_empty_issue_data()`. That way the 'all other literals -> make_issue_data(...)' rule on line 25 no longer covers it, which matches issue item 4."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-10-23
**Findings**:
Still reviewing: checking the `number=0` sentinel sites against the plan's file list.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
