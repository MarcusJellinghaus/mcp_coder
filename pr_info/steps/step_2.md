# Step 2: Implement Core Branch Resolution Method

## Objective
Implement `get_branch_with_pr_fallback()` method in `IssueBranchManager` to make all tests from Step 1 pass. Follow the two-step fallback strategy: linkedBranches → PR timeline.

---

## WHERE: File Location
**Modify existing file:**
```
src/mcp_coder/utils/github_operations/issues/branch_manager.py
```

**Location in file:**
- Add method after existing `get_linked_branches()` method
- Before `create_remote_branch_for_issue()` method
- Approximately line 180 (after line 179 in current file)

---

## WHAT: Method Implementation

### Method Signature
```python
@log_function_call
@_handle_github_errors(default_return=None)
def get_branch_with_pr_fallback(
    self,
    issue_number: int,
    repo_owner: str,
    repo_name: str
) -> Optional[str]:
    """Get branch for issue via linkedBranches or open PR fallback.

    Resolution order:
    1. Query linkedBranches (fast, primary source)
    2. Query issue timeline for open PRs (slower, fallback)

    Note:
        Timeline query limited to first 100 cross-references. This is sufficient
        for typical usage (most issues have <10 cross-references).

    Args:
        issue_number: Issue number to resolve branch for
        repo_owner: Repository owner (e.g., "MarcusJellinghaus")
        repo_name: Repository name (e.g., "mcp_coder")

    Returns:
        Branch name if exactly one source found, None otherwise

    Examples:
        >>> manager = IssueBranchManager(Path.cwd())
        >>> branch = manager.get_branch_with_pr_fallback(123, "owner", "repo")
        >>> if branch:
        ...     print(f"Found branch: {branch}")
        ... else:
        ...     print("No branch found")
    """
```

### Return Values
- **Success cases**:
  - linkedBranches returns branch → return first branch name (str)
  - PR timeline has single draft/open PR → return headRefName (str)
- **Failure cases**:
  - Multiple PRs found → return None, log warning
  - No branches/PRs found → return None
  - Invalid issue number → return None
  - API errors → return None (handled by decorator)

---

## HOW: Integration Points

### 1. Decorators (Already Exist)
```python
from mcp_coder.utils.log_utils import log_function_call
from ..base_manager import _handle_github_errors

@log_function_call  # Logs function entry/exit
@_handle_github_errors(default_return=None)  # Catches GitHub API errors
```

### 2. Imports Required
```python
from typing import Optional  # Already imported
# No new imports needed - reuse existing
```

### 3. Dependencies
- `self.get_linked_branches(issue_number)` - existing method
- `self._validate_issue_number(issue_number)` - existing method
- `self._github_client._Github__requester.graphql_query()` - existing pattern
- `logger` - existing module-level logger

---

## ALGORITHM: Core Logic (Pseudocode)

```python
# Step 1: Validate input
if not _validate_issue_number(issue_number):
    return None

# Step 2: Try linkedBranches (primary path)
branches = self.get_linked_branches(issue_number)
if branches:
    logger.debug(f"Resolved via linkedBranches: {branches[0]}")
    return branches[0]  # Short-circuit on success

# Step 3: Fallback - Query PR timeline via GraphQL
execute_timeline_query(owner, repo, issue_number)
parse_timeline_response()
filter_prs = [pr for pr in all_prs if pr.state == OPEN]

# Step 4: Handle results
if len(filter_prs) == 1:
    logger.debug(f"Resolved via PR #{filter_prs[0].number}: {filter_prs[0].headRefName}")
    return filter_prs[0].headRefName
elif len(filter_prs) > 1:
    logger.warning(f"Multiple PRs found: #{pr1}, #{pr2}, ...")
    return None
else:
    logger.debug("No branch found (checked linkedBranches and PRs)")
    return None
```

---

## DATA: GraphQL Timeline Query

### Query String
```python
TIMELINE_QUERY = """
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      timelineItems(itemTypes: [CROSS_REFERENCED_EVENT], first: 100) {
        nodes {
          __typename
          ... on CrossReferencedEvent {
            source {
              ... on PullRequest {
                number
                state
                isDraft
                headRefName
              }
            }
          }
        }
      }
    }
  }
}
"""
```

### Query Variables
```python
variables = {
    "owner": repo_owner,
    "repo": repo_name,
    "issueNumber": issue_number,
}
```

### Expected Response Structure
```python
{
    "data": {
        "repository": {
            "issue": {
                "timelineItems": {
                    "nodes": [
                        {
                            "__typename": "CrossReferencedEvent",
                            "source": {
                                "number": 42,
                                "state": "OPEN",  # or "CLOSED", "MERGED"
                                "isDraft": True,   # or False
                                "headRefName": "123-feature-branch"
                            }
                        },
                        # ... more nodes
                    ]
                }
            }
        }
    }
}
```

---

## Implementation Details

### Section 1: Input Validation
```python
# Validate issue number (reuse existing method)
if not self._validate_issue_number(issue_number):
    return None
```

### Section 2: Primary Path - linkedBranches
```python
# Try linkedBranches first (fast path)
branches = self.get_linked_branches(issue_number)
if branches:
    logger.debug(
        f"Issue #{issue_number}: resolved branch '{branches[0]}' via linkedBranches"
    )
    return branches[0]

logger.debug(
    f"Issue #{issue_number}: no linkedBranches found, trying PR fallback"
)
```

### Section 3: Fallback - PR Timeline Query
```python
# GraphQL query for PR timeline
query = """
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      timelineItems(itemTypes: [CROSS_REFERENCED_EVENT], first: 100) {
        nodes {
          __typename
          ... on CrossReferencedEvent {
            source {
              ... on PullRequest {
                number
                state
                isDraft
                headRefName
              }
            }
          }
        }
      }
    }
  }
}
"""

variables = {
    "owner": repo_owner,
    "repo": repo_name,
    "issueNumber": issue_number,
}

# Execute GraphQL query
_, result = self._github_client._Github__requester.graphql_query(
    query=query, variables=variables
)
```

### Section 4: Parse Timeline Response
```python
# Parse response and extract PRs
try:
    issue_data = result.get("data", {}).get("repository", {}).get("issue")
    if issue_data is None:
        logger.warning(f"Issue #{issue_number} not found in timeline query")
        return None

    timeline_nodes = issue_data.get("timelineItems", {}).get("nodes", [])
    
    # Filter for draft/open PRs
    open_or_draft_prs = []
    for node in timeline_nodes:
        if not node or node.get("__typename") != "CrossReferencedEvent":
            continue
        
        source = node.get("source")
        if not source:
            continue
        
        # Only consider PRs with OPEN state (includes drafts)
        state = source.get("state")
        is_draft = source.get("isDraft", False)
        
        if state == "OPEN":
            open_or_draft_prs.append({
                "number": source.get("number"),
                "headRefName": source.get("headRefName"),
                "state": state,
                "isDraft": is_draft,
            })

except (KeyError, TypeError) as e:
    logger.error(f"Error parsing timeline response: {e}")
    return None
```

### Section 5: Handle Multiple PRs or Return Branch
```python
# Handle results based on number of PRs found
if len(open_or_draft_prs) == 0:
    logger.debug(
        f"Issue #{issue_number}: no draft/open PRs found in timeline"
    )
    return None

elif len(open_or_draft_prs) == 1:
    pr = open_or_draft_prs[0]
    branch_name = pr["headRefName"]
    logger.debug(
        f"Issue #{issue_number}: resolved branch '{branch_name}' "
        f"via PR #{pr['number']} (draft={pr['isDraft']}, state={pr['state']})"
    )
    return branch_name

else:
    # Multiple PRs found - ambiguous
    pr_numbers = [pr["number"] for pr in open_or_draft_prs]
    logger.warning(
        f"Issue #{issue_number}: multiple draft/open PRs found: "
        f"{pr_numbers}. Cannot determine branch unambiguously."
    )
    return None
```

---

## Complete Implementation

```python
@log_function_call
@_handle_github_errors(default_return=None)
def get_branch_with_pr_fallback(
    self,
    issue_number: int,
    repo_owner: str,
    repo_name: str,
) -> Optional[str]:
    """Get branch for issue via linkedBranches or draft/open PR fallback.

    Resolution order:
    1. Query linkedBranches (fast, primary source)
    2. Query issue timeline for draft/open PRs (slower, fallback)

    Args:
        issue_number: Issue number to resolve branch for
        repo_owner: Repository owner (e.g., "MarcusJellinghaus")
        repo_name: Repository name (e.g., "mcp_coder")

    Returns:
        Branch name if exactly one source found, None otherwise

    Examples:
        >>> manager = IssueBranchManager(Path.cwd())
        >>> branch = manager.get_branch_with_pr_fallback(123, "owner", "repo")
        >>> if branch:
        ...     print(f"Found branch: {branch}")
        ... else:
        ...     print("No branch found")
    """
    # Validate issue number
    if not self._validate_issue_number(issue_number):
        return None

    # Step 1: Try linkedBranches first (fast path)
    branches = self.get_linked_branches(issue_number)
    if branches:
        logger.debug(
            f"Issue #{issue_number}: resolved branch '{branches[0]}' via linkedBranches"
        )
        return branches[0]

    logger.debug(
        f"Issue #{issue_number}: no linkedBranches found, trying PR fallback"
    )

    # Step 2: Fallback - Query PR timeline via GraphQL
    query = """
    query($owner: String!, $repo: String!, $issueNumber: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issueNumber) {
          timelineItems(itemTypes: [CROSS_REFERENCED_EVENT], first: 100) {
            nodes {
              __typename
              ... on CrossReferencedEvent {
                source {
                  ... on PullRequest {
                    number
                    state
                    isDraft
                    headRefName
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "owner": repo_owner,
        "repo": repo_name,
        "issueNumber": issue_number,
    }

    # Execute GraphQL query
    _, result = self._github_client._Github__requester.graphql_query(
        query=query, variables=variables
    )

    # Step 3: Parse response and extract draft/open PRs
    try:
        issue_data = result.get("data", {}).get("repository", {}).get("issue")
        if issue_data is None:
            logger.warning(f"Issue #{issue_number} not found in timeline query")
            return None

        timeline_nodes = issue_data.get("timelineItems", {}).get("nodes", [])

        # Filter for draft/open PRs
        open_or_draft_prs = []
        for node in timeline_nodes:
            if not node or node.get("__typename") != "CrossReferencedEvent":
                continue

            source = node.get("source")
            if not source:
                continue

            # Check if it's a PR with OPEN state or isDraft=True
            state = source.get("state")
            is_draft = source.get("isDraft", False)

            if state == "OPEN" or is_draft:
                open_or_draft_prs.append(
                    {
                        "number": source.get("number"),
                        "headRefName": source.get("headRefName"),
                        "state": state,
                        "isDraft": is_draft,
                    }
                )

    except (KeyError, TypeError) as e:
        logger.error(f"Error parsing timeline response: {e}")
        return None

    # Step 4: Handle results based on number of PRs found
    if len(open_or_draft_prs) == 0:
        logger.debug(f"Issue #{issue_number}: no draft/open PRs found in timeline")
        return None

    elif len(open_or_draft_prs) == 1:
        pr = open_or_draft_prs[0]
        branch_name = pr["headRefName"]
        logger.debug(
            f"Issue #{issue_number}: resolved branch '{branch_name}' "
            f"via PR #{pr['number']} (draft={pr['isDraft']}, state={pr['state']})"
        )
        return branch_name

    else:
        # Multiple PRs found - ambiguous
        pr_numbers = [pr["number"] for pr in open_or_draft_prs]
        logger.warning(
            f"Issue #{issue_number}: multiple draft/open PRs found: "
            f"{pr_numbers}. Cannot determine branch unambiguously."
        )
        return None
```

---

## LLM Prompt for Implementation

```
I need to implement Step 2 of the branch resolution feature.

CONTEXT:
- Read pr_info/steps/summary.md for architectural context
- Read pr_info/steps/step_1.md to understand the test requirements
- Step 1 created failing tests, now we implement the method to make them pass

TASK:
Add the get_branch_with_pr_fallback() method to src/mcp_coder/utils/github_operations/issues/branch_manager.py

LOCATION:
- Add method after get_linked_branches() (around line 180)
- Before create_remote_branch_for_issue() method

REQUIREMENTS:
1. Copy the complete implementation from step_2.md
2. Follow the algorithm: validate input → try linkedBranches → fallback to PR timeline
3. Use @log_function_call and @_handle_github_errors(default_return=None) decorators
4. Include comprehensive docstring with Examples section
5. GraphQL query should match the structure in step_2.md exactly
6. Filter PRs by state=="OPEN" only (includes both draft and non-draft open PRs)
7. Return None for multiple PRs (log warning with PR numbers)
8. Return branch name for single PR
9. Use logger.debug() for success paths, logger.warning() for issues

VERIFICATION:
After implementation, run:
1. pytest tests/utils/github_operations/issues/test_branch_resolution.py -v
2. All 8 tests from Step 1 should now PASS
3. No existing tests should break

DELIVERABLE:
- ~100 lines added to branch_manager.py
- All Step 1 tests passing
- Method follows existing code style and patterns
```

---

## Expected Outcome
- ✅ Method implemented in `branch_manager.py`
- ✅ All 8 tests from Step 1 now pass
- ✅ Decorator pattern followed
- ✅ Comprehensive logging
- ✅ Two-step fallback logic working
- ✅ No regressions in existing tests

**Next Step:** Step 3 will integrate this method into the coordinator workflow.
