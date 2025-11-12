# Step 4: Update Default Config Template

## Context
Reference: `pr_info/steps/summary.md`

This step updates the default configuration template to include documentation and examples for the new `executor_os` field. This ensures new users understand how to configure Windows executors.

## Objective
Update the default config template in `create_default_config()` to:
1. Document the `executor_os` field
2. Provide examples for both Windows and Linux executors
3. Maintain backward compatibility

## WHERE

**File**: `src/mcp_coder/utils/user_config.py`

**Function**: `create_default_config()` (around line 115)

**Section**: Template string for `[coordinator.repos.*]` sections

## WHAT

### Modified Function

#### `create_default_config()`
Add `executor_os` field to repository configuration examples.

**Signature**: (unchanged)
```python
@log_function_call
def create_default_config() -> bool:
```

**Change**: Update `template` string to include `executor_os` field with comments.

## HOW

### Integration Points

**No new imports needed** - only modifying string template

**Documentation style**: Follow existing comment pattern in template

### Template Format

Add `executor_os` field to each repository example with:
- Comment explaining valid values
- Comment explaining default behavior
- Example value in each repository section

## ALGORITHM

```
1. Locate template string in create_default_config()
2. Find [coordinator.repos.*] section examples
3. After github_credentials_id field, add:
   - Blank line
   - Comment explaining executor_os
   - executor_os field with value
4. Update both repository examples (mcp_coder and mcp_server_filesystem)
5. Ensure consistent formatting
```

## DATA

### Updated Template Section

The `[coordinator.repos.*]` sections should include:

```toml
[coordinator.repos.mcp_coder]
repo_url = "https://github.com/your-org/mcp_coder.git"
executor_test_path = "Tests/mcp-coder-coordinator-test"
github_credentials_id = "github-general-pat"
# executor_os: "windows" or "linux" (default: "linux")
# Use "windows" for Windows Jenkins executors, "linux" for Linux/container executors
executor_os = "linux"

[coordinator.repos.mcp_server_filesystem]
repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
executor_test_path = "Tests/mcp-filesystem-coordinator-test"
github_credentials_id = "github-general-pat"
executor_os = "linux"

# Example Windows executor configuration:
# [coordinator.repos.windows_project]
# repo_url = "https://github.com/your-org/windows-app.git"
# executor_test_path = "Windows/Executor/Test"
# github_credentials_id = "github-general-pat"
# executor_os = "windows"
```

### Complete Updated Template

```python
template = """# MCP Coder Configuration
# Update with your actual credentials and repository information

[github]
# GitHub authentication
# Environment variable (higher priority): GITHUB_TOKEN
token = "ghp_your_github_personal_access_token_here"

[jenkins]
# Jenkins server configuration
# Environment variables (higher priority): JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
server_url = "https://jenkins.example.com:8080"
username = "your-jenkins-username"
api_token = "your-jenkins-api-token"
test_job = "Tests/mcp-coder-simple-test"  # Job for integration tests
test_job_coordination = "Tests/mcp-coder-coordinator-test"  # Job for coordinator tests

# Coordinator test repositories
# Add your repositories here following this pattern

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/your-org/mcp_coder.git"
executor_test_path = "Tests/mcp-coder-coordinator-test"
github_credentials_id = "github-general-pat"
# executor_os: "windows" or "linux" (default: "linux")
# Use "windows" for Windows Jenkins executors, "linux" for Linux/container executors
executor_os = "linux"

[coordinator.repos.mcp_server_filesystem]
repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
executor_test_path = "Tests/mcp-filesystem-coordinator-test"
github_credentials_id = "github-general-pat"
executor_os = "linux"

# Example Windows executor configuration:
# [coordinator.repos.windows_project]
# repo_url = "https://github.com/your-org/windows-app.git"
# executor_test_path = "Windows/Executor/Test"
# github_credentials_id = "github-general-pat"
# executor_os = "windows"

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# executor_test_path = "Tests/your-repo-coordinator-test"
# github_credentials_id = "github-credentials-id"
# executor_os = "linux"
"""
```

## Implementation Steps

1. Open `src/mcp_coder/utils/user_config.py`

2. Locate the `create_default_config()` function (around line 115)

3. Find the `template` variable assignment

4. Locate the first repository example:
   ```python
   [coordinator.repos.mcp_coder]
   repo_url = "https://github.com/your-org/mcp_coder.git"
   executor_test_path = "Tests/mcp-coder-coordinator-test"
   github_credentials_id = "github-general-pat"
   ```

5. After `github_credentials_id`, add:
   ```toml
   # executor_os: "windows" or "linux" (default: "linux")
   # Use "windows" for Windows Jenkins executors, "linux" for Linux/container executors
   executor_os = "linux"
   ```

6. Repeat for the second repository example (`mcp_server_filesystem`):
   ```toml
   [coordinator.repos.mcp_server_filesystem]
   repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
   executor_test_path = "Tests/mcp-filesystem-coordinator-test"
   github_credentials_id = "github-general-pat"
   executor_os = "linux"
   ```

7. Add Windows example in commented section before "Add more repositories as needed":
   ```toml
   # Example Windows executor configuration:
   # [coordinator.repos.windows_project]
   # repo_url = "https://github.com/your-org/windows-app.git"
   # executor_test_path = "Windows/Executor/Test"
   # github_credentials_id = "github-general-pat"
   # executor_os = "windows"
   ```

8. Update the final template comment to include `executor_os`:
   ```toml
   # Add more repositories as needed:
   # [coordinator.repos.your_repo_name]
   # repo_url = "https://github.com/your-org/your_repo.git"
   # executor_test_path = "Tests/your-repo-coordinator-test"
   # github_credentials_id = "github-credentials-id"
   # executor_os = "linux"
   ```

9. Run code quality checks:
   ```bash
   mcp__code-checker__run_pylint_check()
   mcp__code-checker__run_mypy_check()
   ```

## Testing

### Manual Verification

1. Delete existing config file (if in test environment):
   ```bash
   rm ~/.config/mcp_coder/config.toml  # Linux/macOS
   # or
   del %USERPROFILE%\.mcp_coder\config.toml  # Windows
   ```

2. Run coordinator command to trigger config creation:
   ```bash
   mcp-coder coordinator test mcp_coder main
   ```

3. Verify generated config includes:
   - `executor_os` field in repository examples
   - Comment explaining valid values
   - Windows example in commented section

### Automated Testing

No automated tests needed for this step - it's a documentation/template update.

## Validation

- Config file should be well-formed TOML
- Comments should be clear and helpful
- Examples should cover both Windows and Linux cases
- Default values should be appropriate (linux)

## LLM Prompt for Implementation

```
I need to implement Step 4 of the Windows support implementation.

Context:
- Read pr_info/steps/summary.md for overall architecture
- Read pr_info/steps/step_4.md for detailed requirements

Task:
Update the default config template in src/mcp_coder/utils/user_config.py:

1. Add executor_os field to [coordinator.repos.mcp_coder] example
2. Add executor_os field to [coordinator.repos.mcp_server_filesystem] example
3. Add commented Windows executor example
4. Update final repository template comment to include executor_os

Requirements:
- Use exact template format from step_4.md
- Include helpful comments explaining valid values
- Default to "linux" for backward compatibility
- Follow existing TOML formatting style

After implementation:
- Run pylint and mypy checks using MCP tools
- Fix any issues found
- Verify template is valid TOML format
```
