# Copilot CLI Repository Setup

GitHub Copilot CLI works with the same repository files as Claude Code. No additional setup is needed if your project already follows the [Claude Code setup](claude-code.md).

## File Compatibility

| File | Copilot Support |
|------|----------------|
| `CLAUDE.md` / `.claude/CLAUDE.md` | Read natively as project instructions |
| `AGENTS.md` | Read natively (combined with `CLAUDE.md`, not prioritized) |
| `.github/copilot-instructions.md` | Copilot's own native instruction format |
| `.claude/skills/*/SKILL.md` | Read natively — same format and location |
| `.mcp.json` | Auto-discovered with env var substitution — same format |

All instruction files are **combined** — Copilot reads `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md` together.

## Copilot-Specific CLI Flags

| Flag | Purpose |
|------|---------|
| `--allow-all-tools` | Required for non-interactive mode |
| `--disable-builtin-mcps` | Force MCP-only tool usage (use project MCP servers exclusively) |

## Using Copilot with mcp-coder

Set Copilot as the default provider in `config.toml`:

```toml
[llm]
provider = "copilot"
```

Or use it ad-hoc on any command:

```bash
mcp-coder prompt "Your prompt" --llm-method copilot
mcp-coder implement --llm-method copilot
```

See [Configuration Guide](../configuration/config.md#llm) for all provider options.
