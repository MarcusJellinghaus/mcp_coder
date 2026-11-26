# Step 4: Linux create-plan and review-plan templates run `mcp-coder setup`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`.
> Write the tests first, then the code and the doc edits. Run pylint, mypy and
> the fast pytest set (`-n auto`). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `tests/cli/commands/coordinator/test_command_templates_setup.py`
- `tests/cli/commands/coordinator/test_command_templates.py`, only if an
  assertion there breaks (`test_create_plan_templates_pass_issue_number` must
  keep passing unchanged)
- Docs: `docs/configuration/setup.md` (lines ~16-18),
  `docs/configuration/config.md` (~962), `docs/migration/multi-language.md`
  (~34), `docs/architecture/architecture.md` (~130)

## WHAT

```python
def _watchdog(failed: str, current: str, *, issue_flag: bool = False) -> str: ...

def _linux_setup_template(
    command: str, failed: str, current: str, *,
    checkout: str = "{branch_name}",
    issue_flag: bool = False,
    archive_plan_sessions: bool = True,
) -> str: ...

CREATE_PLAN_COMMAND_TEMPLATE = _linux_setup_template(
    "create-plan {issue_number}", "status-03f:planning-failed", "status-03:planning",
    checkout="main", issue_flag=True,
)
REVIEW_PLAN_COMMAND_TEMPLATE = _linux_setup_template(
    "review-plan", "status-14f:plan-review-failed", "status-14i:plan-reviewing",
)
```

## HOW

- `_watchdog` inserts `" --issue {issue_number}"` (a plain string with single
  braces) between `--from-status {current}` and `--project-dir`. That gives
  exactly the current create-plan watchdog line:
  `mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --project-dir /workspace/repo --force || true`.
- `_linux_setup_template` emits `f"git checkout {checkout}\n"`. The default
  value `"{branch_name}"` stays a single-brace `str.format` placeholder.
- Update the `_linux_setup_template` docstring: the setup and venv lines
  contain no `$`, braces or backticks. The watchdog's only braces are the
  `{issue_number}` placeholder, which is filled before bash sees the script.
- Header comment, step 2: replace the list of four workflows with "every
  workflow except create-pr, then run `mcp-coder setup`".
- Docs:
  - `setup.md` and `config.md`: name all six Linux workflows that run setup
    (create-plan, implement, review-plan, review-implementation, fix-ci,
    fix-conflict). Linux create-pr and the test template do not.
  - `multi-language.md`: same list.
  - `architecture.md` line ~130: "on Linux for every workflow except create-pr,
    on Windows for every workflow".
  - `setup.md`: note that Linux create-plan runs setup on `main`, before the
    plan branch is checked out.

## ALGORITHM

```
issue = " --issue {issue_number}" if issue_flag else ""
watchdog = f"mcp-coder gh-tool set-status {failed} --from-status {current}{issue} --project-dir /workspace/repo --force || true"
template = f"git checkout {checkout}\n" + "git pull\n" + setup block(watchdog) + ... (rest unchanged)
```

## DATA

Template strings; the dispatch table `WORKFLOW_TEMPLATES` is unchanged.

## Tests first (`test_command_templates_setup.py`)

- Change `SETUP_CASES` to `(template, command, checkout, watchdog)` and add:
  - create-plan: command `"create-plan {issue_number}"`, checkout `"main"`,
    watchdog with `--issue {issue_number}`;
  - review-plan: command `"review-plan"`, checkout `"{branch_name}"`, watchdog
    without `--issue`.
  - The existing four keep their values; checkout is `"{branch_name}"`.
- Tests in the parametrised class:
  - `test_failure_block_runs_watchdog_and_exits` compares with the case's
    `watchdog`.
  - `test_watchdog_appears_twice` counts the case's `watchdog`.
  - `test_formats` formats with `log_level="info", branch_name="b",
    issue_number=1`. It asserts `git checkout <b or main>` and
    `mcp-coder --log-level info {command.format(issue_number=1)} `.
  - `test_new_lines_have_no_expansion_characters`: the setup, `exit 1`, `fi`
    and venv lines have no `$`, braces or backticks. The watchdog line has no
    `$` or backticks, and no braces once `{issue_number}` is removed.
  - Update the class docstring: six templates.
- `test_other_templates_do_not_run_setup`: only `CREATE_PR_COMMAND_TEMPLATE`
  and `DEFAULT_TEST_COMMAND`.

## Commit

`feat(coordinator): run mcp-coder setup in the Linux create-plan and review-plan templates`
