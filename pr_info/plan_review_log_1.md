# review-plan review log 1

## Round 1 — 2026-10-21
**Findings**:
Plan read; checking the code sites the steps target (rebase, review, fix-ci, verify, import contracts).Checking whether the plan's root autouse fixture collides with the import-health test.Checking implement's pre-body rebase path for a second pre-flight call.`pr_info/steps/step_7.md:41` — medium — The new autouse patch of `mcp_coder.cli.commands.verify._print_project_section` (a mock returning `True`) stops `execute_verify` from printing the PROJECT header. That breaks `tests/cli/commands/test_verify_sections_orchestration.py:423`, which calls `output.index("PROJECT")`, and the step does not list that test. Fix: give the patch a `side_effect` that still prints the header, or list the test and say how to adjust it.
`pr_info/steps/step_3.md:53` — low — Issue item 9 asks for "`format_code = false` → formatter not called" tests for each workflow. The plan only tests the gate inside `run_formatters` and rebase's call to `run_formatters`. Review, fix-ci and `check_branch_status` get no test that they still format through `run_formatters`, so the acceptance criterion "no formatting from any of those entry points" is not tested at every entry point.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_7.md (around line 41), fix the autouse patch of mcp_coder.cli.commands.verify._print_project_section. As written it hides the PROJECT header and breaks tests/cli/commands/test_verify_sections_orchestration.py:423, which calls output.index("PROJECT"). Either give the mock a side_effect that still prints the PROJECT header and returns True, or add that test to the step with an explicit instruction for adjusting it.', 'In pr_info/steps/step_3.md (around line 53), add tests for issue item 9 at each remaining entry point. Review, fix-ci and check_branch_status each need a test showing they format through run_formatters, so that format_code = false means no formatter is called from that entry point.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-21
**Findings**:
Reviewing plan against code: checking rebase `_preflight` callers and the review/check_branch_status sites.Checking verify exit code and section functions for step 7 consistency.Reading the planning principles to finish the review.`pr_info/steps/step_3.md:60` — low — The new review test for `format_code = false` gets only a directory (`tests/workflows/review/`), not a file. Unlike step 4, this step says nothing about the 750-line limit. The obvious target, `tests/workflows/review/test_core_after_steps.py`, already has 736 lines, so the test should go in the new `test_core_formatter_preflight.py` that step 4 already names.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_3.md (around line 60), name a specific file for the new review test that checks format_code = false. Use tests/workflows/review/test_core_formatter_preflight.py, the file step 4 already introduces, not tests/workflows/review/test_core_after_steps.py: that file has 736 lines, and adding the test there could push it past the 750-line limit.'], escalate_reason=None)
**Changes**:
applied
