# Claude Desktop Configuration

Setup guide for Claude Desktop to work with MCP Coder development workflows.

## Overview

Claude Desktop provides an interactive LLM interface. With MCP servers, it allows software development:

**Required MCP Servers:**
- **[mcp-server-filesystem](https://github.com/MarcusJellinghaus/mcp_server_filesystem)** - Secure file access for project analysis
- **[mcp-code-checker](https://github.com/MarcusJellinghaus/mcp-code-checker)** - Code quality analysis (optional)

**Configuration tool:** Use [mcp-config](https://github.com/MarcusJellinghaus/mcp-config) to manage MCP server configurations.

**Note:** Claude Desktop doesn't support stored prompts or slash commands - copy/paste from [development-process.md](../processes-prompts/development-process.md) as needed.

## Workflow Integration

| Phase | Claude Desktop Use Case |
|-------|------------------------|
| **Issue Discussion** | Interactive requirement analysis and codebase exploration |
| **Plan Review** | Collaborative review of generated plans in `pr_info/steps/` |
| **Code Review** | Deep analysis of implementations and git diffs |

With mcp-coder, it is possible to automate the creation of the implementation plan, to run the implementation itself and to create the pull request. mcp-coder can also trigger these tasks automatically.

## Troubleshooting

**Config file locations:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Related Documentation

- **[Claude Code Configuration](claude-code.md)** - Claude Code CLI setup
- **[Development Process](../processes-prompts/development-process.md)** - Complete workflow
- **[MCP Documentation](https://spec.modelcontextprotocol.io/)** - Protocol specification