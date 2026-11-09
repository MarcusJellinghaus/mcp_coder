# review-plan review log 1

## Round 1 — 2026-11-09
**Findings**:
Plan files read and the prompt grep shows every Python mention is covered. Now checking a few code facts: the toolkit runner API, the rebase permissions, and the system prompt.`pr_info/steps/step_5.md:9` — medium — The Done-when rule "no prompt in `src/mcp_coder/prompts/` names pylint/mypy/pytest/`mcp__mcp-tools-py__*` or (case-insensitive) 'Python project'" is only checked by a one-off LLM grep that writes `.blocked.txt`. Nothing automated guards it. Add a test in Step 5 that scans every `src/mcp_coder/prompts/*.md` file, after the `[test_filter]` rename.
`pr_info/steps/step_2.md:94` — medium — The prompt-text test only covers the Implementation, Finalisation, CI Fix and plan sections. The Task Tracker Update and Review Implementation Reviewer rewording in this step (step_2.md:28, :33) has no test. The all-files test from the finding above would also cover these sections.
`pr_info/steps/step_4.md:44` — low — Runs `bash_grants_of(llm_permissions(project_dir, "claude"))` before `resolve_prompt_slots`, which repeats the same Bash-grant check and loads the toolkit again. Compute the "declares Bash grants" flag once and reuse it, or note that the duplicate load is intended.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_5.md, add a test that runs after the `[test_filter]` rename. It scans every `src/mcp_coder/prompts/*.md` file and fails if any of them names pylint, mypy, pytest or `mcp__mcp-tools-py__*`, or contains 'Python project' in any letter case. Put this test in the step's Done-when criteria in place of the one-off grep that writes `.blocked.txt`.", 'In pr_info/steps/step_2.md, add test coverage for the reworded Task Tracker Update and Review Implementation Reviewer sections (see step_2.md:28 and :33). Either extend the prompt-text test to assert the new wording, or point to the all-files prompt scan from Step 5 as the test that covers these sections.'], escalate_reason=None)
**Changes**:
applied
