# review-plan review log 1

## Round 1 — 2026-10-28
**Findings**:
Checking test helpers and `failure_handling` to validate the plan's test recipes.pr_info/steps/step_2.md:70 — low — The new tests build `CalledProcessError` (also step_4.md:78), but the step doesn't say where to import it in tests. The `subprocess_isolation` contract also forbids `import subprocess` under `tests`, so state the source: `mcp_coder.utils.subprocess_runner`.
pr_info/steps/step_1.md:56 — low — `comment_safe` strips the suffix and caps the length but leaves newlines in multi-line stderr. The comment's single-line `**Error:** <value>` field then spills onto later lines. Also, the step 2 assertion that "the `**Error:**` line value is ≤ 300 chars" only holds for single-line input.
pr_info/steps/summary.md:26 — low — The summary says the `CalledProcessError` fallback is `str(exc)`, but step_1.md:53 and the issue use `f"{name}: {exc}"`. Align the summary with step 1.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md (near line 70) and pr_info/steps/step_4.md (near line 78), say that tests import `CalledProcessError` from `mcp_coder.utils.subprocess_runner`, not from `subprocess`. The `subprocess_isolation` import-linter contract forbids `import subprocess` under `tests`.', 'In pr_info/steps/step_1.md (near line 56), make `comment_safe` collapse newlines and other line breaks to single spaces, before it strips the suffix and caps the length, so the `**Error:**` field stays on one line. In step_2.md, add a test case with multi-line stderr input. The test asserts that the `**Error:**` value is one line and at most 300 chars.', 'In pr_info/steps/summary.md (near line 26), change the `CalledProcessError` fallback from `str(exc)` to `f"{name}: {exc}"` to match step_1.md:53 and the issue.'], escalate_reason=None)
**Changes**:
applied
