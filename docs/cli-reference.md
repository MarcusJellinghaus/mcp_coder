# CLI Reference

Complete command documentation for all MCP Coder CLI commands.

## Command List

### Basics
Core commands for help, verification, and interactive prompts.

| Command | Description |
|---------|-------------|
| [`help`](#help) | Show comprehensive help information with examples |
| [`verify`](#verify) | Verify Claude CLI installation and configuration |
| [`prompt`](#prompt) | Execute prompt via Claude API with configurable debug output |

### Git Operations
Commit operations with AI assistance.

| Command | Description |
|---------|-------------|
| [`commit auto`](#commit-auto) | Auto-generate commit message using LLM |
| [`commit clipboard`](#commit-clipboard) | Use commit message from clipboard |

### Automated Development Workflow
End-to-end development automation from planning to pull requests.

| Command | Description |
|---------|-------------|
| [`create-plan`](#create-plan) | Generate implementation plan for a GitHub issue |
| [`implement`](#implement) | Execute implementation workflow from task tracker |
| [`create-pr`](#create-pr) | Create pull request with AI-generated summary |

### Coordinating Automated Development
Orchestration and monitoring of automated development across repositories.

| Command | Description |
|---------|-------------|
| [`coordinator test`](#coordinator-test) | Trigger Jenkins integration test for repository |
| [`coordinator run`](#coordinator-run) | Monitor and dispatch workflows for GitHub issues |
| [`coordinator vscodeclaude`](#coordinator-vscodeclaude) | Launch VS Code sessions for issues needing human review |
| [`coordinator issue-stats`](#coordinator-issue-stats) | Display issue statistics grouped by workflow status category |

### Quality Checks
Branch readiness verification and code quality tools.

| Command | Description |
|---------|-------------|
| [`check branch-status`](#check-branch-status) | Check branch readiness and optionally apply fixes |
| [`check file-size`](#check-file-size) | Check file sizes against maximum line count |

### GitHub Tools
GitHub repository utilities for branch detection and workflow automation.

| Command | Description |
|---------|-------------|
| [`gh-tool get-base-branch`](#gh-tool-get-base-branch) | Detect base branch for current feature branch |

### Git Tools
Git utility commands.

| Command | Description |
|---------|-------------|
| [`git-tool compact-diff`](#git-tool-compact-diff) | Generate compact diff replacing moved code blocks with summary comments |

### Repository & Issue Setup
Setup and configuration for GitHub workflow automation.

| Command | Description |
|---------|-------------|
| [`define-labels`](#define-labels) | Sync workflow status labels to GitHub repository |

## Global Options

```bash
mcp-coder --version                    # Show version information
mcp-coder --log-level LEVEL            # Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
mcp-coder --help                       # Show basic argparse help
mcp-coder help                         # Show comprehensive help with examples (recommended)
```

---

## Commands

### help

Show comprehensive help information with examples.

```bash
mcp-coder help
```

**Description:** Display detailed help information about all MCP Coder commands with usage examples and workflow patterns. More comprehensive than the standard `--help` flag.

**Note:** This provides much more detailed information than `mcp-coder --help`, including examples and common usage patterns.

---

### verify

Verify Claude CLI installation and configuration.

```bash
mcp-coder verify
```

**Description:** Check if Claude CLI is properly installed and configured for use with MCP Coder.

---

### prompt

Execute prompt via Claude API with configurable debug output.

```bash
mcp-coder prompt "Your prompt here" [OPTIONS]
```

**Arguments:**
- `prompt` - The prompt to send to Claude (required)

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)
- `--verbosity LEVEL` - Output detail: `just-text` (response only), `verbose` (+ metrics), `raw` (+ full JSON)
- `--store-response` - Save session to `.mcp-coder/responses/` for later continuation
- `--continue-session-from FILE` - Resume conversation from specific stored session file
- `--continue-session` - Resume from most recent session (auto-discovers latest file)
- `--session-id ID` - Direct session ID for continuation (overrides file-based options)
- `--timeout SECONDS` - API request timeout in seconds (default: 60)
- `--llm-method METHOD` - Communication method: `claude_code_cli` (default) or `claude_code_api`
- `--output-format FORMAT` - Output format: `text` (default) or `json` (includes session_id)
- `--mcp-config PATH` - Path to MCP configuration file (e.g., `.mcp.linux.json`)
- `--execution-dir PATH` - Working directory for Claude subprocess (default: current directory)

**Examples:**
```bash
# Basic prompt
mcp-coder prompt "Analyze this code structure"

# Store response for later continuation
mcp-coder prompt "Start project planning" --store-response

# Continue from specific session
mcp-coder prompt "What's next?" --continue-session-from response_2025-01-18T14-30-22.json

# Continue from most recent session
mcp-coder prompt "What's next?" --continue-session

# Use verbose output with MCP config
mcp-coder prompt "Review my implementation" --verbosity verbose --mcp-config .mcp.linux.json
```

---

### commit auto

Auto-generate commit message using LLM.

```bash
mcp-coder commit auto [OPTIONS]
```

**Options:**
- `--preview` - Show generated message and ask for confirmation before committing
- `--llm-method METHOD` - LLM method to use: `claude_code_cli` (default) or `claude_code_api`
- `--project-dir PATH` - Project directory path (default: current directory)
- `--mcp-config PATH` - Path to MCP configuration file
- `--execution-dir PATH` - Working directory for Claude subprocess

**Examples:**
```bash
# Auto-generate and commit
mcp-coder commit auto

# Preview before committing
mcp-coder commit auto --preview

# Use API method
mcp-coder commit auto --llm-method claude_code_api
```

---

### commit clipboard

Use commit message from clipboard.

```bash
mcp-coder commit clipboard [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)

**Examples:**
```bash
# Commit with message from clipboard
mcp-coder commit clipboard

# Specify project directory
mcp-coder commit clipboard --project-dir /path/to/project
```

---

### implement

Execute implementation workflow from task tracker.

```bash
mcp-coder implement [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)
- `--llm-method METHOD` - LLM method: `claude_code_cli` (default) or `claude_code_api`
- `--mcp-config PATH` - Path to MCP configuration file
- `--execution-dir PATH` - Working directory for Claude subprocess
- `--update-labels` - Automatically update GitHub issue labels on successful completion

**Description:** Execute the implementation workflow based on the task tracker. Reads tasks from `pr_info/TASK_TRACKER.md` and implements them step by step.

**Examples:**
```bash
# Run implementation workflow
mcp-coder implement

# Update GitHub labels on completion
mcp-coder implement --update-labels

# Use API method with MCP config
mcp-coder implement --llm-method claude_code_api --mcp-config .mcp.linux.json
```

---

### create-plan

Generate implementation plan for a GitHub issue.

```bash
mcp-coder create-plan ISSUE_NUMBER [OPTIONS]
```

**Arguments:**
- `issue_number` - GitHub issue number to create plan for (required)

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)
- `--llm-method METHOD` - LLM method: `claude_code_cli` (default) or `claude_code_api`
- `--mcp-config PATH` - Path to MCP configuration file
- `--execution-dir PATH` - Working directory for Claude subprocess
- `--update-labels` - Automatically update GitHub issue labels on successful completion

**Description:** Generate a detailed implementation plan for a GitHub issue, including step-by-step tasks and technical approach.

**Examples:**
```bash
# Create plan for issue #123
mcp-coder create-plan 123

# Create plan with label updates
mcp-coder create-plan 456 --update-labels

# Use specific project directory
mcp-coder create-plan 789 --project-dir /path/to/project
```

---

### create-pr

Create pull request with AI-generated summary.

```bash
mcp-coder create-pr [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)
- `--llm-method METHOD` - LLM method: `claude_code_cli` (default) or `claude_code_api`
- `--mcp-config PATH` - Path to MCP configuration file
- `--execution-dir PATH` - Working directory for Claude subprocess
- `--update-labels` - Automatically update GitHub issue labels on successful completion

**Description:** Create a pull request with AI-generated summary based on the changes made. Requires clean working directory and completed tasks.

**Prerequisites:**
- Clean working directory (no uncommitted changes)
- All tasks complete in `pr_info/TASK_TRACKER.md`
- On feature branch (not main)
- GitHub credentials configured

**Examples:**
```bash
# Create PR with auto-generated summary
mcp-coder create-pr

# Update labels after PR creation
mcp-coder create-pr --update-labels
```

---

### coordinator test

Trigger Jenkins integration test for repository.

```bash
mcp-coder coordinator test REPO_NAME --branch-name BRANCH [OPTIONS]
```

**Arguments:**
- `repo_name` - Repository name from config (e.g., `mcp_coder`) (required)

**Options:**
- `--branch-name BRANCH` - Git branch to test (required)
- `--log-level LEVEL` - Log level for mcp-coder commands in test script (default: DEBUG)

**Description:** Trigger Jenkins-based integration tests for a specific repository and branch. Uses configuration from user config file.

**Examples:**
```bash
# Test main branch
mcp-coder coordinator test mcp_coder --branch-name main

# Test feature branch with info logging
mcp-coder coordinator test my_project --branch-name feature-x --log-level INFO
```

**Output:**
```
Job triggered: MCP_Coder/mcp-coder-test-job - test - queue: 12345
https://jenkins.example.com/job/MCP_Coder/mcp-coder-test-job/42/
```

---

### coordinator run

Monitor and dispatch workflows for GitHub issues.

```bash
mcp-coder coordinator run (--all | --repo REPO_NAME) [OPTIONS]
```

**Options (mutually exclusive):**
- `--all` - Process all repositories from config (required if --repo not specified)
- `--repo NAME` - Process single repository (required if --all not specified)

**Additional Options:**
- `--force-refresh` - Force full cache refresh, bypass all caching

**Description:** Monitor GitHub issues and automatically dispatch workflows (create-plan, implement, create-pr) based on issue labels and status.

**Examples:**
```bash
# Process all configured repositories
mcp-coder coordinator run --all

# Process single repository
mcp-coder coordinator run --repo mcp_coder

# Force cache refresh
mcp-coder coordinator run --all --force-refresh
```

---

### coordinator vscodeclaude

Launch VS Code sessions for GitHub issues needing human review.

```bash
mcp-coder coordinator vscodeclaude [OPTIONS]
```

**Options:**
- `--repo NAME` - Process only the specified repository

**Description:** Automatically launch VS Code sessions for issues requiring human action (code review, plan review, issue analysis). Each session includes automated Claude Code integration.

**Prerequisites:**
1. **Trust workspace folder (one-time):** Open VS Code, go to File → Open Folder, select your workspace base folder (e.g., `C:\Users\YourName\Documents\VSCC`), and click "Yes, I trust the authors"
2. **Configuration:** Ensure `[vscodeclaude]` section exists in `~/.config/mcp_coder/config.toml`
3. **Repository setup:** Each repository needs a `.mcp.json` file

**Examples:**
```bash
# Process all configured repositories
mcp-coder coordinator vscodeclaude

# Process specific repository only
mcp-coder coordinator vscodeclaude --repo mcp_coder

# With debug logging
mcp-coder --log-level debug coordinator vscodeclaude
```

**See Also:** [Coordinator VSCodeClaude Guide](coordinator-vscodeclaude.md) for detailed setup and troubleshooting.

---

### coordinator issue-stats

Display issue statistics grouped by workflow status category.

```bash
mcp-coder coordinator issue-stats [OPTIONS]
```

**Options:**
- `--filter CATEGORY` - Filter by category: `all` (default), `human`, `bot`
- `--details` - Show individual issue details with links
- `--project-dir PATH` - Project directory path (default: current directory)

**Examples:**
```bash
# Show all categories
mcp-coder coordinator issue-stats

# Show only human action required
mcp-coder coordinator issue-stats --filter human

# Show bot issues with details
mcp-coder coordinator issue-stats --filter bot --details
```

**Example Output:**
```
=== Human Action Required ===
  status-01:created           5 issues
  status-04:plan-review       2 issues

=== Validation Errors ===
  No status label: 2 issues
  Multiple status labels: 1 issue

Total: 16 open issues (13 valid, 3 errors)
```

---

### check branch-status

Check comprehensive branch readiness including CI status, rebase requirements, task completion, and GitHub labels.

#### Synopsis

```bash
mcp-coder check branch-status [OPTIONS]
```

#### Options

- `--project-dir PATH` - Project directory path (default: current directory)
- `--ci-timeout SECONDS` - Wait up to N seconds for CI completion (default: 0 = no wait)
- `--fix [N]` - Fix issues up to N times (default: 0 = no fix, --fix alone = 1)
- `--llm-truncate` - Truncate output for LLM consumption
- `--llm-method METHOD` - LLM method for --fix (claude_code_cli or claude_code_api)
- `--mcp-config PATH` - Path to MCP configuration file
- `--execution-dir PATH` - Working directory for Claude subprocess

#### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | CI passed, or graceful scenarios (no CI configured, no wait requested) |
| 1 | Failure | CI failed, timeout, pending status, or fix operations failed |
| 2 | Technical Error | Invalid arguments, Git errors, API errors, or unexpected exceptions |

#### Behavior

**Without --ci-timeout (Current Behavior)**
Performs immediate snapshot check of current CI status without waiting.

**With --ci-timeout (New)**
Polls CI status every 15 seconds until completion or timeout:
- Early exits when CI completes (success or failure)
- Shows progress dots in human mode
- Silent polling in LLM mode (--llm-truncate)
- Returns current status on timeout

**Without --fix (Read-Only)**
Only checks and reports status, no automated fixes attempted.

**With --fix (Single Fix, Current Behavior Preserved)**
Attempts to fix CI failures once, no recheck after fix.

**With --fix N (Retry Fixes, New)**
Attempts to fix CI failures up to N times:
- Waits for CI after each fix attempt
- Stops early if CI passes
- Shows attempt progress ("Fix attempt 2/3...")

#### Examples

##### Quick status check
```bash
mcp-coder check branch-status
```

##### Wait for CI to complete (no fixing)
```bash
mcp-coder check branch-status --ci-timeout 300
```

##### Wait and auto-fix once
```bash
mcp-coder check branch-status --ci-timeout 180 --fix
```

##### Wait and retry fixes up to 3 times
```bash
mcp-coder check branch-status --ci-timeout 180 --fix 3
```

##### LLM-optimized with waiting
```bash
mcp-coder check branch-status --ci-timeout 300 --llm-truncate
```

##### Scripting example
```bash
#!/bin/bash
if mcp-coder check branch-status --ci-timeout 300; then
  echo "CI passed, ready to merge"
  exit 0
else
  echo "CI failed or timed out"
  exit 1
fi
```

#### Workflow Integration

##### Manual Development Flow
```bash
# 1. Check status and wait for CI
mcp-coder check branch-status --ci-timeout 180

# 2. If CI fails, auto-fix with retry
mcp-coder check branch-status --ci-timeout 180 --fix 3

# 3. If passes, create PR
mcp-coder create-pr
```

##### Automated Script Flow
```bash
# Wait for CI, fix if needed, exit with appropriate code
mcp-coder check branch-status --ci-timeout 300 --fix 2
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✓ Branch ready"
  # Continue with PR creation or merge
elif [ $EXIT_CODE -eq 1 ]; then
  echo "✗ CI failed after fixes"
  # Notify team or create issue
else
  echo "✗ Technical error"
  # Alert on configuration/Git issues
fi
```

#### Notes

- **Polling Strategy**: Fixed 15-second intervals, no maximum timeout limit
- **Early Exit**: Stops immediately when CI completes (success or failure)
- **API Errors**: Treated as graceful exit (code 0) to avoid blocking workflows
- **No CI Configured**: Returns code 0 (graceful exit)
- **Progress Feedback**: Controlled by --llm-truncate (dots in human mode, silent in LLM mode)

---

### define-labels

Sync workflow status labels to GitHub repository.

```bash
mcp-coder define-labels [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)
- `--dry-run` - Preview changes without applying them

**Description:** Create or update GitHub issue labels for workflow status tracking. Uses label configuration from `workflows/config/labels.json` or package defaults. Also validates issues and initializes issues without status labels.

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success - no errors or warnings |
| 1 | Errors found - issues with multiple status labels |
| 2 | Warnings only - stale bot processes detected |

**Examples:**
```bash
# Preview label changes
mcp-coder define-labels --dry-run

# Apply labels to repository
mcp-coder define-labels

# Apply to specific project
mcp-coder define-labels --project-dir /path/to/project
```

---

### check file-size

Check file sizes against maximum line count.

```bash
mcp-coder check file-size [OPTIONS]
```

**Options:**
- `--max-lines NUMBER` - Maximum lines per file (default: 600)
- `--allowlist-file PATH` - Path to allowlist file (default: .large-files-allowlist)
- `--generate-allowlist` - Output violating paths for piping to allowlist
- `--project-dir PATH` - Project directory path (default: current directory)

**Description:** Scan files in a project and report any that exceed the maximum line count. Binary files are automatically skipped. Files can be excluded from checking by adding them to an allowlist file.

**Exit Codes:**
- `0` - All files pass (or no violations when using `--generate-allowlist`)
- `1` - One or more files exceed the line limit

**Allowlist Format:**
The allowlist file contains one path per line (relative to project directory):
```
# Comments start with #
src/legacy/large_module.py
tests/fixtures/big_test_data.py
```

**Examples:**
```bash
# Check all Python files with default 600 line limit
mcp-coder check file-size

# Use custom line limit
mcp-coder check file-size --max-lines 400

# Check specific project directory
mcp-coder check file-size --project-dir /path/to/project

# Generate allowlist from current violations
mcp-coder check file-size --generate-allowlist > .large-files-allowlist

# Use custom allowlist file
mcp-coder check file-size --allowlist-file .my-allowlist
```

**Use Cases:**
- **CI/CD Integration:** Add to pre-commit hooks or CI pipelines to enforce file size limits
- **Codebase Cleanup:** Identify large files that may need refactoring
- **Gradual Adoption:** Use `--generate-allowlist` to create an allowlist of existing large files, then enforce limits on new files

---

### gh-tool get-base-branch

Detect the base branch for the current feature branch.

```bash
mcp-coder gh-tool get-base-branch [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)

**Description:** Detects the appropriate base branch for git operations (diff, rebase) using a priority-based approach:

1. **GitHub PR base branch** - If an open PR exists for the current branch
2. **Linked issue's base branch** - Extracts issue number from branch name and checks the `### Base Branch` section in the issue body
3. **Default branch** - Falls back to the repository's default branch (main/master)

**Exit Codes:**
- `0` - Success, base branch printed to stdout
- `1` - Could not detect base branch
- `2` - Error (not a git repo, API failure, etc.)

**Examples:**
```bash
# Detect base branch for current feature branch
mcp-coder gh-tool get-base-branch

# Use in shell scripts
BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)
git diff ${BASE_BRANCH}...HEAD

# Specify project directory
mcp-coder gh-tool get-base-branch --project-dir /path/to/project
```

**Use Cases:**
- Slash commands (`/rebase`, `/implementation_review`) use this to determine correct base branch
- CI scripts that need to compare against the correct parent branch
- Workflows involving feature branches based on non-main branches

---

## git-tool

Git utility commands.

### git-tool compact-diff

Generate a compact diff between the current branch and its base branch,
replacing moved code blocks with summary comments.

```bash
mcp-coder git-tool compact-diff [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory (default: current directory)
- `--base-branch BRANCH` - Base branch to diff against (default: auto-detected)
- `--exclude PATTERN` - Exclude paths matching pattern (repeatable)

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success — compact diff printed to stdout |
| 1 | Could not detect base branch |
| 2 | Error (invalid repo, unexpected exception) |

**Examples:**
```bash
# Generate compact diff for current branch
mcp-coder git-tool compact-diff

# Exclude conversation files
mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"

# Specify base branch explicitly
mcp-coder git-tool compact-diff --base-branch main

# Use in scripts
mcp-coder git-tool compact-diff --project-dir /path/to/project --exclude "*.lock"
```

**Description:** Produces a diff between the current branch and its base branch, then applies a two-pass pipeline to replace moved code blocks with concise summary comments. This reduces token usage when reviewing large refactoring changes with an LLM.

---

## Configuration and Setup

### MCP Configuration

Many commands support the `--mcp-config` flag to specify MCP (Model Context Protocol) configuration:

```bash
# Platform-specific MCP configurations
.mcp.linux.json    # Linux environments
.mcp.windows.json  # Windows environments  
.mcp.macos.json    # macOS environments
```

**Commands supporting `--mcp-config`:**
- `prompt`
- `commit auto`
- `implement`
- `create-plan`
- `create-pr`
- `check branch-status`

**Usage:**
```bash
mcp-coder prompt "Analyze code" --mcp-config .mcp.linux.json
mcp-coder implement --mcp-config .mcp.windows.json
```

### First Time Setup

Some commands require configuration on first run:

```bash
# Coordinator commands auto-create config template
mcp-coder coordinator test repo_name --branch-name main
# Output: Created default config file at ~/.config/mcp_coder/config.toml
```

### Common Patterns

**Development Workflow:**
```bash
# 1. Create implementation plan
mcp-coder create-plan 123

# 2. Execute implementation
mcp-coder implement --update-labels

# 3. Create pull request
mcp-coder create-pr --update-labels
```

**Session Continuation:**
```bash
# Start planning session
mcp-coder prompt "Let's plan feature X" --store-response

# Continue later
mcp-coder prompt "What's the next step?" --continue-session
```

**Repository Testing:**
```bash
# Test specific branch
mcp-coder coordinator test my_repo --branch-name feature-branch

# Monitor all repositories for automation
mcp-coder coordinator run --all
```

---

## See Also

- **[Repository Setup](repository-setup.md)** - GitHub Actions, labels, and repository configuration
- **[Configuration Guide](configuration/config.md)** - User config files and environment setup
- **[Development Process](processes-prompts/development-process.md)** - Workflow methodology and best practices
