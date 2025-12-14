# MCP Coder Configuration Guide

## Configuration File Locations

### Windows
```
%USERPROFILE%\.mcp_coder\config.toml
```

Example: `C:\Users\YourName\.mcp_coder\config.toml`

### Linux / macOS / Containers
```
~/.config/mcp_coder/config.toml
```

Example: `/home/username/.config/mcp_coder/config.toml`

## Auto-Creation

On first run of any command requiring configuration, MCP Coder will automatically create the config directory and a template file. You'll see:

```bash
$ mcp-coder coordinator test mcp_coder --branch-name main
Created default config file at ~/.mcp_coder/config.toml
Please update it with your Jenkins and repository information.
```

## Configuration Template

The auto-created template includes all sections with example values:

```toml
# MCP Coder Configuration
# Update with your actual credentials and repository information

[jenkins]
# Jenkins server configuration
# Environment variables (higher priority): JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
server_url = "https://jenkins.example.com:8080"
username = "your-jenkins-username"
api_token = "your-jenkins-api-token"
# The Jenkins variables can be also configured as environment variables:
# - JENKINS_URL
# - JENKINS_USER
# - JENKINS_TOKEN

# Coordinator repositories
# Add your repositories here following this pattern

[coordinator.repos.repo_a]
repo_url = "https://github.com/your-org/repo_a.git"
executor_test_path = "jenkins_folder_a/test-job-a"
github_credentials_id = "github-general-pat"

[coordinator.repos.repo_b]
repo_url = "https://github.com/your-org/repo_b.git"
executor_test_path = "jenkins_folder_b/test-job-b"
github_credentials_id = "github-general-pat"

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# executor_test_path = "Folder/job-name"
# github_credentials_id = "github-credentials-id"
```

## Configuration Sections

### [jenkins]

Jenkins server credentials for job automation.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `server_url` | string | Jenkins server URL with port | Yes |
| `username` | string | Jenkins username | Yes |
| `api_token` | string | Jenkins API token (not password) | Yes |

**Example:**
```toml
[jenkins]
server_url = "https://jenkins.company.com:8080"
username = "ci-automation"
api_token = "11a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5"
```

**How to get API token:**
1. Log into Jenkins web UI
2. Click your name (top right) → Configure
3. Under "API Token", click "Add new Token"
4. Copy the generated token

### [coordinator.repos.*]

Repository configurations for integration testing.

Each repository needs its own nested section: `[coordinator.repos.repo_name]`

**Note:** These are nested TOML sections using dot notation. The configuration system supports accessing nested sections like `coordinator.repos.mcp_coder` to retrieve values from the `[coordinator.repos.mcp_coder]` section

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `repo_url` | string | Git repository HTTPS URL | Yes |
| `executor_test_path` | string | Jenkins job path (folder/job-name) | Yes |
| `github_credentials_id` | string | Jenkins GitHub credentials ID (see setup below) | Yes |

**Example:**
```toml
[coordinator.repos.my_project]
repo_url = "https://github.com/myorg/my_project.git"
executor_test_path = "MyProject/integration-tests"
github_credentials_id = "github-pat-token"
```

**Repository naming:**
- Use lowercase with underscores (e.g., `mcp_coder`, `my_project`)
- Must match the repo_name used in CLI commands
- Can be different from actual GitHub repo name

### GitHub Credentials Setup

For Jenkins to access GitHub repositories, you need to set up GitHub credentials in Jenkins:

#### 1. Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select appropriate scopes (minimum: `repo` for private repos, `public_repo` for public repos)
4. Copy the generated token (save it securely - you won't see it again)

#### 2. Store Token in Jenkins

1. In Jenkins web UI, go to **Manage Jenkins** → **Manage Credentials**
2. Select appropriate domain (usually "Global")
3. Click **Add Credentials**
4. Choose **Username with password** credential type:
   - **Username**: Your GitHub username
   - **Password**: The GitHub personal access token (from step 1)
   - **ID**: Enter a descriptive ID (e.g., `github-general-pat`, `github-mcp-coder`)
   - **Description**: Optional description (e.g., "GitHub PAT for MCP Coder repos")
5. Click **Create**

#### 3. Use Credentials ID in Configuration

Use the **ID** from step 2 as the `github_credentials_id` in your repository configuration:

```toml
[coordinator.repos.my_project]
repo_url = "https://github.com/myorg/my_project.git"
executor_test_path = "MyProject/integration-tests"
github_credentials_id = "github-general-pat"  # ← The ID from Jenkins
```

**Security Notes:**
- Use descriptive but not sensitive credential IDs
- Regularly rotate GitHub tokens
- Use minimum required token scopes
- Consider using different tokens for different repositories if needed

## Environment Variable Overrides

Environment variables take **highest priority** over config file values.

| Environment Variable | Overrides | Example |
|---------------------|-----------|---------|
| `JENKINS_URL` | `[jenkins] server_url` | `https://jenkins.local:8080` |
| `JENKINS_USER` | `[jenkins] username` | `automation-user` |
| `JENKINS_TOKEN` | `[jenkins] api_token` | `abc123def456...` |

**Usage:**
```bash
# Override all Jenkins config via environment
export JENKINS_URL="https://jenkins.dev.local:8080"
export JENKINS_USER="dev-automation"
export JENKINS_TOKEN="dev-token-123"

mcp-coder coordinator test mcp_coder --branch-name feature-x
```

**Use cases:**
- CI/CD pipelines (inject secrets via environment)
- Testing with different Jenkins servers
- Temporary credential overrides

## Usage Examples

### Basic Usage

Trigger test for mcp_coder repository on feature branch:

```bash
mcp-coder coordinator test mcp_coder --branch-name feature-x
```

Expected output:
```
Job triggered: MCP_Coder/mcp-coder-test-job - test - queue: 12345
https://jenkins.example.com/job/MCP_Coder/mcp-coder-test-job/42/
```

### With Debug Logging

```bash
mcp-coder coordinator test mcp_coder --branch-name feature-x --log-level DEBUG
```

### Testing Main Branch

```bash
mcp-coder coordinator test mcp_coder --branch-name main
```

### Testing Different Repository

```bash
mcp-coder coordinator test mcp_server_filesystem --branch-name develop
```

## Test Command

When you trigger a coordinator test, Jenkins executes a comprehensive verification script that validates the entire environment setup. This ensures the containerized environment is properly configured before running actual tests.

### What Gets Tested

The default test command performs the following checks:

#### 1. Tool Verification
- Verifies `mcp-coder` is installed and displays version
- Verifies `mcp-code-checker` is installed
- Verifies `mcp-server-filesystem` is installed
- Runs `mcp-coder verify` to check environment

#### 2. Environment Setup
- Sets `MCP_CODER_PROJECT_DIR=/workspace/repo`
- Sets `MCP_CODER_VENV_DIR=/workspace/.venv`
- Syncs dependencies using `uv sync --extra dev`

#### 3. Claude CLI Verification
- Verifies `claude` CLI is installed
- Lists configured MCP servers with `claude mcp list`
- Tests basic Claude functionality with simple prompt

#### 4. MCP Coder Functionality
- Tests MCP Coder with debug logging
- Verifies prompt command works correctly

#### 5. Virtual Environment
- Activates project virtual environment
- Re-verifies `mcp-coder` from within venv

### Test Command Script

The full test script executed by Jenkins:

```bash
# Tool verification
which mcp-coder && mcp-coder --version
which mcp-code-checker && mcp-code-checker --help
which mcp-server-filesystem && mcp-server-filesystem --help
mcp-coder verify
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
uv sync --extra dev
# Claude CLI verification
which claude
claude mcp list
claude -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level debug prompt "What is 1 + 1?"
# Project environment verification
source .venv/bin/activate
which mcp-coder && mcp-coder --version
```

### Customization

**Note**: The test command is currently hardcoded in the coordinator implementation. Future versions may support custom test commands per repository via configuration.

## Troubleshooting

### Error: Repository not found

```
Error: Repository 'nonexistent_repo' not found in config
Add it to config file under [coordinator.repos.nonexistent_repo]
```

**Solution:** Add repository configuration to config file:
```toml
[coordinator.repos.nonexistent_repo]
repo_url = "https://github.com/your-org/repo.git"
executor_test_path = "Folder/job-name"
github_credentials_id = "github-credentials-id"
```

### Error: Missing required field

```
Error: Repository 'mcp_coder' missing required field 'executor_test_path'
```

**Solution:** Ensure all three fields are present in repository config.

### Error: Jenkins configuration incomplete

```
Error: Jenkins configuration incomplete. Missing: server_url, username
Set via environment variables (JENKINS_URL, JENKINS_USER, JENKINS_TOKEN) or config file [jenkins] section
```

**Solution:** Either:
1. Add to config file:
   ```toml
   [jenkins]
   server_url = "https://jenkins.example.com:8080"
   username = "your-username"
   api_token = "your-token"
   ```

2. Or set environment variables:
   ```bash
   export JENKINS_URL="https://jenkins.example.com:8080"
   export JENKINS_USER="your-username"
   export JENKINS_TOKEN="your-token"
   ```

### Error: Permission denied creating config

```
PermissionError: [Errno 13] Permission denied: '/home/user/.mcp_coder/config.toml'
```

**Solution:** Check directory permissions or run as appropriate user.

## Security Best Practices

### API Tokens
- ✅ Use API tokens (NOT passwords)
- ✅ Store tokens in config file (user-only permissions)
- ✅ Use environment variables in CI/CD
- ❌ Never commit config file to git
- ❌ Never share API tokens

## Adding New Repositories

1. Identify repository details:
   - Git URL
   - Jenkins job path
   - GitHub credentials ID in Jenkins

2. Add to config:
   ```toml
   [coordinator.repos.new_repo]
   repo_url = "https://github.com/org/new_repo.git"
   executor_test_path = "NewRepo/test-job"
   github_credentials_id = "github-credentials"
   ```

3. Test:
   ```bash
   mcp-coder coordinator test new_repo --branch-name main
   ```

## Platform-Specific Notes

### Windows
- Config path uses `%USERPROFILE%` (typically `C:\Users\YourName`)
- Path separators are handled automatically
- Use PowerShell or Command Prompt

### Linux/Containers
- Config path uses `~/.config/mcp_coder/`
- Follows XDG Base Directory Specification
- Ideal for containerized coordinator deployments

### Docker/Containers
Mount config directory as volume:
```bash
docker run -v ~/.config/mcp_coder:/root/.config/mcp_coder my-container
```

## Related Documentation

- [README.md](../../README.md) - Installation and quick start
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - System architecture
- [LABEL_WORKFLOW_SETUP.md](LABEL_WORKFLOW_SETUP.md) - GitHub Actions for issue labels
