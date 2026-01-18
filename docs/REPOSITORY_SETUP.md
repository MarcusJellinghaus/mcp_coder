# Repository Setup Guide

Complete guide for setting up GitHub Actions, workflow labels, and repository configuration for MCP Coder development workflows.

## Overview

This guide covers:
- **GitHub Actions** - Automated issue labeling and status progression
- **Workflow Labels** - Status tracking system for issues
- **Repository Configuration** - Git settings and integrations
- **MCP Configuration** - Model Context Protocol setup

## Quick Setup Checklist

- [ ] Configure GitHub token in user config
- [ ] Set up workflow labels with `mcp-coder define-labels`
- [ ] Install GitHub Actions workflows
- [ ] Configure MCP servers (optional)
- [ ] Test workflow with a sample issue

## GitHub Token Configuration

### Prerequisites

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
                  body: `✅ Status promoted: \\`${currentStatus}\\` → \\`${nextStatus}\\``
                });
                return;
              }
            }
            
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: issue.number,
              body: `⚠️ Cannot promote. Issue needs status: \\`status-01:created\\`, \\`status-04:plan-review\\`, or \\`status-07:code-review\\``
            });
```

**Purpose:** Handles `/approve` comments to promote issues through workflow stages.

### Installing Actions

**1. Create directories:**
```bash
mkdir -p .github/workflows
```

**2. Add workflow files:**
Copy the YAML content above into the respective files.

**3. Commit and push:**
```bash
git add .github/workflows/
git commit -m "Add GitHub Actions for issue workflow automation"
git push
```

**4. Verify in GitHub:**
- Go to repository → Actions tab
- Confirm workflows appear in the list

## Repository Configuration

### Git Configuration

**Recommended git settings for MCP Coder workflows:**

```bash
# Configure git for better commit messages
git config commit.template .gitmessage

# Configure merge behavior
git config merge.ours.driver true

# Configure branch tracking
git config push.default simple
```

### Branch Protection (Optional)

**Protect main branch:**
1. Go to repository → Settings → Branches
2. Add rule for `main` branch:
   - Require pull request reviews
   - Require status checks to pass
   - Require up-to-date branches
   - Include administrators

### Issue Templates (Optional)

Create `.github/ISSUE_TEMPLATE/feature_request.md`:

```markdown
---
name: Feature Request
about: Request a new feature
title: '[FEATURE] '
labels: 'status-01:created'
assignees: ''
---

## Description
Brief description of the feature request.

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Implementation Ideas
Any initial thoughts on implementation approach.
```

## MCP Configuration

### What is MCP?

**Model Context Protocol (MCP)** enables Claude Code to use specialized servers for enhanced functionality:

- **code-checker**: Pylint, pytest, mypy integration
- **filesystem**: Enhanced file operations
- **Custom servers**: Project-specific tools

### Platform-Specific Configuration

MCP Coder supports platform-specific MCP configuration files:

| Platform | Config File |
|----------|-------------|
| **Linux** | `.mcp.linux.json` |
| **Windows** | `.mcp.windows.json` |
| **macOS** | `.mcp.macos.json` |

**File location:** Project root directory

### Basic MCP Configuration

**Example `.mcp.linux.json`:**

```json
{
  "mcpServers": {
    "code-checker": {
      "command": "python",
      "args": ["-m", "mcp_code_checker"],
      "env": {
        "PYTHONPATH": "/path/to/project"
      }
    },
    "filesystem": {
      "command": "python", 
      "args": ["-m", "mcp_server_filesystem"],
      "env": {}
    }
  }
}
```

### Using MCP Configuration

**With commands:**
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

### Gitignore MCP Files

**Add to `.gitignore`:**
```gitignore
# MCP configuration files (may contain sensitive paths)
.mcp.*.json
```

## Complete Workflow Status Labels

| Label | Color | Description |
|-------|-------|-------------|
| `status-01:created` | `#d4c5f9` | Issue created, awaiting triage |
| `status-02:awaiting-planning` | `#c5def5` | Ready for planning phase |
| `status-03:planning-in-progress` | `#b8e6b8` | Currently being planned |
| `status-04:plan-review` | `#ffe066` | Plan ready for review |
| `status-05:plan-ready` | `#66b3ff` | Plan approved, ready for implementation |
| `status-06:implementation-in-progress` | `#ffb366` | Currently being implemented |
| `status-07:code-review` | `#ff9999` | Code ready for review |
| `status-08:ready-pr` | `#c266ff` | Ready for pull request |
| `status-09:pr-in-progress` | `#66ffcc` | PR being created |
| `status-10:pr-created` | `#ff66b3` | PR created, awaiting merge |

## Testing Your Setup

### Verification Steps

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

**3. Test MCP integration (if configured):**
```bash
# This should work if MCP is properly configured
mcp-coder prompt "List files in src/" --mcp-config .mcp.linux.json
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

## Next Steps

After setup is complete:

1. **Read the development process:** [Development Process](docs/processes_prompts/DEVELOPMENT_PROCESS.md)
2. **Learn the CLI commands:** [CLI Reference](docs/CLI_REFERENCE.md) 
3. **Configure your environment:** [Configuration Guide](docs/configuration/CONFIG.md)
4. **Create your first automated workflow:** Start with a simple issue and test the full cycle

## Related Documentation

- **[Label Setup Guide](docs/getting-started/LABEL_SETUP.md)** - Detailed label management
- **[Configuration Guide](docs/configuration/CONFIG.md)** - User and system configuration
- **[Development Process](docs/processes_prompts/DEVELOPMENT_PROCESS.md)** - Complete workflow methodology