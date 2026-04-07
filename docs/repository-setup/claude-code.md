# Claude Code Setup

MCP Coder currently uses Claude Code as the LLM backend. This file covers the required configuration files and Claude-related repo conventions.

> **Note:** Future versions may support additional LLM providers.
> 
> **See [Claude Code Configuration Guide](../configuration/claude-code.md)** for detailed setup including installation, CLI commands, and troubleshooting.

## Required Files

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Project-specific instructions for Claude |
| `.claude/skills/` | Skills for workflow stages |
| `.mcp.json` | MCP server configuration |

## `.claude/CLAUDE.md` - Project Instructions

This file contains mandatory instructions that Claude follows when working on your project. Create `.claude/CLAUDE.md` with project-specific rules.

**See:**
- [Claude Code Configuration Guide](../configuration/claude-code.md#claudeclaudemd---project-instructions) for detailed examples
- mcp-coder's own [CLAUDE.md](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/.claude/CLAUDE.md) for a comprehensive example

## `.claude/skills/` - Skills

Skills provide structured workflows for common tasks. Copy the skills from mcp-coder or create your own.

**Available commands** (see [Claude Code Cheat Sheet](../processes-prompts/claude_cheat_sheet.md) for details):

| Command | Purpose |
|---------|---------|
| `/issue_analyse` | Analyze GitHub issue requirements |
| `/plan_review` | Review implementation plan |
| `/plan_approve` | Approve plan for implementation |
| `/implementation_review` | Code review (human-supervised) |
| `/implementation_review_supervisor` | Code review (autonomous agent-driven) |
| `/commit_push` | Format, commit, and push changes |
| `/rebase` | Rebase branch onto main |

## `.mcp.json` - MCP Server Configuration

**Model Context Protocol (MCP)** enables Claude Code to use specialized servers for enhanced functionality:

- **tools-py**: Pylint, pytest, mypy integration
- **filesystem**: Enhanced file operations
- **Custom servers**: Project-specific tools

### Platform-Specific Configuration

MCP Coder supports platform-specific MCP configuration files:

| Platform | Config File |
|----------|-------------|
| **Linux** | `.mcp.linux.json` |
| **Windows** | `.mcp.windows.json` |
| **macOS** | `.mcp.macos.json` |
| **Generic** | `.mcp.json` |

**File location:** Project root directory

### MCP Configuration Essentials

**Reference Implementation:** See this repository's `.mcp.json` for a complete working configuration.

**Key Configuration Aspects:**

1. **Platform-Specific Paths**:
   - **Windows**: Use double backslashes (`\\`) and `.exe` extensions
   - **Unix**: Use forward slashes, no extensions needed
   - **Environment variables**: `${MCP_CODER_PROJECT_DIR}` and `${MCP_CODER_VENV_DIR}` are set by mcp-coder

2. **Essential Arguments**:
   - `--project-dir`: Points to your project root
   - `--python-executable`: Specific Python executable in your venv
   - `--venv-path`: Virtual environment location
   - `--test-folder`: Test directory (usually "tests")
   - `--log-level`: For debugging MCP server issues

3. **Reference Projects** (filesystem server):
   - Enable access to related codebases for comprehensive LLM context
   - Useful for cross-repository development and learning from examples
   - Format: `--reference-project "name=${PATH_TO_REPO}"`

4. **Environment Variables**:
   - `PYTHONPATH`: Ensures Python modules are discoverable
   - Critical for proper import resolution in MCP servers

### Using MCP Configuration

**With mcp-coder commands:**
```bash
# Use specific MCP config
mcp-coder prompt "Analyze code" --mcp-config .mcp.linux.json
mcp-coder implement --mcp-config .mcp.linux.json
mcp-coder create-plan 123 --mcp-config .mcp.linux.json
```

**Benefits:**
- Enables strict mode (only configured servers)
- Consistent environment across team
- Platform-specific optimizations
- Reference projects for filesystem server (access to related codebases)

## VSCodeClaude Setup

For `mcp-coder vscodeclaude launch`, the session status file `.vscodeclaude_status.txt` should be gitignored to prevent working folders from appearing "dirty". See [repo.md](repo.md) for the centralized `.gitignore` list.

## Local Development Launchers

- **Purpose:** Use current repo's Python environment for immediate testing
- **Benefits:** Test code changes immediately, auto-activate venv, set MCP environment variables
- **Reference:** See `claude_local.bat` in this repository

## Enhanced Claude Permissions

- **Purpose:** Pre-approve safe tools while maintaining security
- **Principles:** Only allow tools that change project folder (git-tracked) or read-only commands
- **Security:** No system-wide edits, no file deletion outside project
- **Architecture Tools:** Use `./tools/` scripts for consistent UX and error handling. **For Claude Code**, prefer MCP tools: `mcp__tools-py__run_format_code`, `mcp__tools-py__run_lint_imports_check`, `mcp__tools-py__run_vulture_check`, `mcp__tools-py__get_library_source`
- **Reference:** See `.claude/settings.local.json` in this repository

## Architecture Documentation

The `/implementation_review` and `/implementation_review_supervisor` commands check code against `docs/architecture/architecture.md`. This file must exist for code reviews to work. Architecture documentation also enables LLM-assisted codebase navigation.

### Recommended Structure

```
docs/
├── README.md                              (optional)
├── architecture/
│   ├── architecture.md                    (mandatory - used by /implementation_review)
│   ├── architecture-maintenance.md
│   └── dependencies/
│       ├── readme.md
│       ├── dependency_graph.html          (generated)
│       ├── pydeps_graph.html              (generated)
│       └── pydeps_graph.dot               (generated)
└── [project-specific docs]
```

**Reference:** See this repository's own [`docs/`](..) folder for a working example of this structure.
