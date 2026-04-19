# Step 5: Copilot command builder + `ask_copilot_cli()`

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 5 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Add the command builder function and the main `ask_copilot_cli()` entry point to `copilot_cli.py`. The command builder constructs the Copilot CLI invocation with all flags. `ask_copilot_cli()` orchestrates: find executable, build command, check 8KB limit, execute subprocess, save JSONL log, parse output, return LLMResponseDict. Follow TDD.

## WHERE

### Modified files
- `src/mcp_coder/llm/providers/copilot/copilot_cli.py` (add command builder + ask function)
- `tests/llm/providers/copilot/test_copilot_cli.py` (add command builder + ask tests)

## WHAT

### Command builder

```python
# Windows CreateProcess limit for .CMD wrappers
COPILOT_CMD_LINE_LIMIT = 8192

def build_copilot_command(
    prompt: str,
    copilot_cmd: str,
    session_id: str | None = None,
    available_tools: list[str] | None = None,
    allow_tools: list[str] | None = None,
) -> list[str]:
    """Build Copilot CLI command arguments.

    Always includes: -p, --output-format json, -s, --allow-all-tools
    Conditionally: --available-tools, --allow-tool (per entry), --resume

    Args:
        prompt: User prompt text (passed via -p)
        copilot_cmd: Path to copilot executable
        session_id: Optional session ID for --resume
        available_tools: Flat hyphen format tool names for --available-tools
        allow_tools: Parentheses format entries for --allow-tool (one flag per entry)

    Returns:
        Command list ready for subprocess execution.

    Raises:
        ValueError: If copilot_cmd is empty, or if combined command exceeds 8KB.
    """
```

### Main entry point

```python
def ask_copilot_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    logs_dir: str | None = None,
    branch_name: str | None = None,
    system_prompt: str | None = None,
    settings_allow: list[str] | None = None,
) -> LLMResponseDict:
    """Ask Copilot CLI with session support and JSONL logging.

    Args:
        question: The question to ask
        session_id: Optional session ID to resume (skips system_prompt if set)
        timeout: Timeout in seconds
        env_vars: Environment variables for subprocess
        cwd: Working directory (Copilot discovers .mcp.json from here)
        logs_dir: Log directory for JSONL files
        branch_name: Git branch for log filename context
        system_prompt: System prompt to prepend to question (skipped on resume)
        settings_allow: Permission entries from settings.local.json to convert

    Returns:
        LLMResponseDict with text, session_id, provider="copilot", raw_response

    Raises:
        ValueError: If question is empty or command exceeds 8KB
        FileNotFoundError: If copilot executable not found
        TimeoutExpired: If command times out
        CalledProcessError: If command fails
    """
```

## HOW

- Imports `find_executable` from `mcp_coder.utils.executable_finder`
- Imports `execute_subprocess`, `CommandOptions`, `TimeoutExpired`, `CalledProcessError` from subprocess_runner
- Imports `LLMResponseDict`, `LLM_RESPONSE_VERSION` from `...types`
- Imports `get_stream_log_path` from `.copilot_cli_log_paths`
- Imports `logging_utils` from `..claude.logging_utils` (shared — not Claude-specific)

## ALGORITHM

### Command builder
```
1. Start with [copilot_cmd, "-p", prompt_text, "--output-format", "json", "-s", "--allow-all-tools"]
2. If available_tools: append --available-tools=<comma-separated>
3. For each allow_tool: append --allow-tool=<entry>
4. If session_id: append --resume=<session_id>
5. Check sum of arg lengths; if > 8KB raise ValueError with guidance
6. Return command list
```

### ask_copilot_cli
```
1. Validate inputs (empty question, timeout <= 0)
2. Find copilot via find_executable("copilot", install_hint=...)
3. Build prompt: if session_id is None and system_prompt set, prepend system_prompt to question
4. Convert settings_allow via convert_settings_to_copilot_tools() if provided
5. Build command via build_copilot_command()
6. Execute subprocess with cwd=cwd, save stdout to JSONL log file
7. Parse output via parse_copilot_jsonl_output(), build and return LLMResponseDict
```

## DATA

### Command structure
```bash
copilot -p "<system_prompt>\n\n<question>" \
  --output-format json \
  -s \
  --allow-all-tools \
  --available-tools="workspace-read_file,tools-py-run_pytest_check" \
  --allow-tool='shell(git diff:*)' \
  --resume=<session_id>
```

### Return value
```python
LLMResponseDict(
    version="1.0",
    timestamp="2026-04-19T...",
    text="...",
    session_id="copilot-session-id",
    provider="copilot",
    raw_response={
        "messages": [...],
        "stream_file": "logs/copilot-sessions/session_....ndjson",
        "usage": {"output_tokens": 150},
        "sessionId": "...",
        "premiumRequests": ...,
        ...
    }
)
```

## Tests

### Command builder tests
- `test_build_basic_command` — minimal args produce correct flag order
- `test_build_command_with_session_id` — `--resume=<id>` included
- `test_build_command_with_available_tools` — `--available-tools=` comma-separated
- `test_build_command_with_allow_tools` — multiple `--allow-tool=` flags
- `test_build_command_always_includes_s_flag` — `-s` always present
- `test_build_command_always_includes_allow_all_tools` — `--allow-all-tools` always present
- `test_build_command_empty_cmd_raises` — ValueError for empty copilot_cmd
- `test_build_command_exceeds_8kb_raises` — ValueError with guidance message

### ask_copilot_cli tests (mocked subprocess)
- `test_ask_copilot_cli_success` — mock subprocess, verify LLMResponseDict structure
- `test_ask_copilot_cli_session_id_returned` — verify session_id from JSONL result
- `test_ask_copilot_cli_system_prompt_prepended` — verify prompt starts with system prompt
- `test_ask_copilot_cli_system_prompt_skipped_on_resume` — session_id set → no system prompt
- `test_ask_copilot_cli_empty_question_raises` — ValueError
- `test_ask_copilot_cli_timeout_raises` — TimeoutExpired propagated
- `test_ask_copilot_cli_nonzero_exit_raises` — CalledProcessError with stream file path
- `test_ask_copilot_cli_saves_jsonl_log` — verify log file written
- `test_ask_copilot_cli_not_found_raises` — FileNotFoundError from find_executable
