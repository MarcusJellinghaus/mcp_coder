# Step 3: Integrate Branch Resolution into Coordinator

## Objective
Update the coordinator's `dispatch_workflow()` function to use the new `get_branch_with_pr_fallback()` method, replacing the existing `get_linked_branches()` call with enhanced error handling.

---

## WHERE: File Location
**Modify existing file:**
```
src/mcp_coder/cli/commands/coordinator/core.py
```

**Function to modify:**
- `dispatch_workflow()` function
- Lines 388-400 (approximately)
- Section handling branch resolution for `branch_strategy == "from_issue"`

---

## WHAT: Changes Required

### 1. Add Import
```python
# At top of file, add to existing imports from github_operations
from ....utils.github_operations.github_utils import parse_github_url
```

**Current imports (around line 12):**
```python
from ....utils.github_operations.issues import (
    CacheData,
    IssueBranchManager,
    IssueData,
    IssueManager,
    get_all_cached_issues,
)
```

**New import to add (around line 17):**
```python
from ....utils.github_operations.github_utils import parse_github_url
```

### 2. Replace Branch Resolution Logic

**BEFORE (lines 388-400):**
```python
else:  # from_issue
    branches = branch_manager.get_linked_branches(issue["number"])
    if not branches:
        logger.warning(
            f"No linked branch found for issue #{issue['number']}, skipping workflow dispatch"
        )
        return
    branch_name = branches[0]
```

**AFTER:**
```python
else:  # from_issue
    # Parse repo URL to extract owner and name for branch resolution
    parsed_url = parse_github_url(repo_config["repo_url"])
    if not parsed_url:
        logger.error(
            f"Invalid GitHub URL in repo config: {repo_config['repo_url']}"
        )
        return

    repo_owner, repo_name = parsed_url

    # Resolve branch with PR fallback (checks linkedBranches then draft/open PRs)
    branch_name = branch_manager.get_branch_with_pr_fallback(
        issue_number=issue["number"],
        repo_owner=repo_owner,
        repo_name=repo_name,
    )

    if not branch_name:
        logger.error(
            f"No branch found for issue #{issue['number']} \"{issue['title']}\"\n"
            f"  Checked: linkedBranches, draft/open PRs\n"
            f"  Issue URL: {issue['url']}\n"
            f"  Requirement: Issue must have linked branch or draft/open PR"
        )
        return
```

---

## HOW: Integration Points

### 1. Import Dependencies
```python
from ....utils.github_operations.github_utils import parse_github_url
# parse_github_url returns Optional[Tuple[str, str]] -> (owner, repo_name)
```

### 2. Error Handling Flow
```python
# Step 1: Parse repo URL
parsed_url = parse_github_url(repo_config["repo_url"])
if not parsed_url:
    # Log error and return early (skip this issue)
    # Other issues in queue will still be processed
    return

# Step 2: Resolve branch with fallback
branch_name = branch_manager.get_branch_with_pr_fallback(...)
if not branch_name:
    # Log comprehensive error and return early
    # Other issues in queue will still be processed
    return

# Step 3: Continue with workflow dispatch (existing code)
```

### 3. Non-Blocking Behavior
- URL parsing fails → log error, return (skip this issue)
- Branch resolution fails → log error, return (skip this issue)
- Other issues in the coordinator loop continue processing
- Consistent with existing coordinator error handling pattern

---

## ALGORITHM: Updated Logic Flow

```python
# In dispatch_workflow() function, branch_strategy == "from_issue" section:

# Step 1: Parse repo URL to get owner and name
parsed = parse_github_url(repo_config["repo_url"])
if not parsed:
    log_error("Invalid repo URL")
    return  # Skip this issue, continue with others

owner, name = parsed

# Step 2: Resolve branch with two-step fallback
branch = branch_manager.get_branch_with_pr_fallback(
    issue_number, owner, name
)

if not branch:
    log_error("No branch found after checking linkedBranches and PRs")
    return  # Skip this issue, continue with others

# Step 3: Continue with existing workflow dispatch
# (existing code from line 401 onwards remains unchanged)
```

---

## DATA: Function Context

### dispatch_workflow() Parameters
```python
def dispatch_workflow(
    issue: IssueData,                      # Issue being processed
    workflow_name: str,                    # "create-plan", "implement", "create-pr"
    repo_config: dict[str, str],           # Contains "repo_url" key
    jenkins_client: JenkinsClient,         # For job triggering
    issue_manager: IssueManager,           # For label updates
    branch_manager: IssueBranchManager,    # NEW METHOD USED HERE
    log_level: str,                        # Log level for workflow
) -> None:
```

### repo_config Structure
```python
{
    "repo_url": "https://github.com/owner/repo",  # Used for parsing
    "executor_job_path": "path/to/job",
    "github_credentials_id": "cred-id",
    "executor_os": "linux",
}
```

### parse_github_url() Return
```python
# Success
("MarcusJellinghaus", "mcp_coder")  # Tuple[str, str]

# Failure
None  # Optional[Tuple[str, str]]
```

---

## Complete Code Change

### Location: src/mcp_coder/cli/commands/coordinator/core.py

#### Change 1: Add Import (line ~17)
```python
from ....utils.github_operations.github_utils import parse_github_url
```

#### Change 2: Replace Branch Resolution (lines ~388-400)

**Find this code block:**
```python
    # Step 2: Determine branch name based on branch_strategy
    if workflow_config["branch_strategy"] == "main":
        branch_name = "main"
    else:  # from_issue
        branches = branch_manager.get_linked_branches(issue["number"])
        if not branches:
            logger.warning(
                f"No linked branch found for issue #{issue['number']}, skipping workflow dispatch"
            )
            return
        branch_name = branches[0]
```

**Replace with:**
```python
    # Step 2: Determine branch name based on branch_strategy
    if workflow_config["branch_strategy"] == "main":
        branch_name = "main"
    else:  # from_issue
        # Parse repo URL to extract owner and name for branch resolution
        parsed_url = parse_github_url(repo_config["repo_url"])
        if not parsed_url:
            logger.error(
                f"Invalid GitHub URL in repo config: {repo_config['repo_url']}"
            )
            return

        repo_owner, repo_name = parsed_url

        # Resolve branch with PR fallback (checks linkedBranches then draft/open PRs)
        branch_name = branch_manager.get_branch_with_pr_fallback(
            issue_number=issue["number"],
            repo_owner=repo_owner,
            repo_name=repo_name,
        )

        if not branch_name:
            logger.error(
                f"No branch found for issue #{issue['number']} \"{issue['title']}\"\n"
                f"  Checked: linkedBranches, draft/open PRs\n"
                f"  Issue URL: {issue['url']}\n"
                f"  Requirement: Issue must have linked branch or draft/open PR"
            )
            return
```

---

## Testing Strategy

### Manual Testing Scenarios

#### Scenario 1: Linked Branch Exists
```
Setup: Issue #123 has linked branch "123-feature"
Expected: 
  - Branch resolved via linkedBranches (fast path)
  - Workflow dispatched successfully
  - No PR query needed
```

#### Scenario 2: Draft PR Exists
```
Setup: Issue #123, no linkedBranches, has draft PR #42
Expected:
  - linkedBranches returns empty
  - PR fallback finds draft PR
  - Branch resolved to PR's headRefName
  - Workflow dispatched successfully
```

#### Scenario 3: No Branch or PR
```
Setup: Issue #123, no linkedBranches, no draft/open PRs
Expected:
  - Error logged: "No branch found for issue #123"
  - Workflow skipped
  - Coordinator continues with next issue
```

#### Scenario 4: Invalid Repo URL
```
Setup: repo_config["repo_url"] = "invalid-url"
Expected:
  - Error logged: "Invalid GitHub URL"
  - Workflow skipped
  - Coordinator continues with next issue
```

### Automated Testing
- Existing coordinator tests should still pass
- New method is already tested in Step 1
- Integration verified by manual testing

---

## LLM Prompt for Implementation

```
I need to implement Step 3 of the branch resolution feature.

CONTEXT:
- Read pr_info/steps/summary.md for architectural context
- Read pr_info/steps/step_2.md to understand the new method
- Step 2 implemented get_branch_with_pr_fallback(), now integrate it into coordinator

TASK:
Update src/mcp_coder/cli/commands/coordinator/core.py to use the new branch resolution method

CHANGES REQUIRED:
1. Add import at top of file (line ~17):
   from ....utils.github_operations.github_utils import parse_github_url

2. Replace branch resolution logic in dispatch_workflow() function (lines ~388-400):
   - Find the "else: # from_issue" block
   - Replace the simple get_linked_branches() call
   - Add URL parsing step
   - Add comprehensive error handling
   - Use the new get_branch_with_pr_fallback() method

EXACT CODE:
Use the complete code replacement from step_3.md section "Complete Code Change"

ERROR HANDLING:
- Invalid URL → log error, return early (non-blocking)
- No branch found → log comprehensive error with details, return early (non-blocking)
- Both cases allow coordinator to continue processing other issues

VERIFICATION:
1. Read the updated code to ensure changes are correct
2. Check that error handling is non-blocking (uses return, not raise)
3. Verify logging provides actionable information
4. Ensure existing coordinator tests still pass

DELIVERABLE:
- 1 import added
- ~15 lines changed in dispatch_workflow()
- Enhanced error messages
- Non-blocking error handling preserved
```

---

## Expected Outcome
- ✅ Import added for `parse_github_url`
- ✅ Branch resolution uses new fallback method
- ✅ URL parsing validates repo_config
- ✅ Comprehensive error logging
- ✅ Non-blocking error handling (continues with other issues)
- ✅ Existing tests still pass
- ✅ Manual testing confirms all scenarios work

**Next Step:** Step 4 will run code quality checks and verify everything works end-to-end.
