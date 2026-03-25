# Step 4: Documentation Updates

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 4: update `docs/configuration/config.md` to document the `[mcp]` section and `MCP_CODER_MCP_CONFIG` env var. Update `docs/cli-reference.md` to note that `--mcp-config` is optional when a default is configured. Run all three code quality checks after changes.

## WHERE

- `docs/configuration/config.md` — add `[mcp]` section documentation
- `docs/cli-reference.md` — add note about optional `--mcp-config`

## WHAT

### `docs/configuration/config.md`

Add a new `### [mcp]` section (after `### [llm]`) documenting:

- Purpose: configures default MCP config file path
- Config key: `default_config_path`
- Env var: `MCP_CODER_MCP_CONFIG` (higher priority than config file)
- Resolution priority: CLI arg > env var > config > auto-detect
- Relative paths resolved relative to CWD
- Error behavior: lenient for env var / config (warn + fall back), strict for CLI arg

Example:

```toml
[mcp]
# Default MCP config file path (relative to CWD or absolute)
# Environment variable (higher priority): MCP_CODER_MCP_CONFIG
default_config_path = ".mcp.json"
```

Also add to the Environment Variable Overrides table:

```
| `MCP_CODER_MCP_CONFIG` | `[mcp] default_config_path` | `.mcp.json` |
```

And add to the Quick Reference table:

```
| **MCP Config** | `[mcp]` section in `config.toml` |
```

### `docs/cli-reference.md`

In the **MCP Configuration** section at the bottom, add a note:

```markdown
**Default configuration:** The `--mcp-config` flag is optional when a default 
is configured via the `MCP_CODER_MCP_CONFIG` environment variable or 
`[mcp] default_config_path` in `config.toml`. See 
[Configuration Guide](configuration/config.md) for details.
```

## ALGORITHM

No code logic — documentation only.

## DATA

N/A — documentation changes only.

## Commit

One commit: documentation updates for `[mcp]` section and env var.
