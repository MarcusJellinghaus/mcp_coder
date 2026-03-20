# Issue #528: Finetune Dual LLM Provider Support

## Summary

This implementation finetunes the dual LLM provider support (Claude / LangChain) across 8 sub-tasks covering a critical bug fix, config key rename, auto-detection of `.mcp.json`, template cleanup, help text improvements, API parity exports, and CLI consistency fixes.

## Architecture / Design Changes

### 1. `resolve_llm_method()` return type change: `str` → `tuple[str, str]`

**Before:** Returns a plain string (`"claude"` or `"langchain"`).
**After:** Returns `(provider, source)` tuple, e.g. `("langchain", "config default_provider")`.

This unifies with `verify.py`'s existing `_resolve_active_provider()` which already returns the same shape. After the change, `_resolve_active_provider()` is deleted and all commands use the shared function.

**Impact:** Every caller of `resolve_llm_method()` must destructure the tuple. Most callers only need the provider: `provider, _ = resolve_llm_method(...)`. The `source` is used only by `verify`.

### 2. Config key rename: `[llm] provider` → `[llm] default_provider`

Clean break, no backwards compatibility. Affects two readers:
- `cli/utils.py:resolve_llm_method()` 
- `llm/providers/langchain/__init__.py:_load_langchain_config()`

A commented-out `[llm]` section is added to the default config template.

### 3. Auto-detection of `.mcp.json`

`resolve_mcp_config_path()` gains a `project_dir` parameter. When `mcp_config` is `None`, it checks `{project_dir}/.mcp.json` (or `{CWD}/.mcp.json`). If the file doesn't exist, returns `None` silently (debug log only).

### 4. `MultiServerMCPClient` context manager removal

The `async with` pattern is replaced with plain instantiation. The client in `langchain-mcp-adapters>=0.1.0` is stateless — no cleanup needed.

### 5. Template and help text changes

- Windows coordinator templates: Remove hardcoded `--llm-method claude`
- Linux templates: Add `# TODO - to be reviewed` comment
- `--llm-method` help: Updated to mention config fallback
- `--project-dir` / `--execution-dir` help: Clarified distinction

### 6. CLI command consistency

- `commit auto`: Remove `--mcp-config` (text-in/text-out, no MCP needed)
- `verify`: Add `--llm-method`, use shared `resolve_llm_method()`

### 7. API parity exports

New public exports: `verify_claude`, `verify_langchain`, `verify_mlflow`, `commit_auto`, `collect_branch_status`.

## Files Modified

| File | Changes |
|------|---------|
| `src/mcp_coder/llm/providers/langchain/agent.py` | Remove `async with` context manager |
| `src/mcp_coder/cli/utils.py` | Rename config key, change return type, add `project_dir` param |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Rename config key |
| `src/mcp_coder/utils/user_config.py` | Add `[llm]` section to config template |
| `src/mcp_coder/cli/parsers.py` | Help text updates, remove commit auto `--mcp-config`, add verify `--llm-method` |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Remove `--llm-method claude` from Windows templates |
| `src/mcp_coder/cli/commands/verify.py` | Delete `_resolve_active_provider()`, use shared function, accept `--llm-method` |
| `src/mcp_coder/cli/commands/commit.py` | Remove `mcp_config` handling, add comment |
| `src/mcp_coder/cli/commands/prompt.py` | Update `resolve_llm_method()` / `resolve_mcp_config_path()` callers |
| `src/mcp_coder/cli/commands/implement.py` | Update callers |
| `src/mcp_coder/cli/commands/create_plan.py` | Update callers |
| `src/mcp_coder/cli/commands/create_pr.py` | Update callers |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Update callers |
| `src/mcp_coder/__init__.py` | Add new exports |
| `src/mcp_coder/checks/__init__.py` | Export `collect_branch_status` |

## Files with Test Changes

| Test File | Covers |
|-----------|--------|
| `tests/llm/providers/langchain/test_langchain_agent.py` | Step 1: agent.py context manager fix |
| `tests/cli/test_utils.py` | Step 2: return type + config key + mcp auto-detect |
| `tests/utils/test_user_config.py` | Step 2: config template |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Step 2: config key rename |
| `tests/workflows/vscodeclaude/test_templates.py` | Step 3: template changes |
| `tests/cli/commands/test_verify.py` | Step 5: verify uses shared function |
| `tests/cli/commands/test_commit.py` | Step 5: commit auto removes mcp-config |
| `tests/cli/commands/test_prompt.py` | Step 4: caller updates |
| `tests/cli/commands/test_implement.py` | Step 4: caller updates |
| `tests/cli/commands/test_create_plan.py` | Step 4: caller updates |
| `tests/cli/commands/test_create_pr.py` | Step 4: caller updates |
| `tests/cli/commands/test_check_branch_status.py` | Step 4: caller updates |
| `tests/test_module_exports.py` | Step 6: API parity |

## Implementation Order

```
Step 1 (bug fix)  →  Step 2 (core resolution)  →  Step 3 (templates + help)
                                                →  Step 4 (update all callers)
                                                →  Step 5 (CLI consistency)
                                                →  Step 6 (API exports)
```

Steps 3-6 depend on Step 2 being complete. Steps 3-6 are independent of each other.
