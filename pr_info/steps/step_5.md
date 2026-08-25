# Step 5 — Drop `exc_info=True` at both coordinator sites

Read [summary.md](summary.md) first.

Small and independent of steps 3-4, but only *useful* after step 4: a clean message alone does not
remove the HTML from the console while `exc_info=True` renders the chained cause.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/commands.py` (modify, two lines)
- `tests/cli/commands/coordinator/test_commands.py` (modify)

## WHAT

Both sites lose `exc_info=True`. Nothing else about either handler changes.

`execute_coordinator_test` (`commands.py:156-161`) — fires one Jenkins build of the executor job
running an environment smoke test; touches no GitHub issues and changes no labels. It is the
documented first-run / new-repo setup command, i.e. exactly the command an operator runs while
configuring Jenkins. It logs **and re-raises**, so it printed the HTML more times than `run` did:

```python
except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
    # Let all other exceptions bubble up; main.py's top-level boundary logs the traceback.
    logger.error(f"Unexpected error: {e}")
    raise
```

`execute_coordinator_run` (`commands.py:323-331`) — the per-issue handler. Fail-fast by design:
log and `return 1`, aborting the run and any remaining repos under `--all`:

```python
except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
    # Fail-fast: log error and exit immediately
    logger.error(f"Failed processing issue #{issue['number']}: {e}")
    return 1
```

## HOW

Leave **`main.py:377` alone.** It is a top-level `except Exception ... exc_info=True` CLI error
boundary; dropping `exc_info` there would degrade debugging for every unrelated failure.
Consequence, and it is intended: after this step `--dry-run` still emits two tracebacks
(`commands.py:161` re-raises into it) and `run` emits one.

Do **not** add an `except JenkinsError` branch to either function. The full remedy is already in
the exception message from step 4; a coordinator-level branch would need a new import plus a
handler in two independent functions plus a shared helper to avoid duplicating the text.

Update the `execute_coordinator_test` comment: "Let all other exceptions bubble up with full
traceback" is no longer accurate at that site — the traceback now comes from `main.py`'s boundary.

## ALGORITHM / DATA

N/A — two deletions.

## TESTS (write first)

`tests/cli/commands/coordinator/test_commands.py` already has `TestExecuteCoordinatorTest`
(`:52`) with the mocking scaffolding for `create_default_config`, config loading and
`JenkinsClient` — reuse it rather than building new fixtures.

1. `test_coordinator_test_error_logged_without_traceback` — make `client.start_job` raise, wrap in
   `pytest.raises` (this path re-raises), then assert every `caplog.records` entry emitted by
   `mcp_coder.cli.commands.coordinator.commands` has `record.exc_info is None`.
2. `test_coordinator_run_error_logged_without_traceback` — make `dispatch_workflow` raise, assert
   the return value is `1` (fail-fast) and that the handler's record has `record.exc_info is None`.

Assert on `record.exc_info`, not on formatted output — `caplog.text` does not always render
`exc_info`, so a text assertion can pass against the unfixed code.

Both tests should use a `JenkinsError` with a realistic multi-line step-4 message as the raised
exception, so they double as a check that the remedy text reaches the console intact.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Step 4 must be committed first.
>
> Implement step 5 test-first: add the two `record.exc_info is None` tests to
> `tests/cli/commands/coordinator/test_commands.py`, reusing the existing
> `TestExecuteCoordinatorTest` scaffolding at `:52`; watch them fail; then drop `exc_info=True` at
> `commands.py:160` and `commands.py:329` and correct the now-stale comment at the first site.
>
> Assert on `record.exc_info`, not on `caplog.text`.
>
> Do not touch `main.py:377` — it is the top-level CLI error boundary and stays as it is. Do not
> add an `except JenkinsError` branch.
>
> Run, with MCP tools only: `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
> Fix everything they report, then `./tools/format_all.sh` and commit as one commit.
