# review-plan review log 1

## Round 1 — 2026-10-26
**Findings**:
`pr_info/steps/step_3.md:74` — medium — The step-3 compact diff runs "over the whole branch", and that diff also includes the `pr_info/` changes (plan files, `TASK_TRACKER.md`, the baseline notes written into `step_1.md`). Line 76 says to write `.blocked.txt` and stop on any deviation, so the implementer would treat those hunks as a broken compact-diff rule and stop for no reason. Fix: limit the diff to `tests/` and `.large-files-allowlist`, or exclude `pr_info/`.
`pr_info/steps/summary.md:23` — low — The issue's fallback says a test that fails at its new location must not be fixed by adding fixtures, `conftest.py` entries or patches. The plan only says "stop" and never states that ban.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_3.md:74, limit the compact diff to `tests/` and `.large-files-allowlist` (or exclude `pr_info/`), so the plan files, TASK_TRACKER.md and the baseline notes in step_1.md are not treated as deviations that trigger the `.blocked.txt` stop at line 76.', "In pr_info/steps/summary.md:23, state the issue's fallback rule: if a test fails at its new location, do not fix it by adding fixtures, conftest.py entries or patches. Write `.blocked.txt` and stop instead."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-26
**Findings**:
`pr_info/steps/step_3.md:74` — low — The compact diff is meant to cover "the whole branch", but no base ref is given (e.g. `args=["main...HEAD"]` or the `get_base_branch` result). It also runs before the step-3 commit. A plain `git diff` there would show only the uncommitted step-3 changes, so the steps 1–2 moves and the removed `from typing import Any` (which line 76 expects to see) would be missing. Fix: name the base ref, e.g. diff `<base>` against the working tree with `pathspec=["tests/", ".large-files-allowlist"]`.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_3.md:74, name the base ref for the whole-branch compact diff. Diff the base branch (from `get_base_branch`, e.g. `main`) against the working tree with `pathspec=["tests/", ".large-files-allowlist"]`, so the committed step 1–2 moves and the removed `from typing import Any` that line 76 expects all show up, along with the uncommitted step-3 changes.'], escalate_reason=None)
**Changes**:
applied
