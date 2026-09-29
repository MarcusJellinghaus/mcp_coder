# review-plan review log 1

## Round 1 — 2026-09-29
**Findings**:
I'll gather context first.Now verifying key plan claims against the code.`pr_info/steps/summary.md:123` — high — Step ordering leaves two intermediate commits where the workflow is unbounded: after Step 1, `process_task_with_retry` returns `no_progress` (reason != `no_changes`) and after Step 2 it returns `no_progress_after_retries`; neither is routed in `core.py`'s else-less chain until Step 3, so both fall through to `progress.completed += 1` and loop forever, with the round cap not landing until Step 4. Order the cap (Step 4) first, and Step 3 before Step 2.

`pr_info/steps/step_1.md:20` — medium — Deleting the blanket `except Exception` from `get_next_task` lets non-`TaskTrackerError` exceptions escape too (`Path.read_text` raises `OSError`/`UnicodeDecodeError`, not wrapped), but the new call-site handler catches only `TaskTrackerError`, so those now propagate out of `process_single_task` into `run_guarded` instead of the intended `error` reason the issue specifies.

`pr_info/steps/step_1.md:105` — low — The autouse fixture's placement in `test_task_processing.py` is unspecified; the file is organised into classes and the ~24 `process_single_task` call sites span several of them, so a class-scoped placement would leave most of them broken.

`pr_info/steps/step_2.md:62` — low — `previous_reason` is read on the first loop iteration but the pseudocode only assigns it at the end of the body (`:68`); no initialisation before the loop.

`pr_info/steps/step_2.md:25` — low — Contradicts `:34`: the signature sketch places `previous_reason` after `attempt` (i.e. before `format_code`/`check_type_hints`), while HOW requires it to be the last parameter so positional call sites are unaffected.

`pr_info/steps/step_1.md:22` — low — Neither step updates the `Returns:` reason enumerations in the `process_single_task` (`task_processing.py:372`) and `process_task_with_retry` (`:568-570`) docstrings, which list the reason strings exhaustively.
**Decisions**:
Verdict(decision='tasks', tasks=["Reorder pr_info/steps/summary.md so the round cap (current Step 4) lands first and the core.py routing for new reasons (current Step 3) lands before the retry change (current Step 2), so no intermediate commit leaves an unbounded loop where 'no_progress'/'no_progress_after_retries' fall through to progress.completed += 1.", "In pr_info/steps/step_1.md, make the new get_next_task call-site handler catch the non-TaskTrackerError exceptions that the removed blanket except Exception used to absorb (e.g. OSError/UnicodeDecodeError from Path.read_text), so they map to the 'error' reason instead of propagating into run_guarded."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-09-29
**Findings**:
I'll gather context first.Now verifying the plan's code claims.`pr_info/steps/summary.md:126` — high — The plan applies "route before emit" to Step 3 but not to Step 4: Step 2's commit makes `process_single_task` return `no_progress`, which the unchanged `process_task_with_retry` passes straight to `core.py`'s else-less chain, so every no-progress round increments `progress.completed` and loops to the round cap (~20 LLM rounds + commits + pushes) until Step 4 lands. Step 4 has no real dependency on Step 2 — it can retry on the `"no_progress"` string before anything emits it, exactly as Step 3 routes a reason nothing emits — so ordering 1, 3, 4, 2 closes the window at zero cost.

`pr_info/steps/summary.md:130` — high — "4 needs both 2 (the reason) and 3 (its route)" is not true: Step 4's tests patch `process_single_task` and its change to `process_task_with_retry`/`previous_reason` compiles and passes without Step 2. The stated dependency is what forces the unbounded-emission window above.

`pr_info/steps/step_4.md:63` — medium — `previous_reason` is read in the call at `:64` on the first iteration but only assigned at `:70`; the pseudocode never initialises it before the loop, so a literal implementation raises `NameError`. (Raised in round 1, not applied.)

`pr_info/steps/step_4.md:69` — medium — `last_detail = outcome.detail` overwrites unconditionally, so a mixed sequence ending in `no_changes` (detail is always `""` at `task_processing.py:498`) reports `no_progress_after_retries` with an empty detail and Step 3's message loses the task name — contradicting the stated "the more informative reason wins".

`pr_info/steps/step_4.md:27` — low — The WHAT signature sketch places `previous_reason` immediately after `attempt` (i.e. before `format_code`/`check_type_hints`), contradicting HOW at `:36` which requires it to be the last parameter. (Raised in round 1, not applied.)

`pr_info/steps/step_2.md:25` — low — Neither Step 2 nor Step 4 updates the exhaustive `Returns:` reason enumerations in the `process_single_task` (`task_processing.py:372-375`) and `process_task_with_retry` (`:567-570`) docstrings, nor adds a `Raises:` to `get_next_task` whose contract changes from "returns None on error" to "propagates". (Raised in round 1, not applied.)
**Decisions**:
Verdict(decision='tasks', tasks=['Reorder pr_info/steps/summary.md to 1, 3, 4, 2 and correct the dependency note at :130: Step 4\'s retry keys off the "no_progress" string and needs no emitter, so landing the retry and its route before Step 2 emits the reason closes the window where every no-progress round increments progress.completed and burns the full round cap.', "In pr_info/steps/step_4.md, initialise previous_reason before the retry loop (e.g. previous_reason = None) so the first iteration's call at :64 does not read an unassigned name.", 'In pr_info/steps/step_4.md:69, stop overwriting last_detail unconditionally — keep the more informative detail so a sequence ending in no_changes (detail always "") still reports no_progress_after_retries with the task name in Step 3\'s message.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-09-29
**Findings**:
I'll gather context first.`pr_info/steps/step_4.md:127` — high — The autouse `_count_incomplete_tasks` fixture is added only to `test_task_processing.py`, but Step 3 creates `test_task_progress_gate.py` containing a prompt-assembly test (`step_3.md:128`) that calls `process_single_task` directly and patches only `prompt_llm`/`get_next_task`. After Step 4 that test hits the new real before-read, returns `"error"` before the LLM call, and fails — so Step 4 cannot land with checks green as written.

`pr_info/steps/step_4.md:105` — medium — The test list for Step 4 patches `_count_incomplete_tasks` per-test in `test_task_progress_gate.py`, which contradicts `:112` (after-read raises `TaskTrackerFileNotFoundError`) and `:113-120` (before-read raises) only being reachable via `side_effect` on that same patch; the plan never states which of the two reads each `side_effect` element/exception belongs to when `get_next_task` is separately patched.

`pr_info/steps/step_4.md:20` — medium — `_count_incomplete_tasks(project_dir: Path)` is specified without saying it must reproduce `get_next_task`'s path derivation (`str(project_dir / PR_INFO_DIR)`, `exclude_meta_tasks=True`); a literal implementation passing `project_dir` would read the wrong directory and always raise, turning every round into `"error"`.

`pr_info/steps/step_4.md:24` — low — `get_next_task`'s docstring contract changes from "returns None on error" to "propagates", and the exhaustive `Returns:` reason enumerations in `process_single_task` (`task_processing.py:372-375`) and `process_task_with_retry` (`:567-570`) are not updated for `no_progress` / `no_progress_after_retries`. (Raised in rounds 1 and 2, not applied.)

`pr_info/steps/step_5.md:63` — low — Tests 2 and 4 assert `stop and report` is absent from prompt sections that never contained it; both pass before the edit and guard nothing.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_4.md, extend the autouse _count_incomplete_tasks fixture (or add an equivalent) to test_task_progress_gate.py so Step 3\'s prompt-assembly test at step_3.md:128, which patches only prompt_llm/get_next_task, does not hit the new real before-read and return "error" before the LLM call — Step 4 must land with checks green.'], escalate_reason=None)
**Changes**:
applied

## Round 4 — 2026-09-29
**Findings**:
I'll gather context now.`pr_info/steps/step_4.md:20` — high — `_count_incomplete_tasks` is specified only by signature and docstring; the plan never states it must reproduce `get_next_task`'s path derivation (`get_incomplete_tasks(str(project_dir / PR_INFO_DIR), exclude_meta_tasks=True)`). A literal implementation passing `project_dir` reads the wrong directory and raises on every round, turning every production round into `"error"`. (Raised round 3, not applied.)

`pr_info/steps/step_4.md:101` — high — No planned test exercises the real `_count_incomplete_tasks`: tests 1–8 patch it, and both autouse fixtures patch it everywhere else. The one genuinely new function in the change — its path derivation and its `exclude_meta_tasks=True` flag — is covered by nothing, so the failure mode above ships green.

`pr_info/steps/step_4.md:112` — medium — Tests 4 and 5/6/7 both drive failures through patched objects, but the plan never says which of the two `_count_incomplete_tasks` reads a given `side_effect` element or exception belongs to when `get_next_task` is separately patched; test 4 ("after-read raises") is unimplementable as written without that mapping. (Raised round 3, not applied.)

`pr_info/steps/summary.md:104` — medium — The Modified table attributes `test_task_processing.py` changes to Step 4 only, but Step 5 also edits that file (`TestBlockedExitInPrompts`, `step_5.md:59`); the file-to-step mapping is incomplete.

`pr_info/steps/step_4.md:24` — low — `get_next_task`'s docstring contract changes from "returns None on error" to "propagates" with no `Raises:`, and the exhaustive `Returns:` reason enumerations in `process_single_task` (`task_processing.py:369-377`) and `process_task_with_retry` (`:566-570`) are not updated for `no_progress` / `no_progress_after_retries`. (Raised rounds 1–3, not applied.)
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_4.md:20, specify _count_incomplete_tasks\'s implementation explicitly: it must call get_incomplete_tasks(str(project_dir / PR_INFO_DIR), exclude_meta_tasks=True), matching get_next_task\'s path derivation, so a literal implementation does not read the wrong directory and turn every round into "error".', 'In pr_info/steps/step_4.md, add a test that exercises the real _count_incomplete_tasks (unpatched) against a temporary pr_info directory, asserting both the path derivation and that meta tasks are excluded.'], escalate_reason=None)
**Changes**:
applied

## Round 5 — 2026-09-29
**Findings**:
I'll gather context now.`pr_info/steps/step_4.md:13` — medium — Test 9 requires a new `real_tracker_count` pytest marker registered in `pyproject.toml` (`--strict-markers` is on in `addopts`), but `pyproject.toml` is listed neither in this step's WHERE section nor in `summary.md`'s Modified files table.
`pr_info/steps/summary.md:74` — medium — The Modified table attributes `test_task_processing.py` changes to Step 4 only; Step 5 also edits that file (`TestBlockedExitInPrompts`, `step_5.md:59`). (Raised round 4, not applied.)
`pr_info/steps/step_4.md:112` — medium — The plan never states which of the two `_count_incomplete_tasks` reads a given `side_effect` element or exception belongs to when `get_next_task` is patched separately, leaving test 4 ("after-read raises") under-specified. (Raised rounds 3–4, not applied.)
`pr_info/steps/step_4.md:24` — low — `get_next_task`'s docstring contract changes from "returns None on error" to "propagates" with no `Raises:`, and the exhaustive `Returns:` reason enumerations in `process_single_task` (`task_processing.py:369-377`) and `process_task_with_retry` (`:566-570`) are not updated for `no_progress` / `no_progress_after_retries`. (Raised rounds 1–4, not applied.)
`pr_info/steps/step_5.md:63` — low — Tests 2 and 4 assert `stop and report` is absent from prompt sections that never contained it; both pass before the edit and guard nothing. (Raised round 3, not applied.)
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
