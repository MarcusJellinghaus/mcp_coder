# Claude Code Configuration

Installing Claude Code for MCP Coder workflows. The files inside a repository (`.claude/`, `.mcp.json`, permissions): [Claude Code Setup](../repository-setup/claude-code.md).

## Prerequisites

- **Anthropic API key** (or a Claude subscription) for Claude access
- **Python 3.11+** and **Git**
- **GitHub token** for issue and PR workflows, configured in `~/.mcp_coder/config.toml` ([GitHub token](../repository-setup/github.md#github-token-configuration))

## Install and verify

Install the CLI as described in [Anthropic's documentation](https://code.claude.com/docs), then:

```bash
claude --version
claude -p "Hello, Claude!"
```

## Launcher (Windows)

Start Claude through the `claude.bat` or `claude_local.bat` launchers from this repository rather than configuring PATH by hand. They activate the venv, set the MCP environment variables and disable the auto-updater: [Launcher Scripts](../repository-setup/claude-code.md#launcher-scripts). How the tool and project environments interact: [Environments](../environments/environments.md).

## Related documentation

- [Repository Setup](../repository-setup/README.md)
- [Configuration Guide](config.md), including the [`[claude]` section](config.md#claude)
- [Copilot CLI Setup](../repository-setup/copilot.md)
- [Slash command cheat sheet](../processes-prompts/claude_cheat_sheet.md)
- [Claude Code documentation](https://code.claude.com/docs) and [MCP specification](https://modelcontextprotocol.io/specification)
