# review-plan review log 1

## Round 1 — 2026-10-21
**Findings**:
Checking the review-comments test file's imports and patches against the plan's step 2 rewrite.`pr_info/steps/step_2.md:1` — medium — Step 2 packs too much into one commit: 4 source files, about 8 test files, the new signatures, `check_pr_health`, moving the call site and the CLI regression test. Split it in two. 2a: add `_resolve_pr_target`, `_escalate`, the new check signatures and `check_pr_health` with their `test_checks*` tests; `process_eligible_issues` calls `check_pr_health` in place of its check loop for now. 2b: move the call to the Step 4 loop, drop the `CIResultsManager` and label-lookup leftovers and their test patches, and add the CLI autouse fixture and `test_vscodeclaude_pr_health.py`.
`pr_info/steps/step_2.md:213` — low — The instruction for `TestProcessEligibleIssuesPriorityChaining` is unclear. "Move … into `test_checks.py` orchestration (covered by the chaining tests above)" can be read as either move it or drop it. State whether it is deleted as redundant or rewritten against `check_pr_health`.
**Decisions**:
Verdict(decision='tasks', tasks=['Split pr_info/steps/step_2.md into two steps. Step 2a: add `_resolve_pr_target`, `_escalate`, the new check signatures and `check_pr_health`, plus their `test_checks*` tests; for now `process_eligible_issues` calls `check_pr_health` instead of its check loop. Step 2b: move the call into the Step 4 loop, remove the `CIResultsManager` and label-lookup leftovers and their test patches, and add the CLI autouse fixture and `test_vscodeclaude_pr_health.py`. Update step numbering and cross-references to match.', 'In pr_info/steps/step_2.md:213, say exactly what happens to `TestProcessEligibleIssuesPriorityChaining`: either it is deleted because the `check_pr_health` chaining tests in `test_checks.py` already cover it, or it is rewritten against `check_pr_health` (name the target test class and file). Remove the wording that can mean either.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-21
**Findings**:
Checking whether step 2's interim call path leaks unpatched GitHub calls into the remaining session_launch tests.`pr_info/steps/step_2.md:142` — medium — During step 2, `process_eligible_issues` calls `checks.check_pr_health`, which calls `checks.get_github_username` (an alias of `get_authenticated_username`, which calls the GitHub API) and builds real managers. The remaining tests in `test_session_launch.py`, `test_session_launch_process_issues.py` and `test_session_restart_branch_integration.py` only patch `session_launch.get_github_username` and `session_launch.*Manager`, so in this step they reach the real GitHub API from unit tests. A setup failure is swallowed as a warning, so the tests can still pass while depending on the network. Fix: step 2 should patch `mcp_coder.workflows.vscodeclaude.checks.check_pr_health` in those tests (step 3 then drops the patch along with the call). Alternatively, step 2 deletes the check loop without adding an interim call, and step 3 adds the CLI call.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md (around line 142), tell the implementer to patch `mcp_coder.workflows.vscodeclaude.checks.check_pr_health` in the remaining tests in `test_session_launch.py`, `test_session_launch_process_issues.py` and `test_session_restart_branch_integration.py`. Without the patch, the interim `process_eligible_issues` call reaches `get_github_username` and the real managers. A shared autouse fixture or a per-test patch both work. In step 3, add a note to remove that patch at the same point the interim call is removed.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-10-21
**Findings**:
Reviewing the plan; checking whether step 2's kept-but-unused imports would fail pylint.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
