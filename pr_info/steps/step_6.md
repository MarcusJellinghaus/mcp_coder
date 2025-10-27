# Step 6: Fix Field Name Inconsistency in Documentation

## Overview
Fix inconsistent field naming in README.md where some examples show `test_job_path` but the implementation uses `executor_test_path`. This ensures documentation matches the actual working code.

## LLM Prompt
```
You are implementing Step 6 of the coordinator test command fixes.

Read pr_info/steps/summary.md for context.
Read pr_info/steps/decisions.md for the decision rationale.

Your task: Update README.md to consistently use executor_test_path instead of test_job_path.

Requirements:
1. Find all occurrences of test_job_path in README.md
2. Replace with executor_test_path
3. Verify consistency with code implementation
4. No code changes needed

Follow the specifications in this step file exactly.
```

## Phase 6A: Identify Occurrences

### WHERE
File: `README.md`

### WHAT
Search for and replace all instances of `test_job_path` with `executor_test_path`

### HOW
Manual search and replace in README.md:
1. Search for: `test_job_path`
2. Replace with: `executor_test_path`
3. Review context to ensure replacement makes sense

## Phase 6B: Update README.md

### Expected Occurrences

Based on the diff, the field appears in configuration examples around lines 35-100.

### Sections to Check:
1. Configuration Template section
2. Configuration Structure section  
3. Example repository configurations
4. Any inline code blocks showing TOML config

### Changes Required

**Before:**
```toml
[coordinator.repos.repo_a]
repo_url = "https://github.com/your-org/repo_a.git"
test_job_path = "jenkins_folder_a/test-job-a"
github_credentials_id = "github-general-pat"
```

**After:**
```toml
[coordinator.repos.repo_a]
repo_url = "https://github.com/your-org/repo_a.git"
executor_test_path = "jenkins_folder_a/test-job-a"
github_credentials_id = "github-general-pat"
```

## Phase 6C: Verification

### Manual Verification Steps
1. Search README.md for any remaining `test_job_path` occurrences
2. Verify all config examples use `executor_test_path`
3. Check that field name matches coordinator.py implementation
4. Ensure no broken references

### Verification Commands
```bash
# Search for any remaining occurrences
grep -n "test_job_path" README.md

# Should return no results after fix
```

## Phase 6D: Cross-Reference with Code

### Verify Consistency

Check that field name matches implementation:

**In coordinator.py:**
```python
def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    section = f"coordinator.repos.{repo_name}"
    
    repo_url = get_config_value(section, "repo_url")
    executor_test_path = get_config_value(section, "executor_test_path")  # ✓ Correct
    github_credentials_id = get_config_value(section, "github_credentials_id")
```

**In README.md after fix:**
```toml
[coordinator.repos.mcp_coder]
repo_url = "https://github.com/user/mcp_coder.git"
executor_test_path = "MCP_Coder/mcp-coder-test-job"  # ✓ Matches code
github_credentials_id = "github-general-pat"
```

## Success Criteria

- ✅ All occurrences of `test_job_path` replaced with `executor_test_path` in README.md
- ✅ Field name matches code implementation in coordinator.py
- ✅ Field name matches config template in user_config.py
- ✅ No broken references or inconsistencies
- ✅ Documentation is clear and correct

## Files Modified

### Modified:
- `README.md` - Replace `test_job_path` with `executor_test_path` (multiple occurrences)

### Total Changes: ~3-5 replacements in README.md

## Estimated Time
~10-15 minutes

## Next Step
After verification complete, proceed to **Step 7: Remove build_token from Documentation**.
