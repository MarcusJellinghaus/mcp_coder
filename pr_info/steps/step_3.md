# Step 3: Verify MCP for All Providers + ImportError Handling

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 3: modify `execute_verify()` in `src/mcp_coder/cli/commands/verify.py` so MCP config resolution and server health checks run for all providers, not just langchain. Handle missing `langchain-mcp-adapters` gracefully. Update section header. Follow TDD — write tests first, then implement. Run all three code quality checks after changes.

## WHERE

- **Test file**: `tests/cli/commands/test_verify_orchestration.py` — add new test class
- **Source file**: `src/mcp_coder/cli/commands/verify.py` — modify `execute_verify()`

## WHAT

### Changes to `execute_verify()`

1. Move `resolve_mcp_config_path()` call **before** the provider branch (currently inside `if active_provider == "langchain"`)
2. Run `verify_mcp_servers()` whenever `mcp_config_resolved` is not None, regardless of provider
3. Wrap `verify_mcp_servers()` in try/except `ImportError` — if `langchain-mcp-adapters` is not installed, print info message and skip
4. Change `_format_mcp_section` header from `"MCP SERVERS"` to `"MCP SERVERS (via langchain-mcp-adapters)"`

### New tests

```python
class TestVerifyMcpAllProviders:
    def test_mcp_config_resolved_for_claude_provider(self, ...): ...
    def test_mcp_servers_checked_for_claude_provider(self, ...): ...
    def test_mcp_import_error_shows_info_message(self, ...): ...
    def test_mcp_section_header_includes_library_name(self, ...): ...
    def test_mcp_failure_informational_for_claude(self, ...): ...
```

## HOW

### Current code structure (simplified)

```python
# Current: MCP only for langchain
if active_provider == "langchain":
    mcp_config_resolved = resolve_mcp_config_path(args.mcp_config, project_dir=args.project_dir)
    langchain_result = verify_langchain(...)
else:
    mcp_config_resolved = None

if mcp_config_resolved:
    mcp_result = verify_mcp_servers(mcp_config_resolved)
```

### New code structure

```python
# NEW: resolve MCP config for ALL providers (moved before provider branch)
mcp_config_resolved = resolve_mcp_config_path(args.mcp_config, project_dir=args.project_dir)

if active_provider == "langchain":
    langchain_result = verify_langchain(...)
else:
    ...

# NEW: MCP health check for all providers, with ImportError handling
if mcp_config_resolved:
    try:
        mcp_result = verify_mcp_servers(mcp_config_resolved)
        print(_format_mcp_section(mcp_result, symbols))
    except ImportError:
        print("\n=== MCP SERVERS (via langchain-mcp-adapters) ===")
        print(f"  {symbols['warning']} server health check skipped (langchain-mcp-adapters not installed)")
```

## ALGORITHM

```python
# 1. Resolve MCP config (moved up, unconditional)
mcp_config_resolved = resolve_mcp_config_path(args.mcp_config, project_dir=args.project_dir)

# 2. Provider-specific checks (langchain vs claude) — unchanged

# 3. MCP server health check (now unconditional when config exists)
if mcp_config_resolved:
    try:
        mcp_result = verify_mcp_servers(mcp_config_resolved)
        print(_format_mcp_section(mcp_result, symbols))
    except ImportError:
        print(info_message)

# 4. _compute_exit_code() — NO CHANGES (already handles MCP correctly)
```

## DATA

- `_format_mcp_section` header: `"\n=== MCP SERVERS (via langchain-mcp-adapters) ==="` (was `"\n=== MCP SERVERS ==="`)
- ImportError info message: `"  {warning_symbol} server health check skipped (langchain-mcp-adapters not installed)"`
- `_compute_exit_code()` already only counts MCP failures for langchain — no change needed

## Test Details

### `test_mcp_config_resolved_for_claude_provider`
- Set provider to claude, provide `mcp_config` arg pointing to real file
- Mock `verify_mcp_servers` to return ok result
- Assert `resolve_mcp_config_path` was called (i.e., MCP config resolved regardless of provider)

### `test_mcp_servers_checked_for_claude_provider`
- Set provider to claude, mock `resolve_mcp_config_path` to return a path
- Assert `verify_mcp_servers` is called

### `test_mcp_import_error_shows_info_message`
- Mock `verify_mcp_servers` to raise `ImportError`
- Mock `resolve_mcp_config_path` to return a path
- Assert output contains "server health check skipped" and "langchain-mcp-adapters not installed"

### `test_mcp_section_header_includes_library_name`
- Mock everything to get MCP section output
- Assert output contains "MCP SERVERS (via langchain-mcp-adapters)"

### `test_mcp_failure_informational_for_claude`
- Set provider to claude, mock MCP result with `overall_ok=False`
- Assert exit code is still 0 (informational only for claude)

## Commit

One commit: tests + implementation for provider-independent MCP verification + ImportError handling.
