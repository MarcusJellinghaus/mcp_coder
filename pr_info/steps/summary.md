# Summary: every mcp-coder commit goes through `format@apply` (#1483)

## Goal

Every commit mcp-coder makes runs the toolkit's `commit` binding
(`format@apply`, `run_formatters`) first, best-effort. Exceptions, by design:

- the scoped round-log flush (`_flush_round_log(only=…)`), which instead
  writes markdown a formatter leaves unchanged;
- create-pr's cleanup commit, the `chore: renormalize line endings` commit, the
  LLM rebase's conflict-resolution commits, and the CLI `mcp-coder commit`.

Today these commits skip formatting: create-plan's plan commit, task tracker
preparation, finalisation, and the review's whole-tree round-log flushes. In a
repo whose formatter also formats markdown (Prettier via `npm run format`), the
plan files and the round logs land unformatted, and the review counts a
reformatted log as an "applied" fix.

## Architectural / design changes

1. **One best-effort formatter helper.**
   `workflow_steps/commit.py::format_best_effort(project_dir, context) -> None`
   wraps `run_formatters`. A raised `Exception` or a `False` return logs one
   WARNING (`Formatting failed before <context>`), and the helper never raises,
   so the caller's commit always happens. Every new call site is one line.
   `rescue_commit` keeps its own inline guard (unchanged).
2. **One autouse test fixture patches the formatter everywhere it is imported.**
   `tests/conftest.py::formatter_mocks` scans `sys.modules` and patches every
   `mcp_coder.*` module attribute that *is* the real `run_formatters` or
   `format_best_effort`, except in `workflow_steps.commit` itself. Because it
   matches by identity, no module list has to be maintained. Opt out with
   `@pytest.mark.real_formatters`.
3. **create-plan has a formatter pre-flight.** `check_formatter_config` runs
   after `manage_branch` and before `create_pr_info_structure` and the LLM work.
   A failure gets the `prereq` label (`planning_prereq_failed`). The plan commit
   is formatted.
4. **Task tracker preparation commits what the formatter changed.** After the
   LLM, the existing guard ensures only the tracker changed. So after
   `format_best_effort`, every other changed file (`_other_changed_files`,
   without `.mcp-coder/…`) came from the formatter. Those files are committed
   with the tracker. If the step does not finish, the `finally` also runs
   `reset_hard(project_dir, "HEAD")` when the formatter changed files.
5. **Finalisation formats** before its "no changes" check and commit.
6. **The review's whole-tree flush formats.** `_flush_round_log` without
   `only` calls `format_best_effort` before `commit_all_changes`. That covers
   the dismiss flush and every `_fail` flush. Scoped flushes stay unformatted.
7. **Dismiss round, implementation lane:** before `_after_steps(is_dismiss=True)`
   the review runs `_flush_round_log(project_dir, FORMAT_BEFORE_GATE_MESSAGE,
   push=False)`, with the message `style: format before the CI gate`. The
   commit the CI gate judges is therefore formatted. On a clean tree it commits
   nothing and stays silent. The plan lane (`run_after_steps=False`) skips it.
8. **"Applied" ignores review logs.**
   `review/steps.py::round_applied(project_dir, sha_before) -> bool` runs
   `git diff --name-only <sha_before>` (commit vs. working tree) and ignores
   `pr_info/*_review_log_*.md`. It is measured right after the round's commit
   and push, before `_after_steps`, so base-branch changes from the rebase are
   not counted. `core.py` no longer uses `is_working_directory_clean`.
9. **Stable markdown where formatting cannot run.**
   - `write_round_log` adds a blank line around headings and after block
     labels, strips each block's content, and separates blocks by exactly one
     blank line. The file ends with exactly one newline.
   - `TASK_TRACKER_TEMPLATE` gets a blank line after its two bold labels.
10. **Linux create-plan and review-plan templates run `mcp-coder setup`.**
    `_linux_setup_template` gains `checkout=` (create-plan stays on `main`) and
    `issue_flag=` (create-plan's watchdog keeps `--issue {issue_number}`).

## Files created or modified

### Source (`src/mcp_coder/`)

| File | Change |
|---|---|
| `workflow_steps/commit.py` | add `format_best_effort` |
| `workflows/review/review_log.py` | formatter-stable `write_round_log` |
| `workflow_utils/task_tracker.py` | blank lines in `TASK_TRACKER_TEMPLATE` |
| `cli/commands/coordinator/command_templates.py` | `_watchdog(issue_flag=)`, `_linux_setup_template(checkout=, issue_flag=)`, create-plan / review-plan Linux templates, header comment |
| `workflows/create_plan/core.py` | formatter pre-flight, `format_best_effort` before commit |
| `workflows/implement/task_tracker_prep.py` | format, commit formatter-changed files, restore via `reset_hard` |
| `workflows/implement/finalisation.py` | `format_best_effort` before the changes check |
| `workflows/review/handoff.py` | format in the whole-tree flush; `FORMAT_BEFORE_GATE_MESSAGE` |
| `workflows/review/core.py` | pre-gate flush on dismiss; `round_applied` measure |
| `workflows/review/steps.py` | add `round_applied` |

### Tests (`tests/`)

| File | Change |
|---|---|
| `conftest.py` | autouse `formatter_mocks` fixture |
| `test_formatter_mocks_fixture.py` (new) | fixture behaviour |
| `workflow_steps/test_commit_format_best_effort.py` (new) | helper tests |
| `workflows/review/test_review_log.py` | golden text + invariants |
| `workflow_utils/test_task_tracker_template.py` (new) | template blank lines |
| `cli/commands/coordinator/test_command_templates_setup.py` | six Linux setup templates |
| `workflows/create_plan/test_formatting.py` (new) | pre-flight + format |
| `workflows/implement/test_task_tracker_prep.py`, `test_task_tracker_repair.py` | adapted |
| `workflows/implement/test_task_tracker_format.py` (new) | format + commit set + restore |
| `workflows/implement/test_finalisation_format.py` (new) | format before commit |
| `workflows/review/test_handoff.py` | flush format tests |
| `workflows/review/test_core_formatter_preflight.py` | restore `handoff.format_best_effort` |
| `workflows/review/test_core_dismiss_format.py` (new) | pre-gate flush |
| `workflows/review/test_round_applied.py` (new) | `round_applied` unit + git test |
| `workflows/review/conftest.py`, `test_core.py` | `round_applied` seam |
| tests that need the real formatter (`ci_fix_drive` users) | `real_formatters` marker |

### Config and docs

- `pyproject.toml`: register the `real_formatters` marker.
- `docs/configuration/setup.md`, `docs/configuration/config.md`,
  `docs/migration/multi-language.md`, `docs/architecture/architecture.md`:
  which Linux templates run setup.
- `docs/configuration/toolkits.md`, `docs/architecture/toolkit-interface.md`,
  `docs/repository-setup/python.md`: users of the `commit` binding, the
  pre-flight list, and which workflows carry on when formatting fails.

## Steps

1. `format_best_effort` helper + autouse `formatter_mocks` fixture + marker
2. Formatter-stable `write_round_log`
3. `TASK_TRACKER_TEMPLATE` blank lines
4. Linux create-plan / review-plan templates run setup (+ template docs)
5. create-plan: formatter pre-flight and formatted plan commit
6. Task tracker preparation: format, commit the formatter's changes, restore
7. Finalisation: format before commit
8. Review: whole-tree round-log flush formats
9. Review: formatted commit before the CI gate on dismiss
10. Review: "applied" ignores review logs
11. Docs: formatting users, pre-flight list, failure behaviour

## Out of scope

- #1485 (`.mcp-coder/` session files in commits), #1486 (clean-tree skip in
  `commit_changes`), #1487 (more LLM text in the round log). Whichever lands
  second adapts.
- No markdown formatter is added to mcp-coder's own toolchain.
