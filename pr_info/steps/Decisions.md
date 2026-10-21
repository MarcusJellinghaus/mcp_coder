# Decisions

## Step 2 — obsolete `check_branch_status` import guards

Context: the Step 2 run blocked on F401 findings from
`try: from mcp_coder.cli.commands.check_branch_status import execute_check_branch_status /
except ImportError` guards in `tests/cli/commands/test_check_branch_status*.py`.

- **Remove the guards, do not `noqa` them.** Agreed in chat after the blocked status check
  ("we want to go for really clean code ... a large amount of noqa sounds a bit silly").
  The module exists, so the `except` branch is dead.
- **Also remove the `CHECK_BRANCH_STATUS_MODULE_AVAILABLE` `skipif` decorators** in all 5
  files. They would hide a broken import as silent skips.
- **Plain top-level import where the function is used; drop it where unused.**
- **Sweep the rest of `tests/` for the same first-party guard pattern** within Step 2.
- **Name `test_implement.py` and `test_create_pr.py` explicitly** instead of relying on
  the sweep. They have the same guard (`test_create_pr.py` with `except Exception` and a
  traceback print). Agreed in chat after the readiness check ("Yes").
- **Delete `unavailable_command_stub` and `test_conftest_helpers.py`.** Once the three
  stub fallbacks are gone, the helper is only exercised by its own test. Agreed in the
  same reply.
