# Claude Code Setup

MCP Coder currently uses Claude Code as the primary LLM backend, with optional langchain support for connecting to other LLM providers. This file covers the required configuration files and Claude-related repo conventions.

**See [Claude Code Configuration Guide](../configuration/claude-code.md)** for detailed setup including installation, CLI commands, and troubleshooting.

## Required Files

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Project-specific instructions for Claude |
| `.claude/skills/` | Skills for workflow stages |
| `.mcp.json` | MCP server configuration |

In the future, these files will also be used by iCoder.

## `.claude/CLAUDE.md` - Project Instructions

> **To be adjusted / customized:** Tool list, project conventions, and allowed bash commands.

This file contains mandatory instructions that Claude follows when working on your project. Create `.claude/CLAUDE.md` with project-specific rules.

**See:**

- [Claude Code Configuration Guide](../configuration/claude-code.md#claudeclaudemd---project-instructions) for detailed examples
- mcp-coder's own [CLAUDE.md](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/.claude/CLAUDE.md) for a comprehensive example

## `.claude/skills/` - Skills

> **To be adjusted / customized:** Repo-specific paths and commands inside individual `SKILL.md` files.

Skills provide structured workflows for common tasks. Copy the skills from mcp-coder or create your own.

**Available commands** (see [Claude Code Cheat Sheet](../processes-prompts/claude_cheat_sheet.md) for details):

**Issue stage:**

| Command | Purpose |
|---------|---------|
| `/issue_create` | Create a new GitHub issue from discussion context |
| `/issue_analyse` | Analyse issue requirements, feasibility, and approaches |
| `/issue_requirements` | Refocus discussion on open requirements |
| `/issue_update` | Update issue with refined content from analysis |
| `/issue_approve` | Approve issue and transition to next status |

**Plan stage:**

| Command | Purpose |
|---------|---------|
| `/plan_review` | Review implementation plan for completeness, simplicity, risks |
| `/plan_review_supervisor` | Autonomous plan review (delegates to subagents) |
| `/plan_update` | Update plan files based on discussion |
| `/plan_approve` | Approve plan and transition to plan-ready |

**Implementation stage:**

| Command | Purpose |
|---------|---------|
| `/implement_direct` | Implement an issue directly |
| `/implementation_review` | Code review with compact diff analysis |
| `/implementation_review_supervisor` | Autonomous code review (delegates to engineer subagents) |
| `/implementation_needs_rework` | Return issue to plan-ready after major review issues |
| `/implementation_new_tasks` | Add implementation steps after review findings |
| `/implementation_finalise` | Complete remaining unchecked tasks in tracker |
| `/implementation_approve` | Approve implementation, transition to PR-ready |

**Branch operations:**

| Command | Purpose |
|---------|---------|
| `/check_branch_status` | Check CI, rebase needs, tasks, labels |
| `/commit_push` | Format, commit, and push changes |
| `/rebase` | Rebase feature branch onto base branch with conflict resolution |

**Meta:**

| Command | Purpose |
|---------|---------|
| `/discuss` | Step-by-step discussion of open questions and suggestions |

## Knowledge Base & Agents

Supporting files referenced by skills. Copy as-is to downstream repos:

- `.claude/knowledge_base/planning_principles.md` — Used by plan review skills
- `.claude/knowledge_base/refactoring_principles.md` — Used by code review skills
- `.claude/knowledge_base/software_engineering_principles.md` — Used by code review skills
- `.claude/knowledge_base/python.md` — Python-specific knowledge for code review (see [python.md](python.md))
- `.claude/agents/commit-pusher.md` — Workflow agent referenced by `/commit_push`

## `.mcp.json` - MCP Server Configuration

> **To be adjusted / customized:** Server paths, project name, `--test-folder`, reference projects.

**Model Context Protocol (MCP)** enables Claude Code to use specialized servers. mcp-coder ships with two MCP servers:

- **`mcp-tools-py`** — Python code-quality tools (pylint, pytest, mypy, vulture, isort+black, etc.)
- **`mcp-workspace`** — Workspace file operations (read, write, edit, list) for the project plus optional reference projects

### Platform-Specific Configuration

MCP Coder supports platform-specific MCP configuration files:

| Platform | Config File |
|----------|-------------|
| **Linux** | `.mcp.linux.json` |
| **Windows** | `.mcp.windows.json` |
| **macOS** | `.mcp.macos.json` |
| **Generic** | `.mcp.json` |

**File location:** Project root directory.

**Reference Implementation:** See this repository's `.mcp.json` for a complete working configuration.

**Path conventions:**

- **Windows**: Use double backslashes (`\\`) and `.exe` extensions
- **Unix**: Use forward slashes, no extensions

### Environment Variables

Set by the launcher scripts (`claude.bat`, `claude_local.bat`, `icoder.bat`, `icoder_local.bat`) before Claude Code starts:

| Variable | Set by launcher | Purpose |
|---|---|---|
| `MCP_CODER_PROJECT_DIR` | `%CD%` (current dir) | Absolute path to your project directory |
| `MCP_CODER_VENV_PATH` | Yes | Path to the venv `Scripts/` directory containing `mcp-tools-py.exe` and `mcp-workspace.exe` |
| `MCP_CODER_VENV_DIR` | Parent of `MCP_CODER_VENV_PATH` | The venv root |
| `VIRTUAL_ENV` | Set if no venv was active | Standard Python venv variable |

Without a launcher (e.g., running Claude Code directly), set these manually before launch.

### `mcp-tools-py` Server

Provides Python code-quality MCP tools.

**Arguments:**

- `--project-dir`: Project root (typically `${MCP_CODER_PROJECT_DIR}`)
- `--python-executable`: Python interpreter in your venv
- `--venv-path`: Virtual environment root
- `--test-folder`: Test directory (usually `tests`)
- `--log-level`: Log verbosity (`DEBUG`, `INFO`)

**Required env:**

- `PYTHONPATH`: `${MCP_CODER_PROJECT_DIR}/src` — needed for src-layout imports

### `mcp-workspace` Server

Provides workspace file MCP tools (`read_file`, `save_file`, `edit_file`, `list_directory`, etc.) for files in your project, plus optional read-only access to reference projects.

**Arguments:**

- `--project-dir`: Project root (typically `${MCP_CODER_PROJECT_DIR}`)
- `--log-level`: Log verbosity
- `--reference-project name=<path>` (repeatable): Make additional repositories readable from MCP. Useful for cross-repository development and learning from examples.

**Required env:**

- `PYTHONPATH`: `${MCP_CODER_VENV_DIR}\Lib\` — for finding installed packages

### Example for using MCP Configuration

**With mcp-coder commands:**

```bash
# Use specific MCP config
mcp-coder prompt "Analyze code" --mcp-config .mcp.json
```

## Launcher Scripts

> **To be adjusted / customized:** Path to `claude.exe` if installed in a non-standard location.

Two launcher scripts are provided. Both auto-activate the venv and set the MCP environment variables before starting Claude Code:

- **`claude.bat`** — Standard launcher using the installed mcp-coder package (recommended for general use)
- **`claude_local.bat`** — Development launcher using local source, for testing changes to mcp-coder itself

## Enhanced Claude Permissions

> **To be adjusted / customized:** Permissions list (`.claude/settings.local.json`) — gitignore this file in downstream repos.

- **Purpose:** Pre-approve safe tools while maintaining security
- **Principles:** Only allow tools that change project folder (git-tracked) or read-only commands
- **Security:** No system-wide edits, no file deletion outside project
- **Reference:** See `.claude/settings.local.json` in this repository

## Architecture Documentation

> **To be adjusted / customized:** Write your own `docs/architecture/architecture.md` — required by `/implementation_review`.

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
