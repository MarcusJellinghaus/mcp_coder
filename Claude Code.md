
# Claude Code

## Installation and getting started

### Download Claude Code CLI
Download the Claude Code CLI from [Anthropic's webpage](https://docs.claude.com/en/docs/claude-code/setup)

### Start Claude in Powershell
```
& "$env:USERPROFILE\.local\bin\claude.exe"
```

### Start Claude in CMD
```
C:\Users\%USERNAME%\.local\bin\claude.exe
```

### Adding Claude to system PATH in CMD

```
setx PATH "%PATH%;%USERPROFILE%\.local\bin"
```
restart CMD or Powershell after setting PATH
Now, simply `claude` should work in any terminal.

### Useful parameters

- `--version`  Show the version and exit
- `--help`  Show help message and exit

- `mcp add-from-claude-desktop` Add mcp config files from Claude Desktop (limited platform support)

- `mcp list` List MCP projects

### useful commands inside Claude Code
- `/` Show available commands
- `/exit` Exit the current conversation
- `/clear` Clear the current conversation
- `/doctor` Run a diagnostic check on the current conversation, also checking MC servers
-  `/help` Show help information about available commands
- `/mcp` Show MCP servers and configurations, also the tools and their documentation

## MCP Configuration

- Project configuration file: `.mcp.json` in project root directory ( alternatively `mcp.json` ?)

## Claude memory file
- File: `.claude_code/memory.jsonl` in project root
- Stores conversation history and context for Claude Code interactions
- Use `/init` command to configure initial memory settings

## Claude project file
- File: `.claude\CLAUDE.md` in project root

### Claude local settings
- File: `.claude/settings.local.json`
- Possible content for MCP Servers:
```json
{
  "enabledMcpjsonServers": [
    "code-checker",
    "filesystem"
  ]
}
```

### Documentation

- [MCP Configuration](https://docs.claude.com/en/docs/claude-code/mcp) - How to configure MCP servers at project level

