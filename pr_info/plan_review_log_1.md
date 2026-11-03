# review-plan review log 1

## Round 1 — 2026-11-03
**Findings**:
Still reviewing — checking code references the plan relies on.`pr_info/steps/step_3.md:25` — medium — `x_steps = {l.step for l in new if l.checked}` puts `None` in the set whenever a `## Pull Request` checkbox is `[x]`, because `step` is reset on every `##` header. All `[ ]` lines in `## Pull Request` (step `None`) then fall under the per-name limit. The issue says they are unrestricted, so a valid restructure that adds PR tasks would be rejected. Fix: exclude `None` from `x_steps` and add a test case with an `[x]` in `## Pull Request`.
`pr_info/steps/step_6.md:29` — medium — After 3 failed restructure attempts, the final `TrackerPrepError` message is built from the last attempt's `check_restructure` errors. Those name tasks, not file lines. The issue's acceptance criterion ("3 failed repairs → `fail("general", …)`, and the message names the offending line(s)") and this step's own test ("message names the offending lines") need the original line-numbered `violations` in the final message. Fix: append `describe_violations(violations)` to the repair failure message.
`pr_info/steps/step_5.md:6` — medium — Step 5 is too large for one commit. It rewrites prep (exception, guard, restore, LLM rounds, session wiring), rewires `core.py`, removes `has_implementation_tasks` from 3 modules, adds the Jenkins signature, and changes about 7 test files. Splitting it would follow the knowledge-base rule "prefer several small steps": for example (a) `TrackerPrepError`, the `core.py` wiring, the Jenkins signature and the classifier-based skip/INVALID decision, then (b) the guard, byte restore and `_llm_rounds` feedback loop.
`pr_info/steps/step_2.md:42` — low — After step 1, the parser ends `## Tasks` at a `### Pull Request` or `#### Pull Request` header. The classifier only ends it at `## Pull Request` and reports other levels as violations. The issue says the classifier mirrors the parser. The result is safe (INVALID), but the deviation should be stated and covered by a test, or the boundary aligned with the parser.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_3.md:25, exclude None from x_steps (e.g. `{l.step for l in new if l.checked and l.step is not None}`) so that `[ ]` lines under `## Pull Request` stay unrestricted even when a PR checkbox is `[x]`. Add a test case where `## Pull Request` contains an `[x]` line and a valid restructure adds new PR tasks; the restructure must be accepted.', "In pr_info/steps/step_6.md:29, build the final TrackerPrepError message after 3 failed restructure attempts with `describe_violations(violations)` appended, so the original line-numbered violations appear in it. Make the step's test assert that the message names the offending line numbers.", 'Split pr_info/steps/step_5.md into two steps and renumber the later steps to match: (a) TrackerPrepError, the core.py wiring, the Jenkins signature, the classifier-based skip/INVALID decision, removal of has_implementation_tasks, plus their tests; (b) the guard, the byte restore and the _llm_rounds feedback loop, plus their tests.', 'In pr_info/steps/step_2.md:42, make the classifier end `## Tasks` on the same headers the step-1 parser uses, including `### Pull Request` and `#### Pull Request`, as the issue requires. Add a test that the classifier and the parser agree on these header levels.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-03
**Findings**:
Verifying code facts the plan relies on (core.py wiring, `commit_paths`, template sections, Jenkins stage line).`pr_info/steps/step_2.md:41` — high — The scanner's section rules never say when the "instructions" section ends. Only Tasks, Pull Request and "after pull_request → other" are defined, so a `## Step 1` header after `## Instructions for LLM` can be left in "instructions". Step 3 skips that section, so `has_completed_tasks` would miss the `[x]` lines of a template-based `## Step N` tracker. That sends the tracker down the reset path and deletes completed work, which is the exact case §3 of the issue guards against. Fix: state that outside `## Tasks` every level-2 header ends the current section (headers with other names → "other").
`pr_info/steps/step_3.md:34` — high — The `has_completed_tasks` test uses a `## Step N` tracker with one `[x]`, and the `## Step N` restructure test at `pr_info/steps/step_7.md:48` is similar. Neither requires the fixture to contain the template's `## Instructions for LLM` block before the `## Step N` headers, so the section-end bug above would pass both tests. Fix: build these fixtures from `TASK_TRACKER_TEMPLATE`'s instruction block followed by `## Step 1` with an `[x]`, and assert True / the restructure path.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md:41, add an explicit rule to the scanner\'s section rules: outside `## Tasks`, every level-2 header ends the current section. A level-2 header that is not Tasks or Pull Request starts an "other" section. This means a `## Step N` header after `## Instructions for LLM` leaves the "instructions" section, so its `[x]` lines are counted.', "In pr_info/steps/step_3.md:34 (the has_completed_tasks test) and pr_info/steps/step_7.md:48 (the `## Step N` restructure test), build the fixtures from TASK_TRACKER_TEMPLATE's `## Instructions for LLM` block followed by `## Step 1` containing an `[x]` line. Assert has_completed_tasks returns True, and assert the restructure path is taken, not reset."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-11-03
**Findings**:
Checking whether `commit_paths` and core wiring exist as the plan assumes.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
