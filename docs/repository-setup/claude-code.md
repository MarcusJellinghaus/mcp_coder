# Claude Code Setup

MCP Coder currently uses Claude Code as the primary LLM backend, with optional langchain support for connecting to other LLM providers. This file covers the required configuration files and Claude-related repo conventions.

Installing Claude Code itself: [Claude Code Configuration](../configuration/claude-code.md).

## Required Files

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Project-specific instructions for Claude |
| `.claude/skills/` | Skills for workflow stages |
| `.mcp.json` | MCP server configuration |

In the future, these files will also be used by iCoder.

## `.claude/CLAUDE.md` - Project Instructions

> **Customize:** Tool list, project conventions, and allowed bash commands.

This file contains mandatory instructions that Claude reads at the start of every session. Use it for code quality requirements, project conventions and mandatory tool use (for example the MCP tools `run_pylint_check`, `run_pytest_check`, `run_mypy_check`). `implement` assumes Claude can read files and run the checks of the configured toolkit (for Python projects, the `mcp-tools-py` MCP tools).

Example: mcp-coder's own [CLAUDE.md](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/.claude/CLAUDE.md).

## `.claude/skills/` - Skills

> **Customize:** Repo-specific paths and commands inside individual `SKILL.md` files.

Skills provide structured workflows for common tasks. Run `mcp-coder init` to deploy skills automatically. To deploy only skills (without config creation), use `mcp-coder init --just-skills`.

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
| `/plan_review_supervisor` | Autonomous plan review (delegates to the `plan-engineer` agent) |
| `/plan_update` | Update plan files based on discussion |
| `/plan_approve` | Approve plan and transition to plan-ready |

**Implementation stage:**

| Command | Purpose |
|---------|---------|
| `/implement_direct` | Implement an issue directly |
| `/implementation_review` | Code review with compact diff analysis |
| `/implementation_review_supervisor` | Autonomous code review (delegates to the `code-engineer` agent) |
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

**PR stage:**

| Command | Purpose |
|---------|---------|
| `/pr_comment_triage` | Triage new PR comments, review threads and code-scanning alerts: fix, reply or decline, resolve threads, then return the issue to `status-10:pr-created` once no alert is open |

**Meta:**

| Command | Purpose |
|---------|---------|
| `/discuss` | Step-by-step discussion of open questions and suggestions |

## Knowledge Base & Agents

Supporting files referenced by skills. Deployed automatically by `mcp-coder init`:

- `.claude/knowledge_base/planning_principles.md` — Used by plan review skills
- `.claude/knowledge_base/refactoring_principles.md` — Used by code review skills
- `.claude/knowledge_base/software_engineering_principles.md` — Used by code review skills
- `.claude/knowledge_base/python.md` — Python-specific knowledge for code review (see [python.md](python.md)) — deployed only with the `mcp-tools-py` toolkit
- `.claude/agents/` — agents launched by the supervisor skills (wiring and permissions: [agent-permissions.md](agent-permissions.md)):
  - `issue-analyst.md` — analyses the issue (`/issue_analyse_supervisor`)
  - `issue-updater.md`, `issue-approver.md` — edit and approve the issue (`/issue_analyse_supervisor`)
  - `plan-engineer.md` — reviews and updates the plan (`/plan_review_supervisor`)
  - `code-engineer.md` — reviews and fixes the code, reports branch status (`/implementation_review_supervisor`)
  - `commit-pusher.md` — commits and pushes (`/plan_review_supervisor`, `/implementation_review_supervisor`)

## `.mcp.json` - MCP Server Configuration

> **Customize:** Server paths, project name, `--test-folder`, reference projects.

**Model Context Protocol (MCP)** enables Claude Code to use specialized servers. Two MCP servers are used with mcp-coder:

- **`mcp-workspace`** — Workspace file operations (read, write, edit, list) for the project plus optional reference projects. Installed with mcp-coder; every repo needs it.
- **`mcp-tools-py`** — Python code-quality tools (pylint, pytest, mypy, vulture, formatting, etc.). Installed by the `python` extra (`pip install "mcp-coder[python]"`); only repos with `toolkit = "mcp-tools-py"` list it in `.mcp.json`. A non-Python repo drops it — every `.mcp.json` server is fatal at session start ([Required MCP servers](../configuration/toolkits.md#required-mcp-servers)).

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

Set by the launcher scripts (`claude.bat`, `claude_local.bat`, `icoder_local.bat`) or `mcp-coder icoder` before Claude Code starts:

| Variable | Set by launcher | Purpose |
|---|---|---|
| `MCP_CODER_PROJECT_DIR` | `%CD%` (current dir) | Absolute path to your project directory |
| `MCP_CODER_VENV_PATH` | Yes | Path to the venv `Scripts/` directory containing `mcp-workspace.exe` (and `mcp-tools-py.exe` with the `python` extra) |
| `MCP_CODER_VENV_DIR` | Parent of `MCP_CODER_VENV_PATH` | The venv root |
| `VIRTUAL_ENV` | Set if no venv was active | Standard Python venv variable |

Without a launcher (e.g., running Claude Code directly), set these manually before launch.

### `mcp-tools-py` Server

Provides Python code-quality MCP tools.

**Arguments:**

- `--project-dir`: Project root (typically `${MCP_CODER_PROJECT_DIR}`)
- `--python-executable`: Python interpreter in your venv
- `--test-folder`: Test directory (usually `tests`)
- `--log-level`: Log verbosity (`DEBUG`, `INFO`)

**Required env:**

- `PYTHONPATH`: `${MCP_CODER_PROJECT_DIR}/src` — needed for src-layout imports

### `mcp-workspace` Server

Provides workspace file MCP tools (`read_file`, `save_file`, `edit_file`, `list_directory`, etc.) for files in your project, plus reference projects: their files are read-only, but their GitHub issues can be created, edited and commented on through `reference_name`.

**Arguments:**

- `--project-dir`: Project root (typically `${MCP_CODER_PROJECT_DIR}`)
- `--log-level`: Log verbosity
- `--reference-project name=<name>,path=<path>[,url=<url>]` (repeatable): Make additional repositories readable from MCP, as `.mcp.json` does. Useful for cross-repository development and learning from examples. `url` is the explicit `url=` or, when omitted, auto-detected from the checkout's git `origin`. A reference project with neither has a null `url`, so its issues can't be written and it never matches cross-repo approval. The old `name=<path>` form is skipped with a warning.

**Required env:**

- `PYTHONPATH`: `${MCP_CODER_VENV_DIR}\Lib\` — for finding installed packages

**File access rules (`.mcp-file-access`):** the server refuses gitignored paths unless a rule in the root `.mcp-file-access` exposes them, and a `read-only` rule blocks writes to committed files. `mcp-coder init` creates the file with `read-write /.scratch/` (so the gitignored `.scratch/` stays usable for probes and temp files) and `read-only` rules for `.vscodeclaude_status.txt`, `.mcp.json` and `.claude/settings*.json` — commit it. Needs mcp-workspace ≥ `f626cf8`. Details: [repo.md](repo.md#mcp-file-access-rules-mcp-file-access).

### Example for using MCP Configuration

**With mcp-coder commands:**

```bash
# Use specific MCP config
mcp-coder prompt "Analyze code" --mcp-config .mcp.json

# Pin both MCP config and Claude Code settings file
mcp-coder prompt "Analyze code" --mcp-config .mcp.json --settings .claude/settings.local.json
```

## Launcher Scripts

> **Customize:** Path to `claude.exe` if installed in a non-standard location.

Two launcher scripts are provided. Both auto-activate the venv and set the MCP environment variables before starting Claude Code:

- **`claude.bat`** — Standard launcher using the installed mcp-coder package (recommended for general use)
- **`claude_local.bat`** — Development launcher using local source, for testing changes to mcp-coder itself

Both check the tool env for `mcp-workspace.exe` and `mcp-tools-py.exe`. A missing `mcp-tools-py.exe` prints a warning ("only Python projects need it") with an install hint, and the launcher continues.

## Enhanced Claude Permissions

> **Customize:** Permissions list (`.claude/settings.local.json`) — tracked in each repo.

- **Purpose:** Pre-approve safe tools while maintaining security
- **Principles:** Only allow tools that change the project folder (git-tracked) or only read. MCP tools before Bash: allow-list the MCP tool (e.g. `mcp__mcp-workspace__git` for `git diff`), Bash only where no MCP tool exists, narrowly (e.g. `Bash(tools/jenkins_builds.sh:*)`)
- **Security:** No system-wide edits, no file deletion outside project. Never allow unrestricted `Bash(*)`
- **Reference:** `.claude/settings.local.json` in this repository. Commit it in each repo (Claude Code may list it in the global git excludes → add it once with `git add -f`). A gitignored personal layout: backlog [#1433](https://github.com/MarcusJellinghaus/mcp_coder/issues/1433)

```json
{
  "permissions": {
    "allow": [
      "mcp__mcp-workspace__read_file",
      "mcp__mcp-workspace__save_file",
      "mcp__mcp-workspace__edit_file",
      "mcp__mcp-workspace__git",
      "mcp__mcp-workspace__github_issue_view",
      "mcp__mcp-tools-py__run_format_code",
      "Skill(check_branch_status)"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["mcp-tools-py", "mcp-workspace"]
}
```

`permissions.allow` pre-approves tools. `Skill(<name>)` only matters for model-invocable skills; it does not lift `disable-model-invocation` ([agent-permissions.md](agent-permissions.md#agents-cannot-invoke-disable-model-invocation-skills)). `enableAllProjectMcpServers` and `enabledMcpjsonServers` enable the servers defined in `.mcp.json`.

The issue write tools (`github_issue_create`, `github_issue_edit`, `github_issue_comment`, `github_issue_set_status`) are deliberately left out so issue writes prompt in the main session (see [agent-permissions.md](agent-permissions.md)).

This repository commits no `.claude/settings.json` and no `deny` rules. Protected config files rest on Claude Code's built-in protection (native writes to `.mcp.json` and `.claude/` prompt), `.mcp-file-access` (MCP tools refuse writes) and git review ([design concept §3](claude-permissions/design-concept.md#3-mechanisms); deny-rule facts: [How Claude permissions work §4](claude-permissions/how-it-works.md#4-rule-evaluation)).

### Pinning the settings file with `--settings`

Claude Code reads `.claude/settings*.json` from its working directory only, no
walk-up ([How Claude permissions work §2](claude-permissions/how-it-works.md#2-settings-files)).
mcp-coder runs Claude with `cwd = --project-dir`, so your repo's files are found
whatever shell you launch from. Start interactive sessions at the repo root.

mcp-coder commands that drive Claude Code accept `--settings <path>` to
forward a settings file via Claude's native `--settings` flag; it is merged
with the cwd files, not a replacement. The file is not limited to
permissions — it also controls `enabledMcpjsonServers`, `hooks`, `env`,
`model`, `outputStyle`, and the rest of the Claude Code settings schema.

```bash
# Force Claude to use the repo's settings file regardless of cwd
mcp-coder prompt "Analyze code" \
    --mcp-config .mcp.json \
    --settings .claude/settings.local.json
```

With no `--settings` argument, mcp-coder auto-detects
`<project_dir>/.claude/settings.local.json` then
`<project_dir>/.claude/settings.json`. Set a default via
`MCP_CODER_CLAUDE_SETTINGS` or `[claude] default_settings_path` in
`config.toml`. See [Configuration Guide](../configuration/config.md#claude)
for the full resolution chain.

#### Both settings files apply

`--settings` pins **one** file, and mcp-coder passes only one — its
auto-detection prefers `settings.local.json` when both exist. Claude
*additionally* discovers `<project_dir>/.claude/settings.json` and
`.claude/settings.local.json` from its cwd and **merges** them with the
pinned file. A repo holding both files gets both: review a checked-in
`settings.json` for entries you don't want in effect (stale `hooks`, a pinned
`model`, permissive `permissions`).

The copilot provider anchors the same way: `_read_settings_allow` in
`llm/providers/copilot/copilot_cli.py` reads
`<cwd>/.claude/settings.local.json` — the driven project's file, not the
launching shell's.

## Architecture Documentation

> **Customize:** Write your own `docs/architecture/architecture.md` — required by `/implementation_review`.

The `/implementation_review` and `/implementation_review_supervisor` commands check code against `docs/architecture/architecture.md`. This file must exist for code reviews to work. Architecture documentation also enables LLM-assisted codebase navigation.

### Recommended Structure

```
docs/
├── README.md                              (optional)
├── architecture/
│   ├── architecture.md                    (mandatory - used by /implementation_review)
│   ├── architecture-maintenance.md        (optional - when to update architecture.md)
│   └── dependencies/
│       ├── readme.md
│       ├── dependency_graph.html          (generated)
│       ├── pydeps_graph.html              (generated)
│       └── pydeps_graph.dot               (generated)
└── [project-specific docs]
```

**Reference:** See this repository's own [`docs/`](..) folder for a working example of this structure.
