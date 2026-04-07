# GitHub Setup

GitHub-side configuration: tokens, labels, actions, CI, and automated dependency management.

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
mcp-coder gh-tool define-labels --dry-run  # Preview changes
```

**2. Apply labels:**

```bash
mcp-coder gh-tool define-labels            # Create/update labels
```

**3. Verify in GitHub:**

- Go to your repository → Issues → Labels
- Confirm status labels are created with correct colors

### Customizing Labels

**Default label source:** `mcp_coder/config/labels.json`, deployed with the package.

**Custom labels:** Place a `labels.json` file at `workflows/config/labels.json` in your project to override the defaults. See [`labels_schema.md`](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/src/mcp_coder/config/labels_schema.md) for the schema.

> **See also:** Issue [#726](https://github.com/MarcusJellinghaus/mcp_coder/issues/726) tracks improving cross-references for label setup docs.

**Test custom config:**

```bash
mcp-coder gh-tool define-labels --dry-run  # Preview your custom labels
```

### Issue Validation and Initialization

The `gh-tool define-labels` command now includes automatic issue validation:

**Automatic initialization:**

- Issues without any workflow status label are initialized with `status-01:created`
- Use `--dry-run` to preview which issues would be initialized

**Validation checks:**

- **Errors:** Issues with multiple status labels (requires manual fix)
- **Warnings:** Bot processes exceeding their stale timeout threshold

### Stale Timeout Configuration

Bot-busy labels can have configurable timeout thresholds in `labels.json`:

```json
{
  "internal_id": "implementing",
  "name": "status-06:implementing",
  "category": "bot_busy",
  "stale_timeout_minutes": 120
}
```

Default timeouts:

| Label | Timeout |
|-------|---------|
| status-03:planning | 15 minutes |
| status-06:implementing | 120 minutes |
| status-09:pr-creating | 15 minutes |

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

## Code Quality CI

Add comprehensive CI checks to your GitHub Actions workflow.

> **Note:** The example below uses Python tools (black, pytest, mypy, etc.). For Python-specific matrix details, see [python.md](python.md#ci-workflow-for-python).

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

### Monitor CI Results

Use `mcp-coder check branch-status` to monitor CI pipeline results and get comprehensive feedback on code quality checks.

## Automated Dependency Management

- **Purpose:** Security updates and dependency monitoring
- **Documentation:** [Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
- **Reference:** See `.github/dependabot.yml` in this repository
