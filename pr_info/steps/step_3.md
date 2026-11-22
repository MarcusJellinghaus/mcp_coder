# Step 3 — Streaming core: error event from the `result` message, no double print

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only. Step 2
> (`build_cli_failure`) is done. Write the fixture and the tests first, then the code. Run
> pylint, pytest (`-n auto`, fast unit markers), mypy; run `run_format_code`; run
> `check_file_size`. Make one commit.

## WHERE

- `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py`: `StreamMessage` gets
  `is_api_error_message: bool`.
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py`:
  `_map_stream_message_to_event`, `ask_claude_code_cli_stream`.
- `src/mcp_coder/llm/types.py`: the `StreamEvent` docstring only (the new `reason` values).
- Create `tests/llm/providers/claude/fixtures/logged_out_stream.ndjson`, the real capture
  below, UTF-8. It is the 4 lines of block (b) from issue #33's comment, copied verbatim
  including `·` (U+00B7). No `__init__.py` is needed in `fixtures/`.
- Create `tests/llm/providers/claude/logged_out_capture.py`, a plain helper module that
  steps 4–5 reuse:
  ```python
  FIXTURE = Path(__file__).parent / "fixtures" / "logged_out_stream.ndjson"
  LOGGED_OUT_RC = 1
  LOGGED_OUT_STDERR = "<the stderr text from block (a), see below>"
  AUTH_HINT = "Run `claude`, then `/login`."
  CLI_TEXT = "Not logged in · Please run /login"
  AUTH_MESSAGE = f"{AUTH_HINT} {CLI_TEXT}"

  def load_logged_out_lines() -> list[str]:
      return FIXTURE.read_text(encoding="utf-8").splitlines()
  ```
- Create `tests/llm/providers/claude/test_claude_cli_stream_auth.py`. Copy the small
  `_make_mock_stream(lines, *, timed_out=False, return_code=0, stderr="")` helper pattern from
  `test_claude_cli_stream_parsing.py`, and use the same three `@patch` targets
  (`_find_claude_executable`, `get_stream_log_path`, `stream_subprocess` in
  `claude_code_cli_streaming`).

### Fixture content (`logged_out_stream.ndjson`, 4 lines)

```
{"type":"system","subtype":"init","cwd":"C:\\project","session_id":"<session-id>","tools":["ToolSearch","mcp__mcp-workspace__read_file","<trimmed>"],"mcp_servers":[{"name":"mcp-tools-py","status":"connected","source":"dynamic"},{"name":"mcp-workspace","status":"connected","source":"dynamic"}],"model":"claude-opus-5-5","permissionMode":"default","slash_commands":["<trimmed>"],"terminal_slash_commands":["<trimmed>"],"apiKeySource":"none","claude_code_version":"2.1.330","output_style":"default","agents":["<trimmed>"],"skills":["<trimmed>"],"plugins":["<trimmed>"],"capabilities":["<trimmed>"],"analytics_disabled":false,"product_feedback_disabled":false,"served_by_anthropic":true,"uuid":"<uuid>","original_cwd":"C:\\project","additional_directories":[],"messaging_socket_path":"<redacted>","fast_mode_state":"off","fast_mode_disabled_reason":"sdk_opt_in_required","per_turn_effort_active":true,"ultrathink_available":false,"ultrathink_typed_raises":false,"view_mode":"default","powershell_path":"<redacted>"}
{"type":"user","message":{"role":"user","content":"Reply with OK"},"session_id":"<session-id>","parent_tool_use_id":null,"uuid":"<uuid>","timestamp":"2026-11-22T10:32:45.004Z","isReplay":true}
{"type":"assistant","message":{"diagnostics":null,"id":"<uuid>","container":null,"model":"<synthetic>","role":"assistant","stop_details":null,"stop_reason":"stop_sequence","stop_sequence":"","type":"message","usage":{"output_tokens_details":null,"input_tokens":0,"output_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":null,"cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":0},"inference_geo":null,"iterations":null,"speed":null,"fallback_credit":null},"content":[{"type":"text","text":"Not logged in · Please run /login"}],"context_management":null},"parent_tool_use_id":null,"session_id":"<session-id>","uuid":"<uuid>","timestamp":"2026-11-22T10:32:47.705Z","error":"authentication_failed","is_api_error_message":true}
{"duration_api_ms":0,"stop_reason":"stop_sequence","session_id":"<session-id>","total_cost_usd":0,"usage":{"output_tokens_details":{"thinking_tokens":0},"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":0,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":0},"inference_geo":"","iterations":[],"speed":"standard","fallback_credit":null},"modelUsage":{},"permission_denials":[],"terminal_reason":"api_error","fast_mode_state":"off","fast_mode_disabled_reason":"sdk_opt_in_required","subagent_stats":{"spawned":0,"requested":{"background":0,"foreground":0,"unset":0},"started_in_background":0,"max_depth":0,"spawned_by_subagents":0,"completed":0,"failed":0,"killed":{"parent":0,"user":0,"system":0},"refused":{"depth_limit":0,"concurrency_limit":0,"budget":0},"by_type":{}},"safety_stops":0,"is_error":true,"num_turns":1,"subtype":"success","api_error_status":null,"result":"Not logged in · Please run /login","type":"result","duration_ms":2729,"uuid":"<uuid>","queued_turn_count":0,"result_index":0,"model_usage_since_last_result":{}}
```

### `LOGGED_OUT_STDERR` (from block (a), representative unrelated stderr)

```
Ignoring 78 permissions.allow entries from .claude/settings.local.json: this workspace has not been trusted. Run Claude Code interactively here once and accept the trust dialog, or set projects["C:/project"].hasTrustDialogAccepted: true in C:\project\.scratch\claude_empty_config\.claude.json.
```

If the fixture can't be written byte-exact as UTF-8 (the `·` must survive), write one line
to `pr_info/.blocked.txt` and stop.

## WHAT

- `_map_stream_message_to_event(msg)`: for `assistant` messages with
  `msg.get("is_api_error_message")`, skip `text` blocks (no `text_delta`); other block types
  are unchanged. `result` messages still yield exactly one `done` event, unchanged.
- `ask_claude_code_cli_stream(...)`: same signature. Inside the loop, remember the last
  `result` message. After the loop, yield at most one error event.

## ALGORITHM

```
result_msg: StreamMessage | None = None
... in loop, after parse:  if msg.get("type") == "result": result_msg = msg
cmd_result = stream.result
if cmd_result.timed_out: yield <inactivity_timeout event>   # unchanged, takes precedence
else:
    is_error = bool(result_msg and result_msg.get("is_error"))
    if cmd_result.return_code != 0 or is_error:
        message, reason = build_cli_failure(result_msg.get("result") if result_msg else None,
                                            is_error, result_msg.get("subtype") if result_msg else None,
                                            cmd_result.stderr or "", cmd_result.return_code)
        yield {"type": "error", "reason": reason, "return_code": cmd_result.return_code, "message": message}
```

## DATA

- Error event: `{"type": "error", "reason": "auth" | "result_error" | "nonzero_exit", "return_code": int, "message": str}`.
  The inactivity-timeout event is unchanged.
- Docstrings: update the Yields section of `ask_claude_code_cli_stream`, and add the
  `reason` values `auth` / `result_error` to the `StreamEvent` docstring in `types.py`.

## Tests (first) — `test_claude_cli_stream_auth.py`

- Fixture with rc=`LOGGED_OUT_RC`, stderr=`LOGGED_OUT_STDERR`:
  - exactly one error event, `reason == "auth"`, `message == AUTH_MESSAGE`
  - the hint comes first and appears once
  - the message has no stderr text and no newline
- Same run: no `text_delta` event carries `CLI_TEXT`; one `done` event is still emitted.
- An assistant block **without** the flag still yields `text_delta` (no regression).
- A non-auth `is_error` result (e.g. `result: "Something broke"`, rc=1, stderr `"boom"`) →
  `reason == "nonzero_exit"`, `message == "Something broke; stderr: boom"`.
- Exit 0 + `is_error` (fixture lines with the result text replaced by `"Something broke"`, rc=0) →
  `reason == "result_error"`.
- `is_error` with empty result text and `subtype: "success"` → message
  `"CLI reported an error"`, never containing `"code 0"`.
- Timeout precedence: `timed_out=True` plus an `is_error` result → only the
  `inactivity_timeout` event.
- Exit 0 without `is_error` → no error event.
- Existing `test_claude_cli_stream_parsing.py` stderr tests stay green unchanged.
