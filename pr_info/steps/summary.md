# Issue #769 — iCoder Timeout Improvements

## Problem
iCoder shows a raw `Error: Agent produced no output for 300s` message on inactivity timeout. Three distinct timeout paths (Claude CLI, langchain agent, langchain text-stream) all produce unhelpful messages. Additionally, the Claude CLI path emits a redundant "CLI failed" error after a timeout kill.

## Goals
1. **Better error messages** — each timeout path gets a distinct, informative message with provider name, timeout value, what happened, and what to do.
2. **`--timeout` CLI flag** — let users adjust the inactivity timeout (default 300s).
3. **Suppress Claude CLI double-error** — change `if` to `elif` so only the timeout message appears.

## Design / Architecture Changes
- **No new files, classes, or abstractions.** This is a plumbing change through existing layers.
- **Data flow**: `argparse` → `icoder.py` → `RealLLMService(timeout=N)` → `prompt_llm_stream(timeout=N)` → provider. The `prompt_llm_stream` interface already accepts and forwards `timeout` — only the construction-time wiring in `RealLLMService` is new.
- **Error messages originate at providers**, not in `app.py`. The existing error event / exception flow carries improved messages naturally.
- **`LLMService` Protocol unchanged.** `FakeLLMService` unchanged.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Add `--timeout` arg to icoder parser |
| `src/mcp_coder/cli/commands/icoder.py` | Read `args.timeout`, pass to `RealLLMService` |
| `src/mcp_coder/icoder/services/llm_service.py` | Accept `timeout` param in `RealLLMService.__init__()` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | Improved timeout message + `elif` fix |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Improved timeout messages (agent + text-stream) |
| `tests/icoder/test_llm_service.py` | Update/add tests for new constructor parameter |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Update timeout message assertion + add double-error suppression test |
| `tests/llm/providers/langchain/test_langchain_streaming_timeout.py` | Update timeout message assertion |
| `tests/llm/providers/langchain/test_langchain_agent_streaming.py` | Update agent timeout message assertion (if test exists) |

## Implementation Order (3 steps)
1. **Step 1** — `RealLLMService` timeout param + `--timeout` CLI flag (tests first)
2. **Step 2** — Claude CLI: improved timeout message + `elif` double-error fix (tests first)
3. **Step 3** — Langchain: improved timeout messages for agent + text-stream (tests first)
