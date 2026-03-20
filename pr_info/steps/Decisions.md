# Decisions

## Decision 1: Env var support in shared `resolve_llm_method()`

**Context:** Verify command currently uses `MCP_CODER_LLM_PROVIDER` env var via its private `_resolve_active_provider()`. The plan deletes that function and replaces it with the shared `resolve_llm_method()`.

**Decision:** Add env var `MCP_CODER_LLM_PROVIDER` support to the shared `resolve_llm_method()`.

Resolution order: CLI arg → env var (`MCP_CODER_LLM_PROVIDER`) → config `default_provider` → default `"claude"`.

Source string for env var: `"env MCP_CODER_LLM_PROVIDER"`.

This way verify's `_resolve_active_provider()` can be deleted, and all commands automatically gain env var support.

## Decision 2: Remove `--mcp-config` from commit auto

**Context:** Commit auto has `--mcp-config` defined in the parser but unused, with a TODO comment suggesting future MCP support.

**Decision:** Remove `--mcp-config` from commit auto parser and delete the TODO. Add a comment explaining why MCP doesn't apply: commit message generation is text-in/text-out — it takes diff text and produces a commit message, no tool use needed.

## Decision 3: No negative test for old config key

**Context:** Config key renamed from `[llm] provider` to `[llm] default_provider` with a clean break.

**Decision:** Skip adding a negative test for the old key. Clean break, no special handling — the code simply reads a different key now. YAGNI.
