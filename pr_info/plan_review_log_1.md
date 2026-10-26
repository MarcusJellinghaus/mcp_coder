# review-plan review log 1

## Round 1 — 2026-10-26
**Findings**:
Plan files, the issue, and the source file have all been read. Last check: the pylint config, because the docstring-only class left after step 1 could trip a lint rule.pr_info/steps/summary.md:60 — medium — The directory baseline is fixed at "**688** … must stay 688 after every step". Issue step 1 says to record the actual value ("688, or the recorded value") because #1319/#1320 may land first and change the count. As written, the gates in every step would then fail on that drift and block the run. Record the measured count in step 1 and compare later steps against that.
pr_info/steps/step_1.md:37 — medium — The baseline gate runs only the 22-passed `-v` run. It skips the issue's step-1 collect-only baselines: the directory total, `test_session_restart.py` → 16 and `test_session_launch_process_issues.py` → 6. So nothing records the "baseline" that later gates compare against.
pr_info/steps/step_2.md:37 — low — Its list of source imports to remove includes `Path`, but groups C and D (`tmp_path: Path`) still use it in the source. Following the example literally would cause an `F821`. Remove `Path` from the example and leave the decision to ruff.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/summary.md:60, replace the hard-coded directory baseline of 688 with the count measured in step 1 ("688, or the recorded value", per the issue). Later step gates should compare against that recorded value, not a fixed 688.', "In pr_info/steps/step_1.md:37, add the issue's collect-only baselines to the step-1 gate and record their results: the total for the test directory, test_session_restart.py (expect 16) and test_session_launch_process_issues.py (expect 6). Later gates compare against these numbers.", 'In pr_info/steps/step_2.md:37, remove `Path` from the example list of source imports to delete, because groups C and D still use `tmp_path: Path`. Say that ruff decides which imports are unused.'], escalate_reason=None)
**Changes**:
applied
