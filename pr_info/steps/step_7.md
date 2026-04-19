# Step 7: Interface integration

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 7 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Wire the Copilot provider into `src/mcp_coder/llm/interface.py` by adding a `"copilot"` branch in both `prompt_llm()` and `prompt_llm_stream()`. Update the provider validation to use `SUPPORTED_PROVIDERS`. Handle system prompt (prepend to question, skip on resume) and project prompt (skip — Copilot reads CLAUDE.md natively). Follow TDD.

## WHERE

### Modified files
- `src/mcp_coder/llm/interface.py`
- `tests/llm/test_interface.py`

## WHAT

### Changes to `prompt_llm()` in `interface.py`

1. Replace `if provider not in ("claude", "langchain"):` with `if provider not in SUPPORTED_PROVIDERS:`
2. Add `elif provider == "copilot":` branch after the `langchain` branch
3. Lazy-import `ask_copilot_cli` from `.providers.copilot`
4. Build system prompt for Copilot: use `system_prompt` only (skip `project_prompt` — Copilot reads CLAUDE.md natively). Pass `None` if `session_id` is set (skip on resume).
5. Pass `execution_dir` to `ask_copilot_cli()` — the copilot module reads `.claude/settings.local.json` internally
6. Call `ask_copilot_cli()` with appropriate parameters
7. Wrap `TimeoutExpired` in `LLMTimeoutError` (same pattern as Claude)

### Changes to `prompt_llm_stream()` in `interface.py`

1. Replace `if provider not in ("claude", "langchain"):` with `if provider not in SUPPORTED_PROVIDERS:`
2. Add `elif provider == "copilot":` branch
3. Lazy-import `ask_copilot_cli_stream` from `.providers.copilot`
4. Same system prompt logic as `prompt_llm()`
5. Yield from `ask_copilot_cli_stream()`

### Settings.local.json reading

Uses `_read_settings_allow()` from `copilot_cli.py` (implemented in step 5).

## HOW

- Import `SUPPORTED_PROVIDERS` from `.types`
- Lazy-import copilot functions inside the `elif provider == "copilot":` branch
- `_read_settings_allow()` lives in `copilot_cli.py` (not interface.py) — reads JSON, extracts `permissions.allow` list
- `interface.py` passes `execution_dir` to `ask_copilot_cli()`, which calls `_read_settings_allow()` internally

## ALGORITHM

### Copilot branch in prompt_llm
```
1. Derive logs_dir from env_vars MCP_CODER_PROJECT_DIR (same as Claude)
2. Build copilot_system_prompt: system_prompt if session_id is None, else None
3. Pass execution_dir to ask_copilot_cli() (it reads settings.local.json internally)
4. Call ask_copilot_cli(question, session_id, timeout, env_vars, cwd=execution_dir,
     logs_dir, branch_name, system_prompt=copilot_system_prompt, execution_dir=execution_dir)
5. Catch TimeoutExpired → raise LLMTimeoutError
```

## DATA

- Copilot branch produces same `LLMResponseDict` as other providers
- Error message in unsupported-provider ValueError now lists all three providers

## Tests

### `tests/llm/test_interface.py`

#### Routing tests
- `test_prompt_llm_routes_to_copilot` — mock `ask_copilot_cli`, verify called with correct args
- `test_prompt_llm_stream_routes_to_copilot` — mock `ask_copilot_cli_stream`, verify yield

#### System prompt handling
- `test_copilot_system_prompt_passed_on_new_session` — no session_id → system_prompt forwarded
- `test_copilot_system_prompt_skipped_on_resume` — session_id set → system_prompt=None
- `test_copilot_project_prompt_always_skipped` — project_prompt never forwarded to copilot

#### Error handling
- `test_copilot_timeout_raises_llm_timeout_error` — TimeoutExpired → LLMTimeoutError
- `test_unsupported_provider_error_lists_all_providers` — error message includes "copilot"

#### Validation
- `test_prompt_llm_accepts_copilot_provider` — no ValueError for provider="copilot"
- `test_prompt_llm_stream_accepts_copilot_provider` — no ValueError for provider="copilot"


