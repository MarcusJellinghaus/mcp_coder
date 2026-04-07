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

- [ ] Configure GitHub token in user config
- [ ] Set up workflow labels with `mcp-coder gh-tool define-labels`
- [ ] Install GitHub Actions workflows
- [ ] Configure Claude Code files (`.claude/`, `.mcp.json`)
- [ ] Test workflow with a sample issue
- [ ] Create `docs/architecture/architecture.md` (required by `/implementation_review` and `/implementation_review_supervisor`)

## Detail Documentation

| Topic | File |
|---|---|
| GitHub-side: tokens, labels, actions, CI, dependabot | [github.md](github.md) |
| Claude Code: `.claude/`, `.mcp.json`, launchers, VSCodeClaude | [claude-code.md](claude-code.md) |
| Architecture enforcement, linters, file size, dev tools | [code-quality.md](code-quality.md) |
| Repo conventions: `.gitattributes`, `pyproject.toml`, `.gitignore` | [repo.md](repo.md) |

## Files Shared With Other Projects

The following files in this repository serve as references/templates for other projects adopting MCP Coder workflows. Use this as a quick map of what to copy and what to adjust.

| File / Folder | Mandatory? | Copy as-is? | What to adjust |
|---|---|---|---|
| `.claude/CLAUDE.md` | Yes | No | Project conventions, tool list, allowed commands |
| `.claude/skills/` | Yes | Mostly | Repo-specific paths/commands inside individual SKILL.md files |
| `.mcp.json` (+ `.mcp.{linux,windows,macos}.json`) | Yes | No | Server paths, project name, `--test-folder`, reference projects |
| `.github/workflows/label-new-issues.yml` | Yes | Yes | — |
| `.github/workflows/approve-command.yml` | Yes | Yes | — |
| `docs/architecture/architecture.md` | Yes | No | Write your own — required by `/implementation_review` |
| `workflows/config/labels.json` | No | No | Only if customizing default labels |
| `.github/workflows/ci.yml` | No | No | Python version, package name, test paths |
| `.importlinter` | No | No | Package names, contract definitions |
| `tach.toml` | No | No | Module boundaries for your package |
| `vulture_whitelist.py` | No | No | Project-specific false positives |
| `.large-files-allowlist` | No | No | Files exempt from size limits |
| `pyproject.toml` | No | No | Use as a dependency/config reference, not a copy |
| `.gitattributes` | No | Yes | — |
| `.github/dependabot.yml` | No | Yes | — |
| `claude_local.bat` / `claude.bat` | No | Mostly | Path to `claude.exe` if non-standard |
| `.claude/settings.local.json` | No | Mostly | Permissions list — gitignored in downstream projects |
| `tools/format_all.{sh,bat}` | No | Yes | — |
| `tools/lint_imports.{sh,bat}`, `tach_check.*`, `pycycle_check.*`, `vulture_check.*` | No | Yes | — |
| `tools/ruff_check.{sh,bat}` | No | Yes | — |

**Notes:**

- **Mandatory** = required for MCP Coder workflows to function. **Optional** files enhance the workflow but are not required.
- **Copy as-is = Yes** means the file works in any project without edits. **Mostly** means small path tweaks may be needed. **No** means the file is project-specific and must be authored or adapted.
- There is currently no sync/versioning mechanism — when files in this repo change, downstream projects must re-pull manually.

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

### Troubleshooting

**Labels not appearing:**
- Check GitHub token permissions
- Verify config file location and format
- Run with `--dry-run` first

**GitHub Actions not working:**
- Check repository permissions (Settings → Actions → General)
- Verify YAML syntax in workflow files
- Check Actions tab for error messages

**MCP servers not working:**
- Verify server installation (`pip list | grep mcp`)
- Check file paths in configuration
- Test servers independently

**Claude Code not following instructions:**
- Verify `.claude/CLAUDE.md` exists and is readable
- Check for syntax errors in the file
- Ensure instructions are clear and unambiguous

## Related Documentation

- **[Claude Code Configuration](../configuration/claude-code.md)** - Detailed Claude Code setup, CLI commands, troubleshooting
- **[CLI Reference](../cli-reference.md)** - Complete mcp-coder command documentation
- **[Configuration Guide](../configuration/config.md)** - User and system configuration
- **[Development Process](../processes-prompts/development-process.md)** - Complete workflow methodology
- **[Claude Code Cheat Sheet](../processes-prompts/claude_cheat_sheet.md)** - Slash command reference
