# Step 2 — Rewrite `ask_claude_code_cli` as the retry-free drain-wrapper

**Reference:** See [summary.md](./summary.md) (Architectural changes 1, 3, 4). This is the core
unification. After this step the blocking path runs entirely through the streaming core; its
`raw_response` becomes the `events` shape and its timeout becomes **inactivity**. Depends on Step 1.

## WHERE
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — rewrite `ask_claude_code_cli`; delete
  `create_response_dict_from_stream` and now-dead code/imports.
- `docs/architecture/architecture.md` — LLM section: one streaming core.
- Tests: `tests/llm/providers/claude/test_claude_code_cli.py`, `test_claude_cli_wrappers.py`,
  `test_claude_code_cli_heartbeat.py`, `tests/llm/test_interface.py`,
  `tests/cli/commands/test_prompt.py`.

## WHAT
Signature unchanged:
```
def ask_claude_code_cli(question, session_id=None, timeout=30, env_vars=None, cwd=None,
    mcp_config=None, settings_file=None, logs_dir=None, branch_name=None,
    append_system_prompt=None, system_prompt_replace=None) -> LLMResponseDict
```
Removed: `create_response_dict_from_stream`, `LLM_HEARTBEAT_INTERVAL_SECONDS`, the inline MCP guard,
`parse_stream_json_string` usage, `execute_subprocess` usage, the write-once file dump. Update
`__all__` accordingly.

## HOW
- Import and call `ask_claude_code_cli_stream` (lazy import to avoid a cycle if needed) and
  `ResponseAssembler`.
- Keep `log_llm_request` / `log_llm_response` / `log_llm_error` calls (side-effect parity).
- Keep raising `TimeoutExpired` and `CalledProcessError`; keep letting `McpServersUnavailableError`
  propagate — `interface.py`'s existing `except TimeoutExpired → LLMTimeoutError` map is reused
  unchanged. MLflow wrapping stays at the `prompt_llm` level (untouched).
- The incremental per-line NDJSON flush now comes from the streaming core (no extra work).

## ALGORITHM
```
log_llm_request(...); start = time(); assembler = ResponseAssembler("claude")
last_error, done, stream_file = None, None, None
try:
    for ev in ask_claude_code_cli_stream(question, ..., timeout=timeout, ...):
        assembler.add(ev)
        t = ev.get("type")
        if t == "stream_file": stream_file = ev.get("path")
        elif t == "done":      done = ev
        elif t == "error":     last_error = ev
except McpServersUnavailableError as e:
    log_llm_error(e, duration_ms); raise
if last_error and last_error.get("reason") == "inactivity_timeout":
    err = TimeoutExpired(command_or_cmd, timeout); log_llm_error(err, ...); raise err
if last_error:  # nonzero_exit
    err = CalledProcessError(rc, cmd, output="", stderr=f"...Stream file: {stream_file}")
    log_llm_error(err, ...); raise err
log_llm_response(duration_ms, session_id=result["session_id"],
                 cost_usd=done.get("cost_usd") if done else None,
                 usage=done.get("usage") if done else None)
return assembler.result()
```

## DATA
- Returns `LLMResponseDict` with `raw_response = {"events": [...], "stream_file": str, "usage"?: ...}`.
- `text` top-level (unchanged consumers); `session_id` top-level (from assembler).
- `prompt --json` output's nested `raw_response` now shows `events` (Decision 11) — top-level
  `text`/`session_id` unchanged.

## TESTS (write first / migrate)
- Blocking success returns `events`-shaped `raw_response` with `stream_file`; `text`/`session_id`
  correct. Rewrite assertions that expected `raw_response["messages"]`.
- Inactivity → `TimeoutExpired`; through `prompt_llm` → `LLMTimeoutError`.
- Nonzero exit → `CalledProcessError` carrying the stream-file path.
- `McpServersUnavailableError` propagates and `log_llm_error` is called once.
- `log_llm_request`/`log_llm_response` still invoked. Update/remove the heartbeat test (no more
  heartbeat on the blocking path). Update `test_prompt.py` `--json` shape expectation.

## LLM PROMPT
> Implement Step 2 from `pr_info/steps/step_2.md` (see `pr_info/steps/summary.md`). Rewrite
> `ask_claude_code_cli` in `claude_code_cli.py` as a retry-free drain-wrapper over
> `ask_claude_code_cli_stream` + `ResponseAssembler`: preserve `log_llm_request/response/error`,
> re-raise `TimeoutExpired` on the `reason=="inactivity_timeout"` event, raise `CalledProcessError`
> on `nonzero_exit`, and let `McpServersUnavailableError` propagate. Delete
> `create_response_dict_from_stream`, the duplicated MCP guard, the heartbeat constant, and the
> now-dead `execute_subprocess`/parse/file-write code; update `__all__` and imports. Migrate the
> affected tests (blocking now returns the `events` shape with `stream_file`; `--json` shifts
> `messages`→`events`; heartbeat test removed). Update `docs/architecture/architecture.md`. TDD,
> pylint/pytest(`-n auto`)/mypy green, one commit.
