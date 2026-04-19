# Repository Setup Guide

Complete guide for setting up repositories to use MCP Coder development workflows.

## Overview

This guide covers the **mandatory** and **optional** components for integrating MCP Coder workflows into your repository.

**Mandatory** - Required for MCP Coder workflows to function:
- GitHub token configuration
- Workflow status labels
- GitHub Actions for automation
- Claude Code configuration

**Optional** - Enhance your development workflow:
- Architecture enforcement tools
- Code quality CI checks
- Development convenience scripts

## Quick Setup Checklist

- [ ] Configure GitHub token in user config (`~/.mcp_coder/config.toml` — see [Configuration Guide](../configuration/config.md))
- [ ] Set up workflow labels with `mcp-coder gh-tool define-labels`
- [ ] Install GitHub Actions workflows (or generate with `mcp-coder gh-tool define-labels --generate-github-actions`)
- [ ] Deploy Claude skills with `mcp-coder init`
- [ ] Configure Claude Code files (`.claude/CLAUDE.md`, `.mcp.json`)
- [ ] Test workflow with a sample issue
- [ ] Create `docs/architecture/architecture.md` (required by `/implementation_review` and `/implementation_review_supervisor`)

## Detail Documentation

| Topic | File | Applies to |
|---|---|---|
| GitHub-side: tokens, labels, actions, CI, dependabot | [github.md](github.md) | Any downstream repo |
| Claude Code: `.claude/`, `.mcp.json`, launchers, architecture docs | [claude-code.md](claude-code.md) | Any downstream repo |
| Copilot CLI: file compatibility, Copilot-specific flags | [copilot.md](copilot.md) | Any downstream repo |
| Generic repo conventions: `.gitattributes`, `.gitignore`, file size | [repo.md](repo.md) | Any downstream repo |
| Python-specific: `pyproject.toml`, linters, formatters, architecture enforcement | [python.md](python.md) | Python downstream repos only |
| mcp-coder repo internals: design docs, mlflow tools, internal scripts | [internal.md](internal.md) | Not for downstream use |
| Legacy / to-be-reviewed files | [to-be-reviewed.md](to-be-reviewed.md) | Not for downstream use |

## Files Shared With Other Projects

The following files in this repository serve as references/templates for other projects adopting MCP Coder workflows. The **Category** column tells you whether a file applies to your project.

**Categories:**
- **G** = General — applies to any downstream repo using mcp-coder
- **P** = Python — only applies to Python downstream projects
- **I** = Internal — used in mcp-coder repo only, not for downstream use
- **L** = Legacy / to-be-reviewed

| File / Folder | Cat | Mandatory? | Copy as-is? | What to adjust |
|---|---|---|---|---|
| `.claude/CLAUDE.md` | G | Yes | No | Project conventions, tool list, allowed commands |
| `.claude/skills/` | G | Yes | Mostly | Repo-specific paths/commands inside individual SKILL.md files |
| `.claude/agents/commit-pusher.md` | G | No | Yes | — |
| `.claude/knowledge_base/planning_principles.md` | G | No | Yes | — |
| `.claude/knowledge_base/refactoring_principles.md` | G | No | Yes | — |
| `.claude/knowledge_base/software_engineering_principles.md` | G | No | Yes | — |
| `.claude/knowledge_base/python.md` | P | No | Yes | — |
| `.claude/settings.local.json` | G | No | Mostly | Permissions list — gitignored in downstream projects |
| `.mcp.json` (+ `.mcp.{linux,windows,macos}.json`) | G | Yes | No | Server paths, project name, `--test-folder`, reference projects |
| `.github/workflows/label-new-issues.yml` | G | Yes | Yes | — |
| `.github/workflows/approve-command.yml` | G | Yes | Yes | — |
| `.github/workflows/ci.yml` | P | No | No | Python version, package name, test paths |
| `.github/dependabot.yml` | G | No | Yes | — |
| `.gitattributes` | G | No | Yes | — |
| `.large-files-allowlist` | G | No | No | Files exempt from size limits |
| `claude_local.bat` / `claude.bat` | G | No | Mostly | Path to `claude.exe` if non-standard |
| `docs/architecture/architecture.md` | G | Yes | No | Write your own — required by `/implementation_review` |
| `pyproject.toml` | P | No | No | Use as a dependency/config reference, not a copy |
| `.python-version` | P | No | No | Pin to your Python version |
| `.importlinter` | P | No | No | Package names, contract definitions |
| `tach.toml` | P | No | No | Module boundaries for your package |
| `vulture_whitelist.py` | P | No | No | Project-specific false positives |
| `tools/format_all.{sh,bat}` | P | No | Yes | — |
| `tools/lint_imports.{sh,bat}`, `tach_check.*`, `pycycle_check.*`, `vulture_check.*` | P | No | Yes | — |
| `tools/ruff_check.{sh,bat}` | P | No | Yes | — |
| `icoder_local.bat` | I | — | — | mcp-coder repo only |
| `mlflow_implementation.md` / `project_idea.md` | I | — | — | mcp-coder repo only |
| `tools/start_mlflow.*`, `get_*mlflow*.py`, `inspect_mlflow_run.py`, `search_mlflow_artifacts.py` | I | — | — | mcp-coder repo only |
| `tools/reinstall_local.bat`, `read_github_deps.py`, `safe_delete_folder.py` | I | — | — | mcp-coder repo only |
| `.run/` | I | — | — | IDE configs, mcp-coder repo only |
| `.github/workflows/langchain-integration.yml` | I | — | — | mcp-coder repo only |
| `.github/workflows/publish.yml` | I | — | — | mcp-coder repo only |
| `tools/commit_summary.bat`, `pr_summary.bat`, `pr_review.bat`, `pr_review_highlevel.bat` | L | — | — | Legacy |
| `tools/check_version.bat`, `test_prompt.bat`, `docstring_stats.sh`, `debug_*.py` | L | — | — | To review |
| `requirements-beta.txt` | L | — | — | To review |

**Notes:**

- **Mandatory** = required for MCP Coder workflows to function. **Optional** files enhance the workflow but are not required.
- **Copy as-is = Yes** means the file works in any project without edits. **Mostly** means small path tweaks may be needed. **No** means the file is project-specific and must be authored or adapted.
- Skills, knowledge base, and agents are deployed via `mcp-coder init`. Re-run `mcp-coder init` after upgrading mcp-coder — existing files are never overwritten (delete a file first to refresh it). Other files must be re-pulled manually.

## Testing Your Setup

### Verification Steps

**1. Test label creation:**
```bash
mcp-coder gh-tool define-labels --dry-run
# Should show configured labels
```

**2. Test issue automation:**
- Create a new issue in GitHub
- Verify it gets `status-01:created` label automatically
- Comment `/approve` on the issue
- Verify it promotes to `status-02:awaiting-planning`

**3. Test MCP integration:**
```bash
mcp-coder prompt "List files in src/" --mcp-config .mcp.json
```

## Related Documentation

- **[Claude Code Configuration](../configuration/claude-code.md)** - Detailed Claude Code setup, CLI commands, troubleshooting
- **[Copilot CLI Setup](copilot.md)** - GitHub Copilot CLI file compatibility and configuration
- **[CLI Reference](../cli-reference.md)** - Complete mcp-coder command documentation
- **[Configuration Guide](../configuration/config.md)** - User and system configuration
- **[Development Process](../processes-prompts/development-process.md)** - Complete workflow methodology
- **[Claude Code Cheat Sheet](../processes-prompts/claude_cheat_sheet.md)** - Slash command reference
