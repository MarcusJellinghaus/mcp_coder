# Step 4 — Coordinator dispatch wiring (WORKFLOW_MAPPING + templates)

Reference: `pr_info/steps/summary.md`. Depends on Step 1 (label
`status-71:merge-conflict`/`status-72:fixing-merge-conflict` must exist)
and Step 3 (the `fix-conflict` CLI verb must exist, so the Jenkins command
this step generates actually runs). This step makes the coordinator's bot
loop dispatch `status-71` issues to Jenkins.

## Precondition check

Read `src/mcp_coder/cli/commands/coordinator/workflow_constants.py` and
confirm `WORKFLOW_MAPPING` is still a plain
`dict[str, WorkflowConfig]` literal. Read
`src/mcp_coder/cli/commands/coordinator/command_templates.py` and confirm
`WORKFLOW_TEMPLATES` is still a plain `dict[str, tuple[str, str]]` literal
built from template string constants, and that `IMPLEMENT_COMMAND_TEMPLATE`/
`IMPLEMENT_COMMAND_WINDOWS` still contain a `gh-tool set-status
status-06f:implementing-failed --from-status status-06:implementing
--force` watchdog line. If either file's shape has changed, write one line
to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/workflow_constants.py` (modify)
- `src/mcp_coder/cli/commands/coordinator/command_templates.py` (modify)
- `tests/cli/commands/coordinator/test_command_templates.py` (modify)

## WHAT

In `workflow_constants.py`, add to `WORKFLOW_MAPPING`:

```python
"status-71:merge-conflict": {
    "workflow": "fix-conflict",
    "branch_strategy": "from_issue",
    "next_label": "status-72:fixing-merge-conflict",
},
```

In `command_templates.py`, add two new template string constants
(`FIX_CONFLICT_COMMAND_TEMPLATE`, `FIX_CONFLICT_COMMAND_WINDOWS`) and
register them in `WORKFLOW_TEMPLATES["fix-conflict"] = (
FIX_CONFLICT_COMMAND_TEMPLATE, FIX_CONFLICT_COMMAND_WINDOWS)`.

## HOW

Mirror the structure of `IMPLEMENT_COMMAND_TEMPLATE`/`_WINDOWS` (checkout
`{branch_name}`, pull, tool-version check, `uv sync`, run the command,
capture RC, watchdog line, archive, exit) but drop the Claude/MCP-specific
lines (`which claude`, `--mcp-config`) since `fix-conflict` calls no LLM and
its parser doesn't accept `--mcp-config`:

```python
FIX_CONFLICT_COMMAND_TEMPLATE: str = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
uv sync --inexact --extra types
mcp-coder --log-level {log_level} fix-conflict --project-dir /workspace/repo
RC=$?
echo RC=$RC

mcp-coder gh-tool set-status status-73:merge-conflict-failed --from-status status-72:fixing-merge-conflict --project-dir /workspace/repo --force || true

echo "archive after execution ======================================="
ls -la logs

exit $RC
"""
```

Windows equivalent follows `IMPLEMENT_COMMAND_WINDOWS`'s structure (same
drops), using `%WORKSPACE%\repo`/`set RC=%ERRORLEVEL%`/`exit /b %RC%` and
the `--force` watchdog line without `|| true` (the Windows templates don't
use that suffix either, per the existing pattern).

## ALGORITHM

Not applicable — static template strings and one dict entry. The dispatch
*mechanism* (`dispatch_workflow` in `coordinator/core.py`) is unchanged; it
already looks up `WORKFLOW_MAPPING`/`WORKFLOW_TEMPLATES` generically by
workflow name.

## DATA

No new data structures — one more key in each of the two existing dicts.

## TDD order

1. In `tests/cli/commands/coordinator/test_command_templates.py`, add a
   `fix-conflict` branch to `test_templates_map_to_expected_constants`:
   `assert WORKFLOW_TEMPLATES["fix-conflict"] == (FIX_CONFLICT_COMMAND_TEMPLATE, FIX_CONFLICT_COMMAND_WINDOWS)`
   (importing those two constants at the top of the file alongside the
   others). Run the test file — it must fail (`NameError`/`ImportError`,
   the constants don't exist yet).
2. Add the two template constants and the `WORKFLOW_MAPPING`/
   `WORKFLOW_TEMPLATES` entries in the `src/` files.
3. Run the full suite. The existing generic tests
   (`test_every_mapping_workflow_has_template`,
   `test_all_templates_format_uniformly_with_all_kwargs` in
   `test_command_templates.py`, and
   `TestDispatchWorkflowSilentFallthroughGuard.test_each_workflow_dispatches_its_verb`
   in `test_core.py`) pick up the new entry automatically via iteration over
   `WORKFLOW_MAPPING`/`WORKFLOW_TEMPLATES` — no changes needed there, just
   confirm they still pass.

## Checks before commit

pylint, pytest (fast unit marker set), mypy,
`mcp__mcp-tools-py__run_format_code`. All must pass.

## Commit message

```
feat(coordinator): dispatch status-71 to fix-conflict workflow
```

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for the overall design, then implement
> `pr_info/steps/step_4.md` exactly as written. Follow TDD: add the new
> assertion to `tests/cli/commands/coordinator/test_command_templates.py`
> first and confirm it fails, then add the two template constants and the
> `WORKFLOW_MAPPING`/`WORKFLOW_TEMPLATES` entries to make it pass. Also
> confirm the existing generic/parametrized tests in that file and in
> `test_core.py` still pass without modification. If this step's
> "Precondition check" section fails, write one line to
> `pr_info/.blocked.txt` and stop. Otherwise make one commit containing all
> the changes, after formatters/pylint/pytest/mypy all pass.
