# GitHub Label Workflow Setup

## Why

The mcp-coder development workflow tracks issues through status labels (`status-01:created` → `status-10:pr-created`). New issues must start with `status-01:created` so that:

- Issues are visible in the workflow pipeline
- The `/approve` command can transition them to the next status
- No issues get lost without a status label

This setup auto-labels new issues with `status-01:created` using a GitHub Action.

## Setup Steps

### 1. Create the GitHub Actions

Copy both workflow files to `.github/workflows/` in your repository.

**`label-new-issues.yml`** - Auto-labels new issues:

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

**`approve-command.yml`** - Handles `/approve` comments to promote issues:

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

### 2. Create Workflow Labels

Run from your project directory:

```bash
python workflows/define_labels.py
```

This creates all workflow status labels (`status-01:created` through `status-10:pr-created`) in your GitHub repository.

Use `--dry-run` to preview changes first.

### 3. Verify

Create a test issue - it should automatically receive the `status-01:created` label.

## Prerequisites

- GitHub Actions enabled on repository
- GitHub token configured in config file (for `define_labels.py`):
  - Linux/macOS: `~/.mcp_coder/config.toml`
  - Windows: `%USERPROFILE%\.mcp_coder\config.toml`
