# review-plan review log 1

## Round 1 — 2026-10-25
**Findings**:
Reviewing the plan; checking the HTML matrix's current length against the 750-line limit.pr_info/steps/step_7.md:116 — high — The HTML matrix is already 746 lines with 34 cards. The rewrite adds 12 cards, a `label-commands` block on most cards, transition text, new CSS rules and 2 swatches, so it will end up well over 750 lines and step 7 will reliably stop at the `.blocked.txt` exit. Decide this in the plan now: either add `docs/processes-prompts/github_Issue_Workflow_Matrix.html` to `.large-files-allowlist` in this step (the issue's 750-line limit only covers new docs), or require compact markup (single-line cards, no blank spacer lines).
pr_info/steps/step_7.md:53 — medium — Test 3 checks `cmd in card_block`, which is a substring match. `/issue_analyse` is a substring of `/issue_analyse_supervisor` on the 01 card's manual line, so the test passes even with no auto-launch line. Match the exact `<code>{cmd}</code>` inside the auto-line element instead, for example by giving the auto `<div>` its own class.
pr_info/steps/step_7.md:49 — medium — The issue requires every label to have exactly one `.label-name`, but no test asserts it. `_cards()` also silently overwrites duplicate names, so a leftover duplicate card (such as the escalation cards this step drops) would go unnoticed. Add a check that `findall` has no duplicates, either to test 2 or as a fourth test.
pr_info/steps/step_7.md:110 — medium — "List the labels using each colour" in the Color Reference could be written with `class="label-name"` markup, which would make the uniqueness and `_cards` logic fail or mislead. State that the swatch label lists use `color-name`/plain text, never `label-name`.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_7.md (around line 116), settle the 750-line limit in the plan: add `docs/processes-prompts/github_Issue_Workflow_Matrix.html` to `.large-files-allowlist` as an explicit step 7 action, because the file is already 746 lines and the 750-line limit applies only to new docs. That way the step cannot stop at the `.blocked.txt` exit.', 'In pr_info/steps/step_7.md test 3 (around line 53), replace the substring check `cmd in card_block` with an exact match. Give the auto-launch `<div>` its own class, such as `auto-command`, and assert that `<code>{cmd}</code>` appears inside that element, so `/issue_analyse` no longer matches `/issue_analyse_supervisor`.', "In pr_info/steps/step_7.md (around line 49), add an assertion that the `.label-name` values from `findall` contain no duplicates, either in test 2 or as a new test 4. This enforces the issue's rule of exactly one `.label-name` per label before `_cards()` builds its dict.", 'In pr_info/steps/step_7.md (around line 110), state that the Color Reference swatch label lists must use `color-name` or plain text and must never use `class="label-name"` markup.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-25
**Findings**:
Reading the existing source files to check the plan's facts against them.pr_info/steps/step_1.md:112 — medium — The issue requires commits ordered "so links stay valid at every step", and steps 1–4 create docs full of relative links (`../../../.claude/skills/...`, `../../../src/mcp_coder/prompts/prompts.md`, `../../configuration/config.md`). But `tools/lychee_check.bat` first runs in step 6, so a wrong relative prefix stays broken across commits 1–5 (step_6.md:34 even expects this as the "common case"). Add the lychee run to the Checks of steps 1–5, with 0 errors as the exit criterion (same for step_2.md:94, step_3.md:94, step_4.md:57, step_5.md:75).
**Decisions**:
Verdict(decision='tasks', tasks=["Add `tools/lychee_check.bat` to the Checks section of steps 1–5 (pr_info/steps/step_1.md:112, step_2.md:94, step_3.md:94, step_4.md:57, step_5.md:75), with 0 link errors as each step's exit criterion. This keeps relative links valid at every commit, as the issue requires. Update step_6.md:34 so it no longer expects broken links from earlier steps to be the common case."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-10-25
**Findings**:
Checked all nine step files against the issue. Now spot-checking `labels.json` and `tools/lychee_check.bat`.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
