# Summary — Show `mcp-coder-utils` Version on Startup (#926)

## Goal

Display the installed `mcp-coder-utils` version in iCoder's startup banner and `/info` output, alongside `mcp-coder`. Provide a graceful `"unknown"` fallback if the package metadata is missing.

## Architectural / Design Changes

1. **New private helper** `_get_package_version(name) -> str` in `env_setup.py`:
   - Wraps `importlib.metadata.version()` in `try/except PackageNotFoundError`.
   - Returns `"unknown"` on failure.
   - Mirrors the existing `_get_claude_code_version()` graceful-fallback pattern.
   - Used for both `mcp-coder` and `mcp-coder-utils` lookups (no duplication).

2. **`RuntimeInfo` gains one field**: `mcp_coder_utils_version: str`.
   - Both display sites (banner + `/info`) read from `RuntimeInfo` — single source of truth.
   - Eliminates the live `importlib.metadata.version()` call currently in `info.py` (and its corresponding import).

3. **No new modules, no shared constants, no changes to MCP server discovery, dependency wiring, or test infrastructure.** This is a small, surgical addition.

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/env_setup.py` | Add `_get_package_version` helper; add `mcp_coder_utils_version` field to `RuntimeInfo`; route both versions through the helper |
| `src/mcp_coder/icoder/ui/app.py` | Insert one banner line after `mcp-coder` line in `on_mount` |
| `src/mcp_coder/icoder/core/commands/info.py` | Read `mcp-coder` version from `runtime_info`, add `mcp-coder-utils` line, drop `import importlib.metadata` |
| `tests/icoder/test_env_setup.py` | Add helper tests; update `RuntimeInfo` direct instantiation; assert new field in integration test |
| `tests/icoder/test_info_command.py` | Update `runtime_info` fixture; replace `importlib.metadata` mock-based test with a `runtime_info`-driven test; add assertion for new line |

**No files created. No files deleted.**

## Decisions Recap (KISS-trimmed)

| Topic | Decision |
|-------|----------|
| Helper extraction | Yes — single `_get_package_version` reused for both packages |
| Fallback | `"unknown"` on `PackageNotFoundError` |
| Display format | Same dev-version format as `mcp-coder` |
| Banner placement | Right after `mcp-coder` line, before MCP server lines |
| `/info` placement | Right after existing `mcp-coder version:` line |
| `/info` source of truth | Both lines from `runtime_info.*_version` (DRY); drop unused import |
| Field name | `mcp_coder_utils_version: str` |
| Tests for helper | Both happy + failure paths (per issue); use real package names — no mocking |

## Step Overview (one commit each)

| Step | File(s) | What |
|------|---------|------|
| 1 | `env_setup.py` + `test_env_setup.py` | Add helper + `RuntimeInfo` field; update tests |
| 2 | `ui/app.py` | Add banner line |
| 3 | `commands/info.py` + `test_info_command.py` | Migrate to `runtime_info`, add line, drop import; update tests |

Each step is self-contained: tests pass, all three quality checks (pylint / pytest / mypy) pass.
