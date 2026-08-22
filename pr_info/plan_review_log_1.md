# review-plan review log 1

## Round 1 — 2026-08-22
**Findings**:
I'll gather context now.`pr_info/steps/step_5.md:107` — high — Step 5 adds 4 new tests to `tests/workflows/implement/test_core_workflow.py`, which is already 747 lines and is **not** in `.large-files-allowlist`; the CI `file-size` job (`mcp-coder check file-size --max-lines 750`, `.github/workflows/ci.yml`) will fail. Plan should place the blocked-routing tests in a new module (e.g. `test_core_blocked.py`) or split the file.
`pr_info/steps/step_3.md:160` — medium — "the `blocked` reason reaches core.py and falls through its reason chain to the generic path" is factually wrong: `core.py:155-191` has no `else`, so an unmatched reason falls past the chain to `progress.completed += 1` and re-enters the `while True` loop — between Step 3 and Step 5 a blocked run counts the task as completed and re-invokes the LLM instead of failing. Either merge Step 5's `core.py` branch into Step 3 or state the real intermediate behaviour.
`pr_info/steps/summary.md:93` — medium — "All three paths that stage everything get cleanup" omits the CI-fix loop: `check_and_fix_ci` (called from `implement/core.py` after finalisation) runs its own LLM turns and commits at `workflow_steps/ci.py:247`, so a marker written there is still committed into the branch and surfaces in the PR diff — the exact failure mode §5/§6 exist to prevent. Excluding a blocked *channel* for CI-fix is in scope; excluding *cleanup* is not justified.
`pr_info/steps/summary.md:98` — low — the per-task `check_and_fix_mypy` call (`task_processing.py:427`) also runs LLM turns between the blocked read and the Step 9 `commit_changes` (`task_processing.py:451`); it is dormant only because `RUN_MYPY_AFTER_EACH_TASK = False`, which the plan does not state.
`pr_info/steps/step_3.md:19` — low — start-of-task cleanup lives inside `process_single_task`, which never runs when `prepare_task_tracker` fails first; that stage runs its own LLM turn and hard-fails on any extra changed file (`task_tracker_prep.py:120-127`), so a marker written there is never cleaned and blocks the next run at `check_git_clean`.
`pr_info/steps/step_8.md:13` — low — `github_Issue_Workflow_Matrix.html` is 718 lines and not allowlisted; 4 CSS rules + 4 six-line cards lands at ~746 of the 750-line CI gate, leaving almost no margin for a differently formatted card.
**Decisions**:
Verdict(decision='tasks', tasks=['Fix pr_info/steps/step_5.md:107 — do not add the 4 blocked-routing tests to tests/workflows/implement/test_core_workflow.py (747 lines, not allowlisted, would breach the 750-line CI file-size gate). Update the plan to place them in a new module such as tests/workflows/implement/test_core_blocked.py.', "Fix pr_info/steps/step_3.md:160 — the claim that the 'blocked' reason 'falls through its reason chain to the generic path' in core.py is wrong: core.py:155-191 has no else, so an unmatched reason falls past the chain to progress.completed += 1 and re-enters the while loop, meaning between Step 3 and Step 5 a blocked run counts the task as completed and re-invokes the LLM. Either move Step 5's core.py branch into Step 3, or correct the text to describe the real intermediate behaviour.", "Fix pr_info/steps/summary.md:93 — the statement 'All three paths that stage everything get cleanup' omits the CI-fix loop: check_and_fix_ci (invoked from implement/core.py after finalisation) runs its own LLM turns and commits at workflow_steps/ci.py:247, so a marker written there gets committed into the branch and appears in the PR diff. Update the plan to cover cleanup for the CI-fix path (or state and justify the exclusion of the blocked channel there explicitly)."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-08-22
**Findings**:
I'll gather context now.`pr_info/steps/step_4.md:12` — high — Step 4's file list omits `tests/cli/commands/test_define_labels.py:69-72`, which hard-asserts `len(labels_config["workflow_labels"]) == 36`; adding a 37th label fails that test, so Step 4 cannot land green as written (the issue's "five places to touch" is likewise incomplete).

`pr_info/steps/step_2.md:14` — high — `tests/workflows/implement/test_core_workflow.py` is 747 lines and is not in `.large-files-allowlist`; Step 2 adds a `TaskOutcome` import (+1) and line 114 grows 82→104 chars so black wraps it to 4 lines (+3), landing at 751 and breaching the 750-line CI `file-size` gate. Step 5 reasons about this gate explicitly; Step 2 does not.

`pr_info/steps/step_7.md:10` — medium — placing `read_and_clear_blocked` immediately before the step-4 changes check leaves it after the empty-response guard at `finalisation.py:104-106`, which returns `False`; a marker written by the finalisation agent before an empty response is never deleted and poisons the next run at `check_git_clean` — the identical bypass Step 3 solves with `finally`.
**Decisions**:
Verdict(decision='tasks', tasks=['Fix pr_info/steps/step_4.md:12 — the file list omits tests/cli/commands/test_define_labels.py:69-72, which hard-asserts len(labels_config["workflow_labels"]) == 36. Add that test file to Step 4\'s file list and specify updating the count assertion to 37 so the step lands green.', "Fix pr_info/steps/step_2.md:14 — Step 2's edits to tests/workflows/implement/test_core_workflow.py (747 lines, not in .large-files-allowlist) push it to ~751 lines via the TaskOutcome import plus black wrapping line 114, breaching the 750-line CI file-size gate. Make Step 2 account for this gate explicitly, as Step 5 does — e.g. split the file or relocate the affected tests.", 'Fix pr_info/steps/step_7.md:10 — placing read_and_clear_blocked immediately before the step-4 changes check leaves it after the empty-response guard at finalisation.py:104-106 which returns False, so a marker written before an empty response is never cleared and poisons the next run at check_git_clean. Use the same finally-based cleanup pattern Step 3 applies so the marker is cleared on every exit path.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-08-22
**Findings**:
I'll gather context now.I reviewed the knowledge base, issue #1112, and all nine plan files against the actual source, tests and CI gates.

`pr_info/steps/step_4.md:12` — high — file list omits `tests/workflows/vscodeclaude/test_types.py:309`, which hard-asserts `len(human_action_labels) == 26`; the new label is `category: human_action`, making it 27, so Step 4 lands red as written (same class of miss as the round-2 `36` finding).
`pr_info/steps/step_4.md:12` — high — file list omits `tests/cli/commands/test_define_labels_label_changes.py:308,311`, which assert `len(result["created"]) == 35` and `create_label.call_count == 35`, both derived from the bundled 36-label config; a 37th label makes them 36 and the step lands red.
`pr_info/steps/summary.md:214` — high — the "Modified — tests" list (and the Step 4 row at `:231`, "2 test files") propagates the same omission: `tests/workflows/vscodeclaude/test_types.py` and `tests/cli/commands/test_define_labels_label_changes.py` must be listed as touched by Step 4.
**Decisions**:
Verdict(decision='tasks', tasks=["Fix pr_info/steps/step_4.md:12 — add tests/workflows/vscodeclaude/test_types.py to Step 4's file list and specify updating the assertion at line 309 (len(human_action_labels) == 26 → 27), since the new label is category: human_action.", 'Fix pr_info/steps/step_4.md:12 — add tests/cli/commands/test_define_labels_label_changes.py to Step 4\'s file list and specify updating the assertions at lines 308 and 311 (len(result["created"]) == 35 and create_label.call_count == 35 → 36) which derive from the bundled label config.', "Fix pr_info/steps/summary.md:214 and :231 — update the 'Modified — tests' list to include tests/workflows/vscodeclaude/test_types.py and tests/cli/commands/test_define_labels_label_changes.py, and correct the Step 4 row's '2 test files' count to match the full set of test files Step 4 touches."], escalate_reason=None)
**Changes**:
applied

## Round 4 — 2026-08-22
**Findings**:
I'll gather context now.`pr_info/steps/step_4.md:13` — high — the `test_define_labels_label_changes.py` row lists only `:308` and `:311`; the same file asserts `len(result["created"]) == 35` a third time at `:366` (in `test_apply_labels_dry_run_mode`), built from the same bundled `labels.json` via the `labels_config_path` fixture, so it also becomes `36` — Step 4 lands red as written. Same omission repeats at `step_4.md:69`, `:103` ("both `:308` and `:311`") and `:132` (LLM PROMPT).

`pr_info/steps/summary.md:219` — high — propagates the same omission: "`35` → `36` at `test_define_labels_label_changes.py:308,311`" must also cover `:366`; the Step 4 row at `:238` ("`35` → `36` twice") must read three times.
**Decisions**:
Verdict(decision='tasks', tasks=['Fix pr_info/steps/step_4.md — the test_define_labels_label_changes.py entries at :13, :69, :103 and :132 list only lines 308 and 311, but the same file asserts len(result["created"]) == 35 a third time at :366 (test_apply_labels_dry_run_mode, built from the same bundled labels.json via the labels_config_path fixture). Update every one of those references to cover :308, :311 and :366 (35 → 36), including the LLM PROMPT at :132.', 'Fix pr_info/steps/summary.md — line :219 must list test_define_labels_label_changes.py:308,311,366 for the 35 → 36 change, and the Step 4 row at :238 must say the change occurs three times rather than twice.'], escalate_reason=None)
**Changes**:
applied

## Round 5 — 2026-08-22
**Findings**:
I'll gather context now.`pr_info/steps/step_5.md:80` — medium — the final-mypy cleanup is a bare `read_and_clear_blocked(project_dir)` before `get_full_status`, bypassed by the two early returns above it (`core.py:220-227` typed LLM failure from `check_and_fix_mypy`, `core.py:236-240` formatting failure); Steps 3 and 7 use `finally` for exactly this bypass class, so a marker written by the mypy-fix turn can survive and poison the next run at `check_git_clean` / `prepare_task_tracker`.
`pr_info/steps/step_7.md:145` — medium — LLM PROMPT says "write the two tests described in the step file" while the TESTS section at `:93` lists three; the third (`test_commit_message_path_has_no_double_prefix`) is the only test pinning the §9 live-bug fix, so the implementing agent can drop it and land the behavioural fix unpinned.
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
