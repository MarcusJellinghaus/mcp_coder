# Decisions for Issue #358

| Topic | Decision | Rationale |
|-------|----------|-----------|
| File moves | Use `mcp__filesystem__move_file` | MCP tool handles git mv under the hood |
| Coordinator vscodeclaude re-exports | Clean delete | Consumers import directly from `workflows.vscodeclaude` |
| `get_cache_refresh_minutes` re-export | No re-export from coordinator | Consumers import from `utils.user_config` |
| Test file location | Stay in `tests/utils/vscodeclaude/` | Move to `tests/workflows/vscodeclaude/` in follow-up PR |
