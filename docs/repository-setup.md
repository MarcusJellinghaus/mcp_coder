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

---

# Mandatory Setup

## Quick Setup Checklist

- [ ] Configure GitHub token in user config
- [ ] Set up workflow labels with `mcp-coder define-labels`
- [ ] Install GitHub Actions workflows
- [ ] Configure Claude Code files (`.claude/`, `.mcp.json`)
- [ ] Test workflow with a sample issue

## GitHub Token Configuration

The workflow automation requires a GitHub token configured in your user config file.

**Config file locations:**

| Platform | Config Path |
|----------|-------------|
| **Linux/macOS** | `~/.mcp_coder/config.toml` |
| **Windows** | `%USERPROFILE%\.mcp_coder\config.toml` |

**Token configuration:**

```toml
[github]
token = "ghp_your_github_token_here"
```

**Required permissions:**
- `repo` scope (for private repositories)
- `public_repo` scope (for public repositories)

**How to create a GitHub token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic) with appropriate repo permissions
3. Copy token and add to config file

## Workflow Labels Setup

### About Status Labels

MCP Coder uses **status labels** to track issues through their development lifecycle:

```
status-01:created → status-02:awaiting-planning → ... → status-10:pr-created
```

**Benefits:**
- Visual pipeline tracking in GitHub Issues
- Automated status progression with `/approve` command
- No issues lost without status tracking
- Team visibility into work progress

### Setting Up Labels

**1. Preview labels:**
```bash
mcp-coder define-labels --dry-run  # Preview changes
```

**2. Apply labels:**
```bash
mcp-coder define-labels            # Create/update labels
```

**3. Verify in GitHub:**
- Go to your repository → Issues → Labels
- Confirm status labels are created with correct colors

### Customizing Labels

**Default label source:** Uses `mcp_coder/config/labels.json` from the package.

**Custom labels:** Create `workflows/config/labels.json` in your project:

```bash
# Create config directory
mkdir -p workflows/config

# Create custom labels file
cat > workflows/config/labels.json << 'EOF'
[
  {
    "name": "status-01:created", 
    "color": "d4c5f9",
    "description": "Issue created, awaiting triage"
  },
  {
    "name": "status-02:awaiting-planning",
    "color": "c5def5", 
    "description": "Ready for planning phase"
  }
]
EOF
```

**Test custom config:**
```bash
mcp-coder define-labels --dry-run  # Preview your custom labels
```

## Base Branch Support for Issues

### Overview

Issues can specify a base branch to start work from a branch other than the repository default. This is useful for:
- **Hotfixes**: Starting from a release branch
- **Feature chains**: Building on existing feature work
- **Release preparation**: Working from release branches

### Issue Body Format

Add a `### Base Branch` section to your issue body:

```markdown
### Base Branch

feature/existing-work

### Description

The actual issue content...
```

### Parsing Rules

- **Case-insensitive**: `Base Branch`, `base branch`, `BASE BRANCH` all work
- **Any heading level**: `#`, `##`, `###` all work
- **Single line only**: Multiple lines will cause an error
- **Whitespace trimmed**: Leading/trailing whitespace is ignored
- **Empty = default**: If section is empty or missing, uses repository default branch

### Validation

The base branch is validated at branch creation time:
- If the branch doesn't exist, branch creation fails with a clear error
- The `/issue_analyse` command will warn if the specified branch doesn't exist

### Backward Compatibility

Existing issues without a `### Base Branch` section continue to work as before, using the repository's default branch (typically `main` or `master`).

### Example Issues

**Issue with base branch:**
```markdown
### Base Branch

release/2.0

### Description

Fix critical bug in release 2.0

### Acceptance Criteria

- Bug is fixed
- Tests pass
```

**Issue without base branch (uses default):**
```markdown
### Description

Add new feature to main branch

### Acceptance Criteria

- Feature works
- Tests pass
```

## GitHub Actions Setup

### Required Actions

Set up these two workflows for full automation:

#### 1. Auto-Label New Issues

Create `.github/workflows/label-new-issues.yml`:

```yaml
name: Label New Issues

on:
  issues:
    types: [opened]

jobs:
  add-label:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Add status label
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: ['status-01:created']
            });
```

**Purpose:** Automatically adds `status-01:created` label to new issues.

#### 2. Approve Command Handler

Create `.github/workflows/approve-command.yml`:

```yaml
name: Approve Command

on:
  issue_comment:
    types: [created]

jobs:
  handle-approve:
    runs-on: ubuntu-latest
    if: github.event.issue.pull_request == null && contains(github.event.comment.body, '/approve')
    permissions:
      issues: write
    steps:
      - name: Handle approve command
        uses: actions/github-script@v7
        with:
          script: |
            const comment = context.payload.comment.body.trim();
            if (comment !== '/approve') return;
            
            const issue = context.payload.issue;
            const labels = issue.labels.map(l => l.name);
            
            const promotions = {
              'status-01:created': 'status-02:awaiting-planning',
              'status-04:plan-review': 'status-05:plan-ready', 
              'status-07:code-review': 'status-08:ready-pr'
            };
            
            for (const [currentStatus, nextStatus] of Object.entries(promotions)) {
              if (labels.includes(currentStatus)) {
                await github.rest.issues.removeLabel({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  name: currentStatus
                }).catch(() => {});
                
                await github.rest.issues.addLabels({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  labels: [nextStatus]
                });
                
                await github.rest.issues.createComment({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  body: `✅ Status promoted: \`${currentStatus}\` → \`${nextStatus}\``
                });
                return;
              }
            }
            
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: issue.number,
              body: `⚠️ Cannot promote. Issue needs status: \`status-01:created\`, \`status-04:plan-review\`, or \`status-07:code-review\``
            });
```

**Purpose:** Handles `/approve` comments to promote issues through workflow stages.

### Installing Actions

```bash
# 1. Create directories
mkdir -p .github/workflows

# 2. Add workflow files (copy YAML content above)

# 3. Commit and push
git add .github/workflows/
git commit -m "Add GitHub Actions for issue workflow automation"
git push
```

**Verify in GitHub:** Go to repository → Actions tab → Confirm workflows appear.

## Claude Code Configuration

MCP Coder currently uses Claude Code as the LLM backend. This section covers the required configuration files.

> **Note:** Future versions may support additional LLM providers.
> 
> **See [Claude Code Configuration Guide](configuration/claude-code.md)** for detailed setup including installation, CLI commands, and troubleshooting.

### Required Files

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Project-specific instructions for Claude |
| `.claude/commands/` | Slash commands for workflow stages |
| `.mcp.json` | MCP server configuration |

### `.claude/CLAUDE.md` - Project Instructions

This file contains mandatory instructions that Claude follows when working on your project. Create `.claude/CLAUDE.md` with project-specific rules.

**See:**
- [Claude Code Configuration Guide](configuration/claude-code.md#claudeclaudemd---project-instructions) for detailed examples
- mcp-coder's own [CLAUDE.md](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/.claude/CLAUDE.md) for a comprehensive example

### `.claude/commands/` - Slash Commands

Slash commands provide structured workflows for common tasks. Copy the commands from mcp-coder or create your own.

**Available commands** (see [Claude Code Cheat Sheet](processes-prompts/claude_cheat_sheet.md) for details):

| Command | Purpose |
|---------|---------|
| `/issue_analyse` | Analyze GitHub issue requirements |
| `/plan_review` | Review implementation plan |
| `/plan_approve` | Approve plan for implementation |
| `/implementation_review` | Code review |
| `/commit_push` | Format, commit, and push changes |
| `/rebase` | Rebase branch onto main |

### `.mcp.json` - MCP Server Configuration

**Model Context Protocol (MCP)** enables Claude Code to use specialized servers for enhanced functionality:

- **code-checker**: Pylint, pytest, mypy integration
- **filesystem**: Enhanced file operations
- **Custom servers**: Project-specific tools

#### Platform-Specific Configuration

MCP Coder supports platform-specific MCP configuration files:

| Platform | Config File |
|----------|-------------|
| **Linux** | `.mcp.linux.json` |
| **Windows** | `.mcp.windows.json` |
| **macOS** | `.mcp.macos.json` |
| **Generic** | `.mcp.json` |

**File location:** Project root directory

#### Basic MCP Configuration

Create `.mcp.json` (or platform-specific variant) in your project root:

```json
{
  "mcpServers": {
    "code-checker": {
      "type": "stdio",
      "command": "mcp-code-checker",
      "args": [
        "--project-dir", "${MCP_CODER_PROJECT_DIR}",
        "--python-executable", "${MCP_CODER_VENV_DIR}/bin/python",
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
      "command": "mcp-server-filesystem",
      "args": [
        "--project-dir", "${MCP_CODER_PROJECT_DIR}",
        "--log-level", "INFO"
      ]
    }
  }
}
```

#### Using MCP Configuration

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

#### Gitignore MCP Files

Add to `.gitignore` if configs contain sensitive paths:
```gitignore
# MCP configuration files (may contain sensitive paths)
.mcp.*.json
```

---

# Optional Setup

These components enhance your development workflow but are not required for MCP Coder to function.

## Architecture Enforcement

Enforce module boundaries and prevent architectural drift. These tools are checked by CI but have no explicit mcp-coder integration.

### Import Linter

Enforces architectural contracts for imports between modules.

**Configuration:** Create `.importlinter` in project root:

```ini
[importlinter]
root_packages = your_package
root_package_paths = src

[importlinter:contract:layers]
name = Layered Architecture
type = layers
layers =
    your_package.cli
    your_package.services
    your_package.utils
```

**Run locally:**
```bash
# Linux/macOS
./tools/lint_imports.sh

# Windows
tools\lint_imports.bat
```

**Or directly:**
```bash
lint-imports
```

### Tach

Enforces architectural boundaries with layer definitions.

**Configuration:** Create `tach.toml` in project root:

```toml
source_roots = ["src"]
exact = false
forbid_circular_dependencies = true

[[modules]]
path = "your_package.cli"
layer = "presentation"
depends_on = [
    { path = "your_package.services" }
]

[[modules]]
path = "your_package.services"
layer = "domain"
depends_on = []
```

**Run locally:**
```bash
# Linux/macOS
./tools/tach_check.sh

# Windows
tools\tach_check.bat
```

**Or directly:**
```bash
tach check
```

## Code Quality CI

Add comprehensive CI checks to your GitHub Actions workflow.

### CI Workflow Example

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: ["*"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        check:
          - {name: "black", cmd: "black --check src tests"}
          - {name: "isort", cmd: "isort --check --profile=black src tests"}
          - {name: "pylint", cmd: "pylint -E ./src ./tests"}
          - {name: "pytest", cmd: "pytest"}
          - {name: "mypy", cmd: "mypy --strict src tests"}
    name: ${{ matrix.check.name }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ${{ matrix.check.cmd }}

  # Architecture checks (PR only)
  architecture:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    strategy:
      fail-fast: false
      matrix:
        check:
          - {name: "import-linter", cmd: "lint-imports"}
          - {name: "tach", cmd: "tach check"}
          - {name: "pycycle", cmd: "pycycle --here"}
          - {name: "vulture", cmd: "vulture src tests --min-confidence 60"}
    name: ${{ matrix.check.name }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ${{ matrix.check.cmd }}
```

## Development Tools

Convenience scripts for local development. Create a `tools/` directory with these scripts:

### Formatting Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `format_all.sh/bat` | Run black + isort on src/tests | **Mandatory** before commits |
| `black.bat` | Run black formatter only | Optional |
| `iSort.bat` | Run isort only | Optional |

**format_all.sh:**
```bash
#!/bin/bash
set -e
echo "Running isort..."
isort --profile=black --float-to-top src tests
echo "Running black..."
black src tests
echo "Formatting complete!"
```

### Quality Check Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `lint_imports.sh/bat` | Run import-linter | Optional (CI runs it) |
| `tach_check.sh/bat` | Run tach architecture check | Optional (CI runs it) |
| `pycycle_check.sh/bat` | Check circular dependencies | Optional (CI runs it) |
| `vulture_check.sh/bat` | Check dead code | Optional (CI runs it) |
| `pylint_check_for_errors.bat` | Run pylint errors only | Optional (CI runs it) |
| `mypy.bat` | Run type checking | Optional (CI runs it) |

### Utility Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `reinstall.bat` | Quick `pip install -e .` | Optional convenience |
| `checks2clipboard.bat` | Copy quality check output to clipboard | Optional, useful for LLM assistance |

### Performance Analysis Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `get_pytest_performance_stats.bat` | Collect test runtime statistics | Optional |
| `test_profiler.bat` | Profile slow tests | Optional |
| `test_profiler_generate_only.bat` | Generate profiler reports | Optional |
| `pydeps_graph.sh/bat` | Generate dependency visualization | Optional |
| `tach_docs.sh/bat/py` | Generate architecture documentation | Optional |

### Legacy Tools (Keep for Reference)

These tools are no longer actively used but kept for reference:

| Script | Status |
|--------|--------|
| `commit_summary.bat` | Legacy |
| `pr_summary.bat` | Legacy |
| `pr_review.bat` | Legacy |
| `pr_review_highlevel.bat` | Legacy |

---

# Testing Your Setup

## Verification Steps

**1. Test label creation:**
```bash
mcp-coder define-labels --dry-run
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

## Troubleshooting

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

---

# Related Documentation

- **[Claude Code Configuration](configuration/claude-code.md)** - Detailed Claude Code setup, CLI commands, troubleshooting
- **[CLI Reference](cli-reference.md)** - Complete mcp-coder command documentation
- **[Configuration Guide](configuration/config.md)** - User and system configuration
- **[Development Process](processes-prompts/development-process.md)** - Complete workflow methodology
- **[Claude Code Cheat Sheet](processes-prompts/claude_cheat_sheet.md)** - Slash command reference
