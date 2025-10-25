# Step 5: Documentation & Integration Tests

## Overview
Create comprehensive documentation and integration tests. This includes CONFIG.md for configuration reference, README updates, and Jenkins integration tests marked with `jenkins_integration` marker.

## LLM Prompt
```
You are implementing Step 5 of the "mcp-coder coordinator test" feature.

Read pr_info/steps/summary.md for context.

Your task: Create documentation and integration tests.

Requirements:
1. Create docs/configuration/CONFIG.md with comprehensive examples
2. Update README.md with usage examples
3. Write integration tests marked with jenkins_integration
4. Run ALL code quality checks (including integration tests if Jenkins configured)
5. Verify all acceptance criteria met

Follow the specifications in this step file exactly.
```

## Phase 5A: Create Configuration Documentation

### WHERE
File: `docs/configuration/CONFIG.md` (NEW FILE)

### WHAT
Comprehensive configuration documentation including:
- File locations (Windows/Linux)
- Full TOML template
- Environment variable overrides
- Usage examples
- Troubleshooting

### CONTENT STRUCTURE

```markdown
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
```

## Phase 5B: Update README

### WHERE
File: `README.md` (MODIFY EXISTING)

### WHAT
Add usage examples for coordinator test command and link to CONFIG.md.

### WHERE IN FILE
Add new section after existing commands documentation (around line 100-150, depending on current README structure).

### CONTENT TO ADD

```markdown
## Coordinator Commands

Trigger Jenkins-based integration tests for repositories in containerized environments.

### coordinator test

Trigger integration test for a specific repository and branch:

```bash
mcp-coder coordinator test <repo_name> --branch-name <branch>
```

**Parameters:**
- `<repo_name>` - Repository identifier from config (e.g., `mcp_coder`)
- `--branch-name` - Git branch to test (required)
- `--log-level` - Logging verbosity (optional, default: INFO)

**Example:**
```bash
mcp-coder coordinator test mcp_coder --branch-name feature-x
```

**Output:**
```
Job triggered: MCP_Coder/mcp-coder-test-job - test - queue: 12345
https://jenkins.example.com/job/MCP_Coder/mcp-coder-test-job/42/
```

**Configuration:**
See [Configuration Guide](docs/configuration/CONFIG.md) for complete configuration documentation.

**First Run:**
On first use, a configuration template is auto-created at:
- Windows: `%USERPROFILE%\.mcp_coder\config.toml`
- Linux: `~/.config/mcp_coder/config.toml`

Update the template with your Jenkins credentials and repository information.
```

## Phase 5C: Integration Tests

### WHERE
File: `tests/cli/commands/test_coordinator.py` (EXTEND EXISTING)

Add new test class at the end of file.

### WHAT
Add integration test class marked with `jenkins_integration`:

```python
@pytest.mark.jenkins_integration
class TestCoordinatorIntegration:
    """Integration tests for coordinator command with real Jenkins.
    
    These tests require:
    - Jenkins server configured
    - Jenkins credentials in config or environment
    - Test job configured in Jenkins
    
    Tests are skipped if Jenkins not configured.
    """
    
    @pytest.fixture
    def jenkins_available(self) -> bool:
        """Check if Jenkins configuration is available."""
        from mcp_coder.cli.commands.coordinator import get_jenkins_credentials
        try:
            get_jenkins_credentials()
            return True
        except ValueError:
            return False
    
    def test_coordinator_test_end_to_end(
        self, jenkins_available: bool, tmp_path: Path
    ) -> None:
        """Test complete coordinator test flow with real Jenkins."""
        if not jenkins_available:
            pytest.skip("Jenkins not configured")
        
        # This test actually triggers a Jenkins job
        # Only run if you have a test Jenkins environment
        
    def test_coordinator_test_with_invalid_job(
        self, jenkins_available: bool
    ) -> None:
        """Test error handling with invalid job path."""
        if not jenkins_available:
            pytest.skip("Jenkins not configured")
```

### HOW
Integration points:
- Mark class with `@pytest.mark.jenkins_integration`
- Use `pytest.skip()` to skip if Jenkins not configured
- These tests can trigger real Jenkins jobs
- Should be run manually or in CI with Jenkins access

### ALGORITHM
```
1. Check if Jenkins credentials available
2. If not, skip test with helpful message
3. If available, create test args
4. Call execute_coordinator_test() with real config
5. Verify job triggered (don't wait for completion)
6. Verify output format is correct
```

## Phase 5D: Final Verification

### Run All Code Quality Checks

```python
# 1. Pylint
mcp__code-checker__run_pylint_check()

# 2. Mypy
mcp__code-checker__run_mypy_check()

# 3. Fast unit tests (default for development)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not jenkins_integration and not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# 4. Integration tests (optional - only if Jenkins configured)
# mcp__code-checker__run_pytest_check(
#     extra_args=["-n", "auto"],
#     markers=["jenkins_integration"]
# )
```

### Manual Testing Checklist

- [ ] Config auto-creation works
- [ ] Config template has all sections
- [ ] Command parsing works
- [ ] Validation catches missing repos
- [ ] Validation catches incomplete repos
- [ ] Jenkins credentials load from config
- [ ] Jenkins credentials load from env vars (priority)
- [ ] Job triggering works with mocked Jenkins
- [ ] Output format is correct
- [ ] Exit codes are correct (0 success, 1 error)
- [ ] Help text shows coordinator command
- [ ] Error messages are helpful

### Acceptance Criteria Verification

From issue #149:

- [ ] Command accepts repo name and branch name parameters
- [ ] Loads Jenkins configuration from user config or environment variables
- [ ] Auto-creates config directory and template file on first run
- [ ] Validates requested repo exists and is complete
- [ ] Starts Jenkins job with correct parameters (REPO_URL, BRANCH_NAME, GITHUB_CREDENTIALS_ID)
- [ ] Displays job information with clickable URL
- [ ] Returns exit code 0 for success, 1 for failures
- [ ] Shows helpful error for missing/invalid repository
- [ ] Comprehensive documentation in `docs/configuration/CONFIG.md`
- [ ] Unit tests with >80% coverage
- [ ] Integration tests (can be skipped if Jenkins not configured)
- [ ] All imports working correctly

## Success Criteria

### Documentation:
- ✅ CONFIG.md created with all sections
- ✅ CONFIG.md includes platform-specific paths
- ✅ CONFIG.md includes troubleshooting
- ✅ README.md updated with usage examples
- ✅ README.md links to CONFIG.md

### Integration Tests:
- ✅ Integration test class created
- ✅ Tests marked with `jenkins_integration`
- ✅ Tests skip gracefully if Jenkins not configured
- ✅ Tests verify end-to-end flow

### Code Quality:
- ✅ Pylint: No errors
- ✅ Pytest: All unit tests pass
- ✅ Mypy: No type errors
- ✅ Test coverage >80% for new code

### Acceptance Criteria:
- ✅ All acceptance criteria from issue #149 met
- ✅ All functional requirements working
- ✅ All quality requirements met

## Files Created/Modified

### New Files:
- `docs/configuration/CONFIG.md` (~300-400 lines)

### Modified Files:
- `README.md` - Add coordinator section (~40-50 lines)
- `tests/cli/commands/test_coordinator.py` - Add integration tests (~50-70 lines)

### Total New Lines: ~390-520 lines

## Post-Implementation Checklist

### Code Quality:
- [ ] All pylint checks pass
- [ ] All pytest unit tests pass (fast tests)
- [ ] All mypy type checks pass
- [ ] Test coverage >80% for new code

### Documentation:
- [ ] CONFIG.md is complete and accurate
- [ ] README.md updated with examples
- [ ] All file paths correct for Windows/Linux
- [ ] Troubleshooting section helpful

### Functionality:
- [ ] Command works end-to-end
- [ ] Error messages are helpful
- [ ] Config auto-creation works
- [ ] Validation catches all error cases
- [ ] Output format matches specification

### Testing:
- [ ] Unit tests comprehensive
- [ ] Integration tests can run (if Jenkins available)
- [ ] All edge cases covered
- [ ] Mock tests don't require external services

## Final Deliverable

After completing all 5 steps, you will have:

1. **Config template system** - Auto-creates user config
2. **Repository validation** - Validates config completeness
3. **CLI command** - Full coordinator test implementation
4. **CLI integration** - Command accessible via `mcp-coder coordinator test`
5. **Documentation** - Complete CONFIG.md and README updates
6. **Tests** - Unit tests + integration tests (>80% coverage)
7. **Quality** - All pylint, pytest, mypy checks passing

**Total implementation: ~600-700 lines of code (vs ~800-1000 for complex approach)**

## Next Steps (Post-Implementation)

After implementation complete:
1. Create pull request
2. Link to issue #149
3. Run all quality checks in CI
4. Manual testing with real Jenkins (if available)
5. Address review feedback

## Completion

🎉 **Congratulations!** You have successfully implemented the `mcp-coder coordinator test` command following TDD and KISS principles.

All CLAUDE.md requirements followed ✓
