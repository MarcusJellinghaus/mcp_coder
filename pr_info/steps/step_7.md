# Step 7: Remove build_token from Documentation

## Overview
Remove all references to `build_token` from documentation (README.md and CONFIG.md) since the implementation does not use this parameter. The `token` parameter in `JenkinsClient.start_job()` is kept for future use but is not currently utilized.

## LLM Prompt
```
You are implementing Step 7 of the coordinator test command fixes.

Read pr_info/steps/summary.md for context.
Read pr_info/steps/decisions.md for the decision rationale (Issue #2).

Your task: Remove all build_token references from README.md and CONFIG.md.

Requirements:
1. Remove build_token field from all TOML config examples
2. Remove build_token from field description tables
3. Remove build_token from explanatory text
4. Keep the token parameter in JenkinsClient.start_job() code (no code changes)
5. Ensure remaining documentation is coherent after removal

Follow the specifications in this step file exactly.
```

## Phase 7A: Identify Occurrences

### WHERE
Files: 
- `README.md`
- `docs/configuration/CONFIG.md`

### WHAT
Remove all occurrences of `build_token` field from documentation

### Occurrences to Remove

#### In README.md:
1. Configuration template examples (around line 35-80)
2. Example repository configurations
3. Any explanatory text about build tokens

#### In CONFIG.md:
1. Configuration template section
2. Field description tables
3. "About build_token" explanatory sections
4. Any troubleshooting or setup instructions related to build tokens

## Phase 7B: Update README.md

### Changes Required

**Before:**
```toml
[coordinator.repos.repo_a]
repo_url = "https://github.com/your-org/repo_a.git"
executor_test_path = "jenkins_folder_a/test-job-a"
github_credentials_id = "github-general-pat"
build_token = "your-build-token-here"  # Required
```

**After:**
```toml
[coordinator.repos.repo_a]
repo_url = "https://github.com/your-org/repo_a.git"
executor_test_path = "jenkins_folder_a/test-job-a"
github_credentials_id = "github-general-pat"
```

### Remove from Multiple Sections

1. **Configuration Structure section** - Remove build_token line
2. **Example configurations** - Remove build_token from all repo examples
3. **Auto-generated template** - Remove build_token lines and comments

## Phase 7C: Update CONFIG.md

### Changes Required

#### 1. Configuration Template Section

**Remove these lines:**
```toml
build_token = "your-build-token-here"  # Required
```

From all repository configuration examples.

#### 2. Field Description Table

**Before:**
```markdown
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `repo_url` | string | Git repository HTTPS URL | Yes |
| `executor_test_path` | string | Jenkins job path (folder/job-name) | Yes |
| `github_credentials_id` | string | Jenkins GitHub credentials ID | Yes |
| `build_token` | string | Per-job build authentication token | **Yes** |
```

**After:**
```markdown
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `repo_url` | string | Git repository HTTPS URL | Yes |
| `executor_test_path` | string | Jenkins job path (folder/job-name) | Yes |
| `github_credentials_id` | string | Jenkins GitHub credentials ID | Yes |
```

#### 3. Remove "About build_token" Section

Remove entire section explaining build_token setup, including:
- How to configure build tokens in Jenkins
- Why build tokens are required
- Security implications of build tokens

#### 4. Update Example Configurations

Remove build_token from all example repository configurations throughout the document.

## Phase 7D: Verification

### Manual Verification Steps

1. **Search for remaining occurrences:**
   ```bash
   grep -rn "build_token" README.md docs/configuration/CONFIG.md
   # Should return no results after fix
   ```

2. **Verify table formatting:**
   - Check that field description tables render correctly
   - Ensure no broken markdown after line removal

3. **Check documentation flow:**
   - Read through configuration sections
   - Ensure removal doesn't leave dangling references
   - Verify examples are complete without build_token

4. **Verify only 3 required fields:**
   - `repo_url`
   - `executor_test_path`
   - `github_credentials_id`

### Code Verification

**Confirm code does NOT use build_token:**

```python
# In coordinator.py - load_repo_config()
def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    # ...
    repo_url = get_config_value(section, "repo_url")
    executor_test_path = get_config_value(section, "executor_test_path")
    github_credentials_id = get_config_value(section, "github_credentials_id")
    # ✓ No build_token loaded
    
    return {
        "repo_url": repo_url,
        "executor_test_path": executor_test_path,
        "github_credentials_id": github_credentials_id,
    }

# In coordinator.py - execute_coordinator_test()
queue_id = client.start_job(validated_config["executor_test_path"], params)
# ✓ No token parameter passed
```

**Confirm token parameter still exists but unused:**

```python
# In jenkins_operations/client.py
def start_job(
    self,
    job_path: str,
    params: Optional[dict[str, Any]] = None,
    token: Optional[str] = None,  # ✓ Still exists for future use
) -> int:
```

## Success Criteria

- ✅ All `build_token` references removed from README.md
- ✅ All `build_token` references removed from CONFIG.md
- ✅ Field description tables only show 3 required fields
- ✅ No dangling references or incomplete sentences
- ✅ Documentation flows naturally without build_token mentions
- ✅ Token parameter remains in JenkinsClient.start_job() code (unchanged)
- ✅ Examples are complete and functional

## Files Modified

### Modified:
- `README.md` - Remove build_token from all config examples (~5-8 lines removed)
- `docs/configuration/CONFIG.md` - Remove build_token from template, tables, and explanatory text (~15-20 lines removed)

### Total Changes: ~20-28 lines removed across 2 files

## Estimated Time
~20-30 minutes

## Next Step
After verification complete, proceed to **Step 8: Implement DEFAULT_TEST_COMMAND Constant**.
