# Step 1: Log the WORKFLOW FAILED banner at ERROR

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #738).

This is a single, self-contained commit: test hardening + implementation + checks passing.

## Goal

Align the shared failure banner's log level with its severity. The six banner lines
become `ERROR`; the one fallback that aborts the handler (`IssueManager` creation)
becomes `ERROR`; the three fallbacks that let the handler continue stay `WARNING`.

## TDD order

Write the test assertion first (it fails because the banner is currently `INFO`),
then apply the source change (it passes), then run the checks.

---

## WHERE

- **Test:** `tests/workflow_utils/test_failure_handling.py`
  — method `TestHandleWorkflowFailure.test_logs_failure_banner`
- **Source:** `src/mcp_coder/workflow_utils/failure_handling.py`
  — function `handle_workflow_failure(...)`

## WHAT

No signatures change. Edits are log-level swaps only.

**Source — `handle_workflow_failure()`:**
- The six banner calls (step "1. Log failure banner"):
  `logger.info(...)` → `logger.error(...)` for all six lines
  (`"=" * 60`, `"WORKFLOW FAILED"`, `"Category: %s"`, `"Stage: %s"`,
  `"Error: %s"`, `"=" * 60`). Keep six separate calls — do **not** merge into one.
- The `IssueManager` creation fallback (step "3."):
  `logger.warning("Failed to create IssueManager: %s", exc)` → `logger.error(...)`.
- Leave unchanged as `logger.warning`:
  `"Failed to extract issue number from branch: %s"`,
  `"Failed to update issue label: %s"`,
  `"Failed to post failure comment: %s"`.

**Test — `test_logs_failure_banner`:**
- Add `import logging` at the top of the test module (if not already present).
- Keep the existing text assertions and the `INFO` capture level.
- Add a level assertion on the banner record.

**Test — new test for the `IssueManager`-creation fallback (ERROR level):**
- The `IssueManager` creation fallback changes from `logger.warning` to
  `logger.error` because that branch aborts the handler via an early `return`.
  There is currently NO test exercising that failure path, so the level change
  would ship unverified. Add an explicit test for it.
- In `tests/workflow_utils/test_failure_handling.py`, add a test (e.g.
  `test_issue_manager_creation_failure_logs_error`) that patches
  `IssueManager(project_dir)` to raise, invokes `handle_workflow_failure(...)`,
  and asserts the corresponding log record is at `ERROR`. Find the record whose
  message contains `"Failed to create IssueManager"` and assert
  `record.levelno == logging.ERROR`.

## HOW

- Imports: add `import logging` to the test module. No new imports in the source file
  (`logging` and `logger` already exist).
- No decorators, no config, no wiring changes.

## ALGORITHM

Test assertion (added to `test_logs_failure_banner`, after the existing text asserts):

```
banner = next(
    r for r in caplog.records if "WORKFLOW FAILED" in r.getMessage()
)
assert banner.levelno == logging.ERROR
```

New test for the `IssueManager`-creation fallback (patch `IssueManager` to raise,
then assert the fallback record is logged at `ERROR`):

```
record = next(
    r for r in caplog.records if "Failed to create IssueManager" in r.getMessage()
)
assert record.levelno == logging.ERROR
```

Source: mechanical replacement — swap the log method name on the seven lines listed
above; message strings and `%s` args are untouched.

## DATA

- No return-value or data-structure changes. `handle_workflow_failure()` still
  returns `None`.
- Exit codes untouched (out of scope — see summary).
- Test reads `caplog.records` (list of `logging.LogRecord`); asserts
  `record.levelno == logging.ERROR` (int `40`).

## Verification / checks (must pass before commit)

- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with (per CLAUDE.md, `-n auto` for parallel execution)
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_format_code` before committing.

## Commit

One commit containing the source change + the hardened test, e.g.:

```
Fix: log WORKFLOW FAILED banner at ERROR instead of INFO (#738)
```
