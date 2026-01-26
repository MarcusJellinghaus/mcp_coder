# Label Setup Guide

## Introduction

The mcp-coder development workflow uses **status labels** to track issues through their lifecycle. These labels (`status-01:created` through `status-10:pr-created`) provide visibility into where each issue stands in the development pipeline.

**Why status labels matter:**
- Issues are visible in the workflow pipeline
- The `/approve` command can transition issues to the next status
- No issues get lost without a status label
- Team members can quickly see work-in-progress

## Prerequisites

### GitHub Token Configuration

The `define-labels` command requires a GitHub token configured in your user config file:

| Platform | Config Location |
|----------|-----------------|
| Linux/macOS | `~/.mcp_coder/config.toml` |
| Windows | `%USERPROFILE%\.mcp_coder\config.toml` |

Add your GitHub token to the config file:

```toml
[github]
token = "ghp_your_github_token_here"
```

The token needs `repo` scope permissions to create and manage labels.

## Label Configuration

The `define-labels` command uses a two-location configuration system to determine which labels to create.

### Configuration Priority

1. **Local project config** (checked first):
   ```
   your-project/workflows/config/labels.json
   ```
   Use this to customize labels for your specific project.

2. **Bundled package config** (fallback):
   ```
   mcp_coder/config/labels.json
   ```
   Used when no local config exists. Provides sensible defaults.

### Configuration File Format

The `labels.json` file contains an array of label definitions:

```json
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
```

Each label requires:
- `name`: The label name (string)
- `color`: Hex color code without the `#` prefix (string)
- `description`: Brief description of the label's purpose (string)

### Customizing Labels

To use custom labels for your project:

1. Create the config directory:
   ```bash
   mkdir -p workflows/config
   ```

2. Copy the default config as a starting point:
   ```bash
   # Find the bundled config location
   python -c "from mcp_coder.utils.github_operations.label_config import get_labels_config_path; print(get_labels_config_path(None))"
   ```

3. Create `workflows/config/labels.json` with your custom labels

4. Preview changes before applying:
   ```bash
   mcp-coder define-labels --dry-run
   ```

## Using the define-labels Command

### Basic Usage

```bash
# Preview changes (recommended first step)
mcp-coder define-labels --dry-run

# Apply labels to repository
mcp-coder define-labels
```

### Command Options

| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Specify project directory (default: current directory) |
| `--dry-run` | Preview changes without applying them |

### Examples

```bash
# Preview what labels will be created
mcp-coder define-labels --dry-run

# Apply labels to current project
mcp-coder define-labels

# Apply labels to a specific project
mcp-coder define-labels --project-dir /path/to/project
```

### Output

The command shows:
- Labels that will be created (new)
- Labels that will be updated (color or description changed)
- Labels that already exist and are unchanged

## GitHub Actions Setup

To automate label management, set up these GitHub Actions in your repository.

### Auto-Label New Issues

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

This automatically labels new issues with `status-01:created`.

### Approve Command Handler

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

This handles `/approve` comments to promote issues through the workflow.

## Label Reference

The default workflow uses these status labels:

| Label | Description |
|-------|-------------|
| `status-01:created` | Issue created, awaiting triage |
| `status-02:awaiting-planning` | Ready for planning phase |
| `status-03:planning-in-progress` | Currently being planned |
| `status-04:plan-review` | Plan ready for review |
| `status-05:plan-ready` | Plan approved, ready for implementation |
| `status-06:implementation-in-progress` | Currently being implemented |
| `status-07:code-review` | Code ready for review |
| `status-08:ready-pr` | Ready for pull request |
| `status-09:pr-in-progress` | PR being created |
| `status-10:pr-created` | PR created, awaiting merge |

## Verification

After setup, verify everything works:

1. Run `mcp-coder define-labels --dry-run` to confirm labels are configured
2. Create a test issue in your repository
3. Verify the issue automatically receives the `status-01:created` label
4. Comment `/approve` on the issue to test status promotion

## See Also

- [Development Process](../processes-prompts/development-process.md) - Complete workflow documentation
- [Configuration Guide](../configuration/config.md) - General configuration options
