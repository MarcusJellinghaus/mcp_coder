# Issue #741: iCoder `/info` Slash Command + Persistent MCPManager

## Overview

Add an `/info` slash command to iCoder that displays runtime diagnostics and a `MCPManager` component that holds persistent MCP connections for the Langchain provider, replacing per-request connection creation.

## Architecture & Design Changes

### New Components

1. **`MCPManager`** (`src/mcp_coder/llm/mcp_manager.py`)
   - Owns persistent MCP server connections for the app's lifetime
   - Runs a dedicated daemon thread with its own `asyncio` event loop (required because Textual owns the main event loop)
   - Lazy connection: connects on first `tools()` call, not at construction
   - Reconnection strategy: recreate entire `MultiServerMCPClient` on failure (simple, robust)
   - Exposes `tools()`, `status()`, `close()`
   - No Textual dependency — works in TUI, CLI, tests, or headless mode

2. **`/info` command** (`src/mcp_coder/icoder/core/commands/info.py`)
   - Closure-based registration: `register_info(registry, runtime_info, mcp_manager)` captures dependencies
   - Re-reads all values live on each invocation (not cached from `RuntimeInfo`)
   - Inline secret redaction (`_redact_env_vars`) with TODO to swap to `mcp_coder_utils` when available

### Modified Components

3. **Langchain agent** (`src/mcp_coder/llm/providers/langchain/agent.py`)
   - `run_agent_stream()` gains optional `tools` parameter — when provided, skips `MultiServerMCPClient` creation
   - `run_agent()` unchanged (not on icoder's hot path)

4. **Langchain provider** (`src/mcp_coder/llm/providers/langchain/__init__.py`)
   - `_ask_agent_stream()` gains optional `tools` parameter, passes through to `run_agent_stream()`
   - `ask_langchain_stream()` gains optional `tools` parameter, passes through to `_ask_agent_stream()`

5. **LLM interface** (`src/mcp_coder/llm/interface.py`)
   - `prompt_llm_stream()` gains optional `tools` parameter, passes to langchain path only

6. **LLM service** (`src/mcp_coder/icoder/services/llm_service.py`)
   - `RealLLMService` gains optional `mcp_manager` parameter; calls `mcp_manager.tools()` when streaming and passes to `prompt_llm_stream()`
   - `LLMService` protocol and `FakeLLMService` unchanged

7. **iCoder entry point** (`src/mcp_coder/cli/commands/icoder.py`)
   - Creates `MCPManager` (when provider is langchain and mcp_config exists)
   - Registers `/info` command with `register_info()`
   - Ensures `MCPManager.close()` on exit via try/finally

### Data Flow

```
execute_icoder()
  ├── MCPManager(server_config)          # created once
  ├── register_info(registry, runtime_info, mcp_manager)
  ├── RealLLMService(mcp_manager=mcp_manager)
  │     └── stream() → prompt_llm_stream(tools=mcp_manager.tools())
  │           └── ask_langchain_stream(tools=...)
  │                 └── _ask_agent_stream(tools=...)
  │                       └── run_agent_stream(tools=...)  # skips MultiServerMCPClient
  └── MCPManager.close()                 # on exit
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Lazy connection (not eager startup) | Avoids startup complexity; first user message triggers connection |
| Recreate-everything on failure | Simple and robust; matches current per-request pattern but less frequent |
| Thread MCPManager through `tools` param | Minimal signature changes; middle layers just pass through |
| `run_agent()` untouched | Only streaming path used by icoder; non-streaming path works as-is |
| Inline `_redact_env_vars` | Unblocks from external dependency; trivial swap later |
| Closure-based `/info` registration | Matches existing `register_help` pattern; no `AppCore` changes needed |

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/llm/mcp_manager.py` | MCPManager class |
| `src/mcp_coder/icoder/core/commands/info.py` | `/info` command handler |
| `tests/llm/test_mcp_manager.py` | MCPManager unit tests |
| `tests/icoder/test_info_command.py` | `/info` command unit tests |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/agent.py` | `run_agent_stream()` optional `tools` param |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | `_ask_agent_stream()` + `ask_langchain_stream()` optional `tools` param |
| `src/mcp_coder/llm/interface.py` | `prompt_llm_stream()` optional `tools` param |
| `src/mcp_coder/icoder/services/llm_service.py` | `RealLLMService` optional `mcp_manager` |
| `src/mcp_coder/cli/commands/icoder.py` | Create MCPManager, register `/info`, cleanup |

## Implementation Order

| Step | Description | Depends On |
|------|-------------|------------|
| 1 | MCPManager class + tests | — |
| 2 | `run_agent_stream()` accepts optional `tools` + tests | Step 1 |
| 3 | Thread `tools` through langchain provider + interface + LLM service | Step 2 |
| 4 | `/info` command + tests | Step 1 |
| 5 | Wire everything in `execute_icoder()` | Steps 3, 4 |
