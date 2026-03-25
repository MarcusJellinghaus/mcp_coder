# Issue #527: Configurable Default MCP Config Path + Verify MCP for All Providers

## Summary

Add a resolution chain for MCP config path (CLI arg > env var > config file > auto-detect) so users don't need `--mcp-config` on every invocation. Update `mcp-coder verify` to show MCP config status and run server health checks for all providers, not just langchain.

## Architectural / Design Changes

### Resolution Chain Pattern (existing pattern reuse)

The `resolve_mcp_config_path()` function currently supports only CLI arg and auto-detect. This issue extends it to follow the same **4-level resolution chain** already used by `resolve_llm_method()`:

```
CLI argument  →  Environment variable  →  Config file  →  Default/auto-detect
```

This is not a new pattern — it's applying the existing `resolve_llm_method()` pattern to MCP config resolution. Key design difference: CLI arg is **strict** (raises `FileNotFoundError`), while env var and config are **lenient** (warn + fall back to auto-detect).

### Verify Command: Provider-Independent MCP Checks

Currently, MCP config resolution and server health checks only run when `active_provider == "langchain"`. This changes to:

- **MCP config resolution**: runs unconditionally (all providers may use MCP)
- **Server health checks**: runs whenever an MCP config is found, regardless of provider
- **Exit code impact**: MCP failures only affect exit code for langchain provider (informational for claude) — this behavior is **already correct** in `_compute_exit_code()`, no change needed there

### Config Template Extension

The `[mcp]` section is added as a commented-out block in `create_default_config()`, consistent with how `[llm]` is handled.

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/cli/utils.py` | **Modify** | Add env var + config lookup to `resolve_mcp_config_path()` |
| `src/mcp_coder/utils/user_config.py` | **Modify** | Add `[mcp]` to `verify_config()` display + `create_default_config()` template |
| `src/mcp_coder/cli/commands/verify.py` | **Modify** | Move MCP resolution outside provider branch; wrap health check in try/except ImportError; update section header |
| `docs/configuration/config.md` | **Modify** | Document `[mcp]` section and `MCP_CODER_MCP_CONFIG` env var |
| `docs/cli-reference.md` | **Modify** | Note `--mcp-config` is optional when default is configured |
| `tests/cli/test_utils.py` | **Modify** | Add tests for new resolution chain in `TestResolveMcpConfigPath` |
| `tests/utils/test_verify_config.py` | **Modify** | Add tests for `[mcp]` section display |
| `tests/utils/test_user_config.py` | **Modify** | Add test for `[mcp]` in config template |
| `tests/cli/commands/test_verify_orchestration.py` | **Modify** | Add tests for provider-independent MCP resolution and ImportError handling |

## Acceptance Criteria Mapping

| AC# | Criteria | Step |
|-----|----------|------|
| 1 | Env var `MCP_CODER_MCP_CONFIG` works | Step 1 |
| 2 | Config `[mcp] default_config_path` works | Step 1 |
| 3 | Priority: CLI > env var > config > auto-detect | Step 1 |
| 4 | CLI `--mcp-config` strict FileNotFoundError | Step 1 (existing, preserved) |
| 5 | Env var / config warn with source, fall back | Step 1 |
| 6 | `verify` always shows `[mcp]` section | Step 2 |
| 7 | `verify` runs MCP health checks for all providers | Step 3 |
| 8 | MCP failures only affect exit code for langchain | Step 3 (existing, preserved) |
| 9 | Missing `langchain-mcp-adapters` skipped with info | Step 3 |
| 10 | MCP servers header includes `(via langchain-mcp-adapters)` | Step 3 |
| 11 | `mcp-coder init` template has commented `[mcp]` section | Step 2 |
