# Summary — Claude provider: surface "Please run /login" auth failures (#33)

## Goal

When the Claude CLI is logged out or its OAuth token has expired, `mcp-coder prompt`,
`mcp-coder verify` and the workflows must show the CLI's own error text, prefixed once by
the hint ``Run `claude`, then `/login`.``. The failure is typed as `LLMAuthError`, and
every workflow stops on it at once.

Scope: Claude provider only. Copilot (#1441), the other display boundaries and
ERROR-level logging (#1097), and retry policy (#1353) are out of scope.

## Ground truth: the logged-out capture

Issue comment #issuecomment-7077904725 (claude_code_version 2.1.330):

- Stream-json emits the auth text twice:
  - as an assistant text block flagged `"is_api_error_message": true`
  - as the final `result` message: `is_error: true`, `subtype: "success"`,
    `result: "Not logged in · Please run /login"`
- Exit code 1. stderr carries an unrelated trust warning.
- The MCP servers are `connected`, so the MCP guard does not mask the auth error.

Step 3 commits block (b) of that comment as the fixture
`tests/llm/providers/claude/fixtures/logged_out_stream.ndjson`.

## Architectural / design changes

1. **One shared auth type.** `LLMAuthError(Exception)` moves to `llm/types.py`, which stays
   stdlib-only. It is re-exported from `llm/interface.py` and from
   `llm/providers/langchain/_exceptions.py` (`from mcp_coder.llm.types import LLMAuthError as LLMAuthError`).
   Claude and langchain auth failures are therefore the same class. `.importlinter` gets
   the `_exceptions -> mcp_coder.llm.types` ignore entry, matching `_usage`.
   - It is plain `Exception`, not `OSError`/`TimeoutError`/`CalledProcessError`: verify
     would route those through `classify_connection_error`, and the langchain branch of
     `prompt_llm` converts `TimeoutError`.
2. **A pure failure-message builder** `llm/providers/claude/claude_cli_failure.py`.
   - One public function: `build_cli_failure(...) -> (message, reason)`. The hint and the
     auth patterns are private.
   - It is the only place that matches auth patterns and adds the hint. Every output
     (streaming, `json`, verify, workflows) shows the hint because every other layer reuses
     this message.
   - #1353 can add its classifier here later.
3. **The streaming core emits one error event after the loop.**
   - Trigger: a non-zero exit **or** `is_error: true` on the `result` message.
   - `reason` is `auth` | `result_error` (exit 0 with `is_error`) | `nonzero_exit`.
     `inactivity_timeout` keeps precedence.
   - Assistant blocks flagged `is_api_error_message` no longer yield `text_delta`, so the
     text is not printed twice.
   - Behaviour change: exit 0 + `is_error` is now a failure, where today it returns the
     error text as the response.
4. **Exception mapping** in `ask_claude_code_cli`.
   - `reason == "auth"` → `LLMAuthError(<event message>)`, with no stream-file suffix. The
     stream-file path goes in a DEBUG line.
   - Other failures stay `CalledProcessError`, with the return code clamped to at least 1.
5. **Display boundaries.** The `prompt.py` exception boundary and verify's "Test prompt" row
   use `summarize_exception(e)`.
6. **Workflow fail-fast.**
   - `llm_failure_reason` maps `LLMAuthError` → `"auth"`.
   - Every lane adds an "Auth" category display. Labels are unchanged: auth uses each
     lane's general label (fix-ci: `pr_ci_failed`).
   - The new auth branches use `exception_summary(e)` as their error text. Timeout/MCP text
     is unchanged.
   - KISS pattern: `LLMAuthError` joins the **existing** `(LLMTimeoutError, McpServersUnavailableError)`
     `except` tuples. Each site only picks its message text with `exception_summary(e) if reason == "auth" else <old text>`.
     The one new `except` block is `_run_ci_fix`'s `except LLMAuthError: raise`, a narrow
     exception to "Decision 10".
   - Implement routing:
     - task call → `fail`
     - per-task fix turn → `abort_checks` (rescue commit)

     Both go through one `auth` branch using `task_fail`.
     - final check → `abort_checks`
     - finalisation and CI → `fail("auth", …)`
7. **Not fail-fast on purpose:** commit-message generation (it has a static fallback) and
   fix-ci's `refresh_pr_description` (best-effort). The next real LLM call stops the run.

### Message formats (built by `build_cli_failure`)

| Case | Message | reason |
|------|---------|--------|
| auth pattern in failure text | ``Run `claude`, then `/login`. <failure text>`` (one line, no stderr suffix) | `auth` |
| `is_error`, non-empty result text | `<result text>` + `; stderr: <stderr[:500]>` if stderr | `nonzero_exit` / `result_error` |
| `is_error`, empty result text | `CLI reported an error` + ` (subtype: X)` unless X is None/`"success"` + `: <stderr[:500]>` if stderr | `nonzero_exit` / `result_error` |
| non-zero exit, no `is_error` | `CLI failed with code N` + `: <stderr[:500]>` if stderr (unchanged) | `nonzero_exit` |

- The failure text is the `is_error` result text when non-empty; otherwise the full stderr.
- The auth patterns match case-insensitively: `Not logged in`, `Please run /login`,
  `authentication_error`, `OAuth token has expired`, `Invalid API key`.
- They are never matched against assistant text.

## Files

### Created
- `src/mcp_coder/llm/providers/claude/claude_cli_failure.py` — pure message builder (step 2)
- `tests/llm/providers/claude/test_claude_cli_failure.py` (step 2)
- `tests/llm/providers/claude/fixtures/logged_out_stream.ndjson` — real capture (step 3)
- `tests/llm/providers/claude/logged_out_capture.py` — fixture loader + capture constants (step 3)
- `tests/llm/providers/claude/test_claude_cli_stream_auth.py` (step 3)
- `tests/llm/providers/claude/test_claude_cli_auth_errors.py` (step 4)
- `tests/cli/commands/test_auth_error_display.py` (step 5)
- `tests/workflow_utils/test_failure_reason_auth.py` (step 6)
- `tests/workflows/implement/test_core_auth.py` (steps 7–8)
- `tests/workflow_steps/test_ci_auth.py` (step 9)

### Modified
- `src/mcp_coder/llm/types.py`, `src/mcp_coder/llm/interface.py`,
  `src/mcp_coder/llm/providers/langchain/_exceptions.py`, `.importlinter` (step 1)
- `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py` (`StreamMessage` field),
  `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` (step 3)
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py` (step 4)
- `src/mcp_coder/cli/commands/prompt.py`, `src/mcp_coder/cli/commands/verify.py` (step 5)
- `src/mcp_coder/workflow_utils/failure_handling.py`,
  `src/mcp_coder/workflows/create_plan/core.py`, `src/mcp_coder/workflows/review/handoff.py` (step 6)
- `src/mcp_coder/workflows/implement/failure_reporting.py`, `.../implement/check_loop.py`,
  `.../implement/task_processing.py`, `.../implement/core.py` (step 7)
- `src/mcp_coder/workflows/implement/core.py` (step 8)
- `src/mcp_coder/workflow_steps/ci.py`, `src/mcp_coder/workflows/fix_ci/core.py`,
  `src/mcp_coder/workflows/review/steps.py` and `review/core.py` (docstring/comment only) (step 9)
- Small additions to existing test files where they stay under the 750-line gate, as named
  in each step.

## Steps

1. Shared `LLMAuthError` type
2. Pure failure-message builder
3. Streaming core: error event from the `result` message, no double print, fixture
4. `ask_claude_code_cli` raises `LLMAuthError`; clamp the return code
5. Display: `prompt.py` and verify use `summarize_exception`
6. `llm_failure_reason` → `auth`; create-plan `.get`; review "Auth" category
7. Implement: task call, fix turn, final check
8. Implement: finalisation and CI
9. Shared CI step re-raises auth; fix-ci catches it; review CI gate

Steps 6–8 land before step 9: once `ci.py` re-raises auth, every caller already handles it.

## Constraints for every step

- TDD: write the step's tests first, then the code.
- Run the pylint, pytest (`-n auto`, fast unit markers), mypy and lint-imports checks, then
  `run_format_code`. Run `check_file_size` (750 lines, source **and** tests).
- Make exactly one commit per step.
- Assert individual keys on stream events, never exact dict equality.
- Read the fixture with `encoding="utf-8"` and split it with `splitlines()` (Windows CRLF).
- Any blocked precondition: write one line to `pr_info/.blocked.txt` and stop.
