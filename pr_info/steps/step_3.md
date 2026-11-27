# Step 3 — Linux workflow templates list all sessions

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly
> (steps 1 and 2 are already committed). Write the test first, then change
> `_linux_setup_template` and `CREATE_PR_COMMAND_TEMPLATE`. Run pylint, pytest (fast unit set)
> and mypy; all must pass. Run `run_format_code`, then commit only the files listed under
> WHERE in one commit.

## WHERE

- `tests/cli/commands/coordinator/test_command_templates_setup.py`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`

## WHAT

### Tests: `test_command_templates_setup.py`

Replace `test_linux_fix_conflict_does_not_list_plan_sessions` (added in step 1) with:

```python
LINUX_WORKFLOWS = [
    pytest.param(param.values[0], id=param.id) for param in SETUP_CASES
] + [pytest.param(CREATE_PR_COMMAND_TEMPLATE, id="create-pr")]


@pytest.mark.parametrize("template", LINUX_WORKFLOWS)
def test_linux_workflow_lists_sessions(template: str) -> None:
    """Linux workflows list all of .mcp-coder and logs without failing under set -e."""
```

ALGORITHM:
```
lines = template.splitlines()
assert "ls -laR .mcp-coder || true" in lines
assert "ls -la logs || true" in lines
assert "create_plan_sessions" not in template
```

### Implementation: `command_templates.py`

- `_linux_setup_template`: remove the `archive_plan_sessions` parameter and the `plan_sessions`
  variable. The archive section becomes:
  ```python
  'echo "archive after execution ======================================="\n'
  "ls -laR .mcp-coder || true\n"
  "ls -la logs || true\n"
  ```
  Docstring: extend the `set -e` sentence. The listings end in `|| true`, so a missing folder
  cannot abort the script before `exit $RC`.
- `CREATE_PR_COMMAND_TEMPLATE` literal: replace `ls -la .mcp-coder/create_plan_sessions` and
  `ls -la logs` with `ls -laR .mcp-coder || true` and `ls -la logs || true`.
- `FIX_CONFLICT_COMMAND_TEMPLATE`: remove `archive_plan_sessions=False`.
- Leave `DEFAULT_TEST_COMMAND` untouched.

New signature:
```python
def _linux_setup_template(
    command: str,
    failed: str,
    current: str,
    *,
    checkout: str = "{branch_name}",
    issue_flag: bool = False,
) -> str:
```

## HOW

No new imports. Nothing else calls `archive_plan_sessions`. After this step a search for it in
`src/` and `tests/` must return nothing.

## DATA

Template constants stay `str`.

## Done when

- `create_plan_sessions` appears in `command_templates.py` only inside `DEFAULT_TEST_COMMAND`
  and `DEFAULT_TEST_COMMAND_WINDOWS`.
- `archive_plan_sessions` appears nowhere.
- pylint, mypy and pytest pass.
