# Summary — Issue #1489: workflow log lines that mislead, and a force-push that sends nothing

## Goal

Three independent fixes to what the workflows log and do:

1. **create-plan** logs "Step 4/7", "Step 5/7" and "Step 6/7" when each prompt
   actually starts, instead of all three before the first prompt runs.
2. **Rebase step**: a rebase that left HEAD equal to `origin/<branch>` no longer
   force-pushes. It logs `Already up to date with origin/<branch>; nothing to push`
   and returns `ok`.
3. **Check runs** say what they ran:
   - INFO: one line per `check@…` / `test@…` request in the implement check loop,
     with status, duration and the one-line summary.
   - DEBUG: one line per command-toolkit step, with label, command as run, exit
     code and duration (or label and status on an early return).

## Architectural / design changes

- **Step numbering moves into `run_planning_prompts`.** It now owns
  create-plan's step numbers 4–6. `run_create_plan_workflow` still owns 1–3 and
  7. Each "Step N/7" line replaces the matching "Executing prompt N" line, so the
  module gains no lines (it is 8 lines below the 750-line limit).
- **`RebaseOutcome.ok` means more.** Before: "rebase and push both succeeded".
  After: "the rebase succeeded and `origin/<branch>` holds HEAD", either because
  this step pushed it or because it was already there.
  - The comparison is HEAD vs `origin/<branch>` (full SHAs), never HEAD vs
    `pre_sha`. So local commits that the rebase did not rewrite are still pushed,
    for example the review dismiss round's round-log commit.
  - Every case that is not provably equal still pushes: different SHAs, no
    upstream (`None`), or the comparison raising.
  - All callers already handle `ok` correctly under the wider meaning, so no
    caller changes.
  - `_check_branch_not_moved` is untouched; the LLM rebase uses it too.
- **New helper `_up_to_date_branch`** in `workflow_steps/rebase.py`. It never
  raises, logs its own failure at DEBUG, and returns the branch name only when
  HEAD equals `origin/<branch>`.
- **Check-loop observability uses only `ActionResult.summary`.**
  - Nothing parses the summary, and `ActionResult` is unchanged (it lives in
    mcp-coder-utils).
  - Durations are measured locally with `time.perf_counter()`.
  - A small `_one_line` helper replaces newlines with `, ` and caps the text at
    `_SUMMARY_MAX = 200` characters, ending in `…` when cut.
- **`_run_step` DEBUG lines serve every caller**: the check loop, `run_binding`,
  the formatters and `rebase_checks.py`. That is intended.
- **Log levels:** every new line is INFO or DEBUG, never WARNING (Jenkins' Text
  Finder marks a build UNSTABLE on any WARNING).

## Files modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/create_plan/core.py` | Step 4–6 lines move from `run_create_plan_workflow` into `run_planning_prompts` |
| `src/mcp_coder/workflow_steps/rebase.py` | New `_up_to_date_branch`; `_attempt_rebase_and_push` skips the push when up to date; docstrings updated |
| `src/mcp_coder/workflows/review/steps.py` | Comment before the CI gate and the `_after_steps` docstring (comment and docstring text only) |
| `src/mcp_coder/workflows/implement/check_loop.py` | `_run_group` logs one INFO line per non-skipped request; new `_one_line`, `_SUMMARY_MAX` |
| `src/mcp_coder/toolkits/command/toolkit.py` | `_run_step` logs one DEBUG line per step and on each early return |
| `docs/architecture/toolkit-interface.md` | Implement fix-loop bullet describes the new INFO line |
| `tests/workflows/create_plan/test_prompt_execution.py` | Step-line ordering test |
| `tests/workflow_steps/test_rebase.py` | `test_ok` / `test_push_failed` give `origin/feature` no SHA so the push still runs |
| `tests/workflow_steps/test_rebase_branch_moved.py` | New `TestUpToDate` class reusing the `mocks` fixture |
| `tests/workflows/implement/test_check_loop.py` | New `TestRequestLogging` class |
| `tests/toolkits/command/test_toolkit_run.py` | DEBUG assertions for a normal step and the three early returns |

No files or modules are created (other than these plan files).

## Constraints that apply to every step

- 750-line limit per file: `create_plan/core.py` (742) must not grow, and
  `tests/workflow_steps/test_rebase.py` (708) gets only edits in place.
- No new WARNING log lines.
- Before each commit: `run_format_code`, then pylint, mypy and pytest (fast unit
  set; add `git_integration` for rebase changes).

## Steps

1. `step_1.md`: create-plan step lines at prompt start.
2. `step_2.md`: rebase skips the push when HEAD equals `origin/<branch>`.
3. `step_3.md`: check loop INFO line per request, plus the doc update.
4. `step_4.md`: command toolkit `_run_step` DEBUG lines.
