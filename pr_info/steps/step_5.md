# Step 5 — Display: `prompt.py` and verify use `summarize_exception`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` only. Steps 1–4
> are done. Write the tests first, then the code. Run pylint, pytest (`-n auto`, fast unit
> markers), mypy; run `run_format_code`; run `check_file_size`. Make one commit.

## WHERE

- `src/mcp_coder/cli/commands/prompt.py`: the top-level `except Exception as e` boundary at
  the end of `execute_prompt`.
- `src/mcp_coder/cli/commands/verify.py`: the "Test prompt" `except` (the non-`OSError`
  branch that builds `category`).
- Create `tests/cli/commands/test_auth_error_display.py`. Follow the `argparse.Namespace`
  patterns in `tests/cli/commands/test_prompt.py` and the `execute_verify` patch stack in
  `tests/cli/commands/test_verify_orchestration.py` (`_make_args`, `_claude_ok`, `_mlflow_not_installed`).

## WHAT

```python
# prompt.py
from ...llm.error_summary import summarize_exception
...
except Exception as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
    logger.error("Prompt command failed: %s", summarize_exception(e))
    return 1

# verify.py (else-branch only; the OSError/ConnectionError branch is unchanged)
from ...llm.error_summary import summarize_exception
...
else:
    category = summarize_exception(exc)
```

- The streaming (`rendered`/`text`/`ndjson`) path of `prompt.py` needs no change: it
  already prints the error event message, which carries the hint since step 3.

## DATA

- Verify row: `FAILED (LLMAuthError: Run `claude`, then `/login`. Not logged in · Please run /login)`,
  on one line.
- The `prompt` log line: `Prompt command failed: LLMAuthError: Run ...`.
- Non-auth `CalledProcessError` now shows its stderr detail, including the
  `Stream file: …` suffix. This is accepted.

## Tests (first)

- **prompt, rendered:** build the event list by running the real `ask_claude_code_cli_stream`
  on the fixture (`load_logged_out_lines()`, rc 1, `LOGGED_OUT_STDERR`; patch
  `stream_subprocess`, `_find_claude_executable`, `get_stream_log_path` in
  `claude_code_cli_streaming`). Patch `mcp_coder.cli.commands.prompt.prompt_llm_stream` to
  return `iter(events)` and run `execute_prompt` with the default (`rendered`) format.
  - Return code 1.
  - In `capsys` stdout+stderr combined, `CLI_TEXT` appears exactly once and `AUTH_HINT`
    appears exactly once.
- **prompt, json:** patch `mcp_coder.cli.commands.prompt.prompt_llm` with
  `side_effect=LLMAuthError(AUTH_MESSAGE)` and `output_format="json"`. The `caplog` ERROR
  record contains `"LLMAuthError: "` and `CLI_TEXT`, and the hint appears once.
- **prompt, CalledProcessError:** with `side_effect=CalledProcessError(1, ["claude","-p"], stderr="real cause Stream file: x")`,
  the log contains `"real cause"`.
- **verify:** patch `prompt_llm` with `side_effect=LLMAuthError(AUTH_MESSAGE)`. The output
  has one "Test prompt" line containing `CLI_TEXT`, and `AUTH_HINT` appears exactly once in
  that line.
- Existing verify/prompt tests stay green. Adjust only assertions that relied on the old
  `f"{type(exc).__name__}: {exc}"` text for `CalledProcessError`.
