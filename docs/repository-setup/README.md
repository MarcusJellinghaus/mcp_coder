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
| GitHub-side: tokens, labels, actions, CI, badges, dependabot | [github.md](github.md) | Any target repo |
| Jenkins: API user permissions, credentials, coordinator job setup | [jenkins.md](jenkins.md) | Repos dispatched by the coordinator |
| Claude Code: `.claude/`, `.mcp.json`, launchers, architecture docs | [claude-code.md](claude-code.md) | Any target repo |
| Agent permissions: how `.claude/agents/*.md` are wired, and what `bypassPermissions` does and does not enforce | [agent-permissions.md](agent-permissions.md) | Any target repo — reference only, `mcp-coder init` does not deploy `docs/` |
| Copilot CLI: file compatibility, Copilot-specific flags | [copilot.md](copilot.md) | Any target repo |
| Generic repo conventions: `.gitattributes`, `.gitignore`, file size | [repo.md](repo.md) | Any target repo |
| Python-specific: `pyproject.toml`, linters, formatters, architecture enforcement | [python.md](python.md) | Python target repos only |
| Quality and security checks: which automated checks run, and why | [quality-and-security-checks.md](quality-and-security-checks.md) | Not for target repos |
| mcp-coder repo internals: design docs, mlflow tools, internal scripts | [internal.md](internal.md) | Not for target repos |

## Files Shared With Other Projects

The following files in this repository serve as references/templates for other projects adopting MCP Coder workflows. The **Category** column tells you whether a file applies to your project.

**Categories:**
- **G** = General — applies to any target repo using mcp-coder
- **P** = Python — only applies to Python target repos
- **I** = Internal — used in mcp-coder repo only, not for target repos

| File / Folder | Cat | Mandatory? | Copy as-is? | What to adjust |
|---|---|---|---|---|
| `.claude/CLAUDE.md` | G | Yes | No | Project conventions, tool list, allowed commands |
| `.claude/skills/` | G | Yes | Mostly | Repo-specific paths/commands inside individual SKILL.md files |
| `.claude/agents/commit-pusher.md` | G | No | Yes | — |
| `.claude/agents/issue-updater.md` | G | No | Yes | — |
| `.claude/agents/issue-approver.md` | G | No | Yes | Requires `mcp-coder` on PATH and the status labels; `approve-command.yml` only for cross-repo approval |
| `.claude/knowledge_base/planning_principles.md` | G | No | Yes | — |
| `.claude/knowledge_base/refactoring_principles.md` | G | No | Yes | — |
| `.claude/knowledge_base/software_engineering_principles.md` | G | No | Yes | — |
| `.claude/knowledge_base/python.md` | P | No | Yes | — |
| `.claude/settings.local.json` | G | No | Mostly | Permissions list — tracked in the target repo; the permission entries differ per repo |
| `.mcp.json` (+ `.mcp.{linux,windows,macos}.json`) | G | Yes | No | Server paths, project name, `--test-folder`, reference projects |
| `.github/workflows/label-new-issues.yml` | G | Yes | Yes | — |
| `.github/workflows/approve-command.yml` | G | Yes | Yes | — |
| `.github/workflows/ci.yml` | P | No | No | Python version, package name, test paths, coverage badge filename (`<repo>-coverage.json`) |
| `.github/dependabot.yml` | G | No | Yes | — |
| `.github/workflows/scorecard.yml` | G | No | Yes | — |
| `SECURITY.md` | G | No | No | Adjust contact and scope |
| `.gitattributes` | G | No | Yes | — |
| `.large-files-allowlist` | G | No | No | Files exempt from size limits |
| `claude_local.bat` / `claude.bat` | G | No | Mostly | Path to `claude.exe` if non-standard |
| `docs/architecture/architecture.md` | G | Yes | No | Write your own — required by `/implementation_review` |
| `pyproject.toml` | P | No | No | Use as a dependency/config reference, not a copy |
| `.python-version` | P | No | No | Pin to your Python version |
| `.importlinter` | P | No | No | Package names, contract definitions |
| `tach.toml` | P | No | No | Module boundaries for your package |
| `vulture_whitelist.py` | P | No | No | Project-specific false positives |
| `tools/lint_imports.{sh,bat}`, `tach_check.*`, `vulture_check.*` | P | No | Yes | — |
| `tools/ruff_check.{sh,bat}` | P | No | Yes | — |
| `icoder_local.bat` | I | — | — | mcp-coder repo only |
| `mlflow_implementation.md` / `project_idea.md` | I | — | — | mcp-coder repo only |
| `tools/mlflow/*` (start_mlflow, get_*mlflow*, inspect/search, extract/analyze permission events) | I | — | — | mcp-coder repo only |
| `tools/reinstall_local.*`, `tools/read_github_deps.py`, `tools/safe_delete_folder.py` | I | — | — | mcp-coder repo only |
| `.run/` | I | — | — | IDE configs, mcp-coder repo only |
| `.github/workflows/langchain-integration.yml` | I | — | — | mcp-coder repo only |
| `.github/workflows/publish.yml` | I | — | — | mcp-coder repo only |

**Notes:**

- **Mandatory** = required for MCP Coder workflows to function. **Optional** files enhance the workflow but are not required.
- **Copy as-is = Yes** means the file works in any project without edits. **Mostly** means small path tweaks may be needed. **No** means the file is project-specific and must be authored or adapted.
- Skills, knowledge base, and agents are deployed via `mcp-coder init`. Re-run `mcp-coder init` after upgrading mcp-coder — existing files are never overwritten (delete a file first to refresh it). Other files must be re-pulled manually.

## Target-Repo Contracts

What a repo must declare about itself to be installed into and driven by mcp-coder. `validate_target_repo` checks all five rows at VSCodeClaude launch.

| Contract | Declared / enforced by | Fails how |
|---|---|---|
| ships `.mcp.json` (+ `.mcp.linux.json` on POSIX) | `workspace._MCP_CONFIG_FILES`, `validate_mcp_json` | `FileNotFoundError` at launch — fatal |
| extras to install | `[tool.mcp-coder.install] extras`, default `dev` | `uv sync` error — warn |
| `[tool.mcp-coder.install-from-github]` for sibling pinning | `pyproject_config.get_github_install_config` | silently no overrides — warn |
| venv at `<repo>/.venv` | installer, `uv sync`, `session_setup` | two venvs / empty venv — warn |
| post-install checks | `[tool.mcp-coder.install] post_install_checks`, optional | install exits 1; malformed value warned at launch |

A `uv.lock` is **not** required — mcp_coder itself tracks none, so `uv sync` resolves fresh.

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

# Optionally pin the Claude Code settings file too
mcp-coder prompt "List files in src/" --mcp-config .mcp.json --settings .claude/settings.local.json
```

## Related Documentation

- **[Claude Code Configuration](../configuration/claude-code.md)** - Detailed Claude Code setup, CLI commands, troubleshooting
- **[Copilot CLI Setup](copilot.md)** - GitHub Copilot CLI file compatibility and configuration
- **[CLI Reference](../cli-reference.md)** - Complete mcp-coder command documentation
- **[Configuration Guide](../configuration/config.md)** - User and system configuration
- **[Development Process](../processes-prompts/development-process.md)** - Complete workflow methodology
- **[Claude Code Cheat Sheet](../processes-prompts/claude_cheat_sheet.md)** - Slash command reference
