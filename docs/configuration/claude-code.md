# Claude Code Configuration

Configuration guide for Claude Code CLI to work with MCP Coder workflows.

## Overview

Claude Code CLI is the primary LLM interface for MCP Coder's automated workflows. This guide covers:

- Claude Code CLI installation and verification
- Project configuration files (`.claude/` folder)
- Integration with mcp-coder commands

> **Note:** For MCP server configuration (`.mcp.json`), see [Repository Setup Guide](../repository-setup.md#mcp-json---mcp-server-configuration).

## Installation

### Prerequisites

- **Anthropic API Key**: Required for Claude API access
- **Python 3.11+**: For MCP server compatibility
- **Git**: For repository operations
- **GitHub Token**: Required for issue/PR workflows - configure in `~/.mcp_coder/config.toml` (see [Repository Setup](../repository-setup.md#github-token-configuration))

### Claude Code CLI Installation

Follow the installation guide at [Anthropic's documentation](https://docs.anthropic.com/en/docs/claude-code).

### Windows Setup with `claude.bat`

For Windows users, create a `claude.bat` launcher script in your project root. This approach is **recommended** over manual PATH configuration because it:

- **Auto-activates** the virtual environment
- **Sets environment variables** (`MCP_CODER_PROJECT_DIR`, `MCP_CODER_VENV_DIR`) required by MCP servers
- **Disables auto-updater** for consistent behavior
- **Clears screen** for clean startup

**Example `claude.bat`:**

```batch
@echo off
cls
setlocal enabledelayedexpansion
REM Simple launcher for Claude Code with MCP servers

REM Check if virtual environment is activated
if "!VIRTUAL_ENV!"=="" (
    if not exist ".venv\Scripts\activate.bat" (
        echo ERROR: Virtual environment not found at .venv
        exit /b 1
    )
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Set project directories for MCP servers
set "MCP_CODER_PROJECT_DIR=%CD%"
set "MCP_CODER_VENV_DIR=%CD%\.venv"
set "DISABLE_AUTOUPDATER=1"

REM Start Claude Code
echo Starting Claude Code with:
echo MCP_CODER_PROJECT_DIR=!MCP_CODER_PROJECT_DIR!
echo MCP_CODER_VENV_DIR=!MCP_CODER_VENV_DIR!
C:\Users\%USERNAME%\.local\bin\claude.exe %*
```

**Usage:**
```cmd
cd your-project
claude.bat
```

### Verification

```bash
# Verify installation
claude --version

# Test basic functionality
claude -p "Hello, Claude!"
```

## Project Configuration Files

Claude Code uses a `.claude/` folder in your project root for configuration.

### Directory Structure

```
your-project/
├── .claude/
│   ├── CLAUDE.md              # Project instructions (mandatory)
│   ├── settings.local.json    # Local settings (optional)
│   └── commands/              # Slash commands (optional)
│       ├── commit_push.md
│       ├── plan_review.md
│       └── ...
├── .mcp.json                  # MCP server config (see repository-setup.md)
└── ...
```

### `.claude/CLAUDE.md` - Project Instructions

This file contains **mandatory instructions** that Claude follows when working on your project. Claude reads this file at the start of every session. The file included with MCP Coder gives a strong preference to the related MCP servers. Adjust the instructions for your purposes. The MCP-Coder `implement` assumes to have access to the files and to be able to run pylint, pytest and mypy, prefereably via MCP-Coder.

**Purpose:**

- Define code quality requirements
- Set project-specific conventions
- Specify mandatory tool usage (e.g., MCP tools)
- Configure workflow behaviors

**See mcp-coder's own [CLAUDE.md](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/.claude/CLAUDE.md) for a comprehensive example.**

### `.claude/settings.local.json` - Local Settings

This file configures Claude Code permissions and MCP server settings for your local environment. It should be gitignored since it may contain user-specific paths.

**See mcp-coder's own [settings.local.json](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/.claude/settings.local.json) for a reference.**

**Key sections:**

```json
{
  "permissions": {
    "allow": [
      "mcp__code-checker__*",
      "mcp__filesystem__*",
      "Bash(git diff:*)",
      "Bash(git status:*)",
      "Bash(./tools/format_all.sh:*)",
      "Skill(commit_push)",
      "Skill(plan_review)"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "code-checker",
    "filesystem"
  ]
}
```

**Explanation:**

| Setting | Purpose |
|---------|---------|
| `permissions.allow` | Pre-approved tools (avoids confirmation prompts) |
| `enableAllProjectMcpServers` | Enable MCP servers defined in `.mcp.json` |
| `enabledMcpjsonServers` | Specific MCP servers to enable |

**Security considerations:**

- **Allow MCP servers**: Enable `mcp__code-checker__*` and `mcp__filesystem__*` for development workflows
- **Allow read-only commands**: `Bash(git diff:*)`, `Bash(git status:*)` are safe
- **Allow formatting tools**: `Bash(./tools/format_all.sh:*)` for code formatting
- **Restrict dangerous commands**: Do NOT allow unrestricted `Bash(*)` - this could modify files outside the project or execute arbitrary commands

**Gitignore:** For your own projects, add to `.gitignore`:

```gitignore
.claude/settings.local.json
```

> **Note:** In the mcp-coder repository itself, this file is tracked as a reference template for users.

### `.claude/commands/` - Slash Commands

Slash commands provide structured workflows for common tasks. They appear as `/command_name` in Claude Code.

For the MCP Coder and its processes, a number of slash commands have been defined.

**Available commands** (see [Claude Code Cheat Sheet](../processes-prompts/claude_cheat_sheet.md) for full list):

| Command | Purpose |
|---------|---------|
| `/issue_analyse` | Analyze GitHub issue requirements |
| `/plan_review` | Review implementation plan |
| `/plan_approve` | Approve plan for implementation |
| `/implementation_review` | Code review |
| `/commit_push` | Format, commit, and push changes |
| `/rebase` | Rebase branch onto main |

## Integration with mcp-coder Commands

### Environment Variables

mcp-coder sets these environment variables for MCP servers:

| Variable | Description |
|----------|-------------|
| `MCP_CODER_PROJECT_DIR` | Absolute path to project directory |
| `MCP_CODER_VENV_DIR` | Path to Python virtual environment |

These are used in `.mcp.json` to configure MCP servers with correct paths:

```json
{
  "mcpServers": {
    "code-checker": {
      "type": "stdio",
      "command": "${MCP_CODER_VENV_DIR}\\Scripts\\mcp-code-checker.exe",
      "args": [
        "--project-dir", "${MCP_CODER_PROJECT_DIR}",
        "--python-executable", "${MCP_CODER_VENV_DIR}\\Scripts\\python.exe",
        "--venv-path", "${MCP_CODER_VENV_DIR}",
        "--test-folder", "tests",
        "--log-level", "INFO"
      ],
      "env": {
        "PYTHONPATH": "${MCP_CODER_PROJECT_DIR}/src"
      }
    },
    "filesystem": {
      "type": "stdio",
      "command": "${MCP_CODER_VENV_DIR}/Scripts/mcp-server-filesystem.exe",
      "args": [
        "--project-dir", "${MCP_CODER_PROJECT_DIR}",
        "--log-level", "INFO"
      ]
    }
  }
}
```

## Related Documentation

- **[Repository Setup](../repository-setup.md)** - Complete project setup including MCP configuration
- **[Claude Desktop Configuration](claude-desktop.md)** - Alternative Claude interface
- **[Configuration Guide](config.md)** - General mcp-coder configuration
- **[Claude Code Cheat Sheet](../processes-prompts/claude_cheat_sheet.md)** - Slash command reference
- **[Development Process](../processes-prompts/development-process.md)** - Workflow methodology

## External Resources

- **[Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)** - Official Anthropic documentation
- **[MCP Protocol](https://spec.modelcontextprotocol.io/)** - Model Context Protocol specification
