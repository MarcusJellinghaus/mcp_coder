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

# Coordinator test repositories
# Add your repositories here following this pattern

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/your-org/mcp_coder.git"
test_job_path = "MCP_Coder/mcp-coder-test-job"
github_credentials_id = "github-general-pat"

[coordinator.repos.mcp_server_filesystem]
repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
test_job_path = "MCP_Filesystem/test-job"
github_credentials_id = "github-general-pat"

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# test_job_path = "Folder/job-name"
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

Each repository needs its own section: `[coordinator.repos.repo_name]`

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `repo_url` | string | Git repository HTTPS URL | Yes |
| `test_job_path` | string | Jenkins job path (folder/job-name) | Yes |
| `github_credentials_id` | string | Jenkins GitHub credentials ID | Yes |

**Example:**
```toml
[coordinator.repos.my_project]
repo_url = "https://github.com/myorg/my_project.git"
test_job_path = "MyProject/integration-tests"
github_credentials_id = "github-pat-token"
```

**Repository naming:**
- Use lowercase with underscores (e.g., `mcp_coder`, `my_project`)
- Must match the repo_name used in CLI commands
- Can be different from actual GitHub repo name

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
test_job_path = "Folder/job-name"
github_credentials_id = "github-credentials-id"
```

### Error: Missing required field

```
Error: Repository 'mcp_coder' missing required field 'test_job_path'
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

### File Permissions

Ensure config file is readable only by you:

**Linux/macOS:**
```bash
chmod 600 ~/.config/mcp_coder/config.toml
```

**Windows:**
File is automatically created in user profile (protected by OS).

### Git Ignore

Add to `.gitignore`:
```gitignore
# MCP Coder config (contains secrets)
.mcp_coder/
config.toml
```

## Adding New Repositories

1. Identify repository details:
   - Git URL
   - Jenkins job path
   - GitHub credentials ID in Jenkins

2. Add to config:
   ```toml
   [coordinator.repos.new_repo]
   repo_url = "https://github.com/org/new_repo.git"
   test_job_path = "NewRepo/test-job"
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
