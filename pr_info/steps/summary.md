# Issue #517: feat(llm): add MCP tool-use support for LangChain provider

## Summary

Enable the LangChain provider to use MCP tools via LangChain's agent framework,
so that **all 6 CLI commands** work with `--llm-method langchain` — not just text-only commands.

Currently `interface.py` silently drops `mcp_config`, `execution_dir`, `env_vars` when
routing to `ask_langchain()`. This change adds an **agent mode** that activates when
`mcp_config` is provided, using `langchain-mcp-adapters` + `langgraph` to bridge MCP
servers into LangChain tool-calling agents.

## Architectural / Design Changes

### Before (text-only)

```
interface.py → ask_langchain(question, session_id, timeout)
                   → openai_backend / gemini_backend / anthropic_backend
                   → returns text response
```

### After (text-only + agent mode)

```
interface.py → ask_langchain(question, session_id, timeout,
                              mcp_config, execution_dir, env_vars)
                   │
                   ├─ mcp_config is None → existing text-only path (unchanged)
                   │
                   └─ mcp_config provided → agent mode:
                        → runtime import check (langchain_mcp_adapters, langgraph)
                        → asyncio.run(run_agent(...))
                            → load .mcp.json + resolve ${VAR} placeholders
                            → MultiServerMCPClient (stdio transport)
                            → create_react_agent(chat_model, tools)
                            → invoke with history, capped at AGENT_MAX_STEPS=50
                            → return (text, messages, stats)
                        → store full message history (LangChain native serialization)
                        → log to MLflow (params, metrics, tool_trace.json)
```

### Key Design Decisions (from issue)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent output | Final text only in `text` field | Matches `LLMResponseDict` contract |
| Error handling | Hard fail on MCP server startup; tool errors → agent recovery | Strict mode |
| Async | `asyncio.run()` wrapper | Matches Claude API provider pattern |
| Max iterations | `AGENT_MAX_STEPS = 50`, partial output on limit | Prevents runaway loops |
| Transport | `stdio` only | Only transport used by the project |
| Session | LangChain native `.dict()` serialization for all message types. No mode marker needed (Decision 11) — `_to_lc_messages()` handles all types | Single deserialization path for both modes |
| Verify | Runtime: package check. Verify cmd: also stdio smoke test | Two levels |

### What is NOT changing

- No changes to Claude provider
- No changes to MLflowLogger class itself (reuse existing methods)
- No changes to session storage API (reuse existing functions)
- Text-only mode remains fully backward compatible

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/llm/providers/langchain/agent.py` | Agent module: env var resolution, MCP config loading, agent execution |
| `tests/llm/providers/langchain/test_langchain_agent.py` | Unit tests for agent module |

## Files to Modify (backend refactor — Decision 9)

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/openai_backend.py` | Extract model creation into reusable function |
| `src/mcp_coder/llm/providers/langchain/gemini_backend.py` | Extract model creation into reusable function |
| `src/mcp_coder/llm/providers/langchain/anthropic_backend.py` | Extract model creation into reusable function |

## Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Add `langchain-mcp-adapters`, `langgraph` to `[langchain]` extras |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Extend `ask_langchain()` with `mcp_config`, `execution_dir`, `env_vars` params; add agent mode branch + MLflow logging |
| `src/mcp_coder/llm/interface.py` | Pass `mcp_config`, `execution_dir`, `env_vars` through to `ask_langchain()` |
| `src/mcp_coder/llm/providers/langchain/verification.py` | Add MCP adapter package checks + stdio smoke test |
| `src/mcp_coder/cli/commands/verify.py` | Wire new verification entries into label map and formatting |
| `src/mcp_coder/cli/parsers.py` | Add `--mcp-config` argument to verify subparser (Decision 13) |
| `src/mcp_coder/llm/providers/langchain/_utils.py` | Extend `_to_lc_messages()` with ToolMessage + tool_calls support (Decision 10) |
| `tests/llm/providers/langchain/conftest.py` | Add `langchain_mcp_adapters` and `langgraph` mock modules |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Add tests for agent mode routing in `ask_langchain()` |

## Implementation Steps

1. **Step 1** — Dependencies + agent utilities (env var substitution, MCP config loading)
2. **Step 2** — Agent execution core (`run_agent` with `create_react_agent`)
3. **Step 3** — Extend `ask_langchain()` with agent mode routing + MLflow logging
4. **Step 4** — Update `interface.py` to pass parameters through
5. **Step 5** — Verification extensions (package checks + stdio smoke test)

Each step follows TDD: tests first, then implementation.

See [Decisions.md](Decisions.md) for design decisions from plan review.
