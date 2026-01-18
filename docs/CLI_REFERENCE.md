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

### define-labels

Sync workflow status labels to GitHub repository.

```bash
mcp-coder define-labels [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory path (default: current directory)
- `--dry-run` - Preview changes without applying them

**Description:** Create or update GitHub issue labels for workflow status tracking. Uses label configuration from `workflows/config/labels.json` or package defaults.

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

- **[Repository Setup](REPOSITORY_SETUP.md)** - GitHub Actions, labels, and repository configuration
- **[Configuration Guide](configuration/CONFIG.md)** - User config files and environment setup
- **[Development Process](processes_prompts/DEVELOPMENT_PROCESS.md)** - Workflow methodology and best practices