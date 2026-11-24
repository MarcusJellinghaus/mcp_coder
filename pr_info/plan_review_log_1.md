# review-plan review log 1

## Round 1 — 2026-11-24
**Findings**:
Reviewing plan for #1451: checking code sites the plan touches (check_loop, command toolkit, verify rows).Checking the docs page the plan's step 4 edits for other now-stale statements.`pr_info/steps/summary.md:31` — low — The summary says "Rebase doesn't change", but step 1 does change rebase. Rebase sessions pass `bash_grants` to `prompt_llm`, and the injected `system-prompt.md` has a `[check_instructions]` slot. That slot will now list only the rebase binding's grants instead of every declared step. This change fits Decision 4, but the plan should say so, and step 1 should add one test that pins it.

`pr_info/steps/step_1.md:41` — medium — `CommandToolkit.prompt_fragments()["check_instructions"]` becomes dead code. It still builds the full `_RERUN_INTRO + _steps_text(all_steps)` list, but `resolve_prompt_slots` now always overrides it for a Bash toolkit. That leaves two places that build the re-run list. The plan also adds a toolkit→`prompt_slots` import only to keep this dead text the same. The fragment only needs to be `""` for `llm_permissions = "none"`, so step 1 should make prompt_slots the only place that builds the list: drop the all-steps text in the fragment and adjust `test_toolkit_describe.py`. The issue already lists that test file for updating. Do not move `RERUN_INTRO` across layers just to keep dead output unchanged.

`pr_info/steps/step_2.md:78` — medium — The acceptance test only checks `llm_permissions` per entry, which already works today. Two parts of the issue's acceptance criteria are covered only by mocked unit tests:
- the implement-task session gets the union of `check@quick`, `check@standard` and `test@quick`;
- no session gets a re-run line for `check.full`, `test.mutation`, `format.apply` or `format.check`.

Add a test on the same real command-toolkit project. It should feed the scoped grants for `implement_task` + `implement_final` and for `implement_final` alone into `resolve_prompt_slots("[check_instructions]", …)`. It should assert the listed commands are exactly those grants and include none of the four unrequested commands.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/summary.md:31, replace 'Rebase doesn't change' with a statement that rebase sessions now list only the rebase binding's grants in the [check_instructions] slot, under Decision 4. In pr_info/steps/step_1.md, add one test that pins this: a rebase session's resolved [check_instructions] lists only the rebase binding's grants.", "In pr_info/steps/step_1.md, make resolve_prompt_slots the only place that builds the re-run list. Change CommandToolkit.prompt_fragments()['check_instructions'] so it no longer builds _RERUN_INTRO + _steps_text(all_steps). Keep only the '' result needed for llm_permissions = 'none'. Drop the planned toolkit→prompt_slots import and do not move RERUN_INTRO across layers. Update test_toolkit_describe.py to match.", "In pr_info/steps/step_2.md, add an acceptance test on the same real command-toolkit project. It passes the scoped grants for implement_task + implement_final, and for implement_final alone, into resolve_prompt_slots('[check_instructions]', ...). For implement_task, assert the listed commands are exactly the union of check@quick, check@standard and test@quick. For both cases, assert that check.full, test.mutation, format.apply and format.check do not appear."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-24
**Findings**:
Checking the command toolkit's grant format and session call sites against the plan's claims.Nearly done — checking pylint limits that could affect step 3's added helper and the larger `toolkit_rows`.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
