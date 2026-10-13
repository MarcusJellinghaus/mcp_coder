# Step 2 — execute_coordinator_test(): add LABEL

See [summary.md](./summary.md) for context and the overall design.

Depends on Step 1 being committed first (same files, no functional overlap).

Precondition: `execute_coordinator_test()` in `commands.py` must still build
its Jenkins `params` dict in one place, from `validated_config`,
`args.branch_name`, and `test_command`. If it does not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/commands.py` —
  `execute_coordinator_test()`
- `tests/cli/commands/coordinator/test_commands.py` —
  `TestExecuteCoordinatorTest::test_execute_coordinator_test_success`

## WHAT

No signature changes — `execute_coordinator_test(args: argparse.Namespace) ->
int` is unchanged. Only its `params` dict gains one key.

## HOW

No new imports. `args.repo_name` and `args.branch_name` are already in
scope at the point `params` is built.

## ALGORITHM

In the existing `params = {...}` dict inside `execute_coordinator_test()`,
add:

```python
"LABEL": f"{args.repo_name} - {args.branch_name} - test",
```

## DATA

`params` gains one key:

```python
{
    "REPO_URL": ...,
    "BRANCH_NAME": ...,
    "COMMAND": ...,
    "GITHUB_CREDENTIALS_ID": ...,
    "LABEL": "mcp_coder - feature-x - test",
}
```

## Tests (write/update first, TDD)

In `tests/cli/commands/coordinator/test_commands.py`, in
`test_execute_coordinator_test_success`, add
`"LABEL": "mcp_coder - feature-x - test"` to the expected `params` dict in
the `mock_client.start_job.assert_called_once_with(...)` call (matches this
test's `args.repo_name="mcp_coder"` / `args.branch_name="feature-x"`).

## Checks

Run pylint, pytest (unit marker set from CLAUDE.md), and mypy. All must
pass before committing.

## Commit

One commit: the test update + the `commands.py` change together.

---

## LLM prompt for this step

```
Implement Step 2 of pr_info/steps/summary.md, described in
pr_info/steps/step_2.md.

Follow TDD: update the listed test first (it should fail), then make the
implementation change in commands.py so it passes. Run pylint, pytest, and
mypy; fix anything they flag. Then create exactly one commit containing the
test and implementation changes together.
```
