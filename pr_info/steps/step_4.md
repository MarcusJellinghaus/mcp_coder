# Step 4: Implement GitHub Operations (Make Tests Pass)

## Objective
Implement the actual GitHub operations using PyGithub to make the failing test pass.

## WHERE
- File: `src/mcp_coder/utils/github_operations.py` (modify existing)

## WHAT
- Add PyGithub imports and GitHub client initialization
- Implement create_pull_request with actual GitHub API calls
- Implement get_pull_request with PR data retrieval
- Implement close_pull_request with state updates

## HOW
### Implementation Structure
```python
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

def _get_github_client() -> Optional[Github]:
    """Initialize GitHub client from config."""

def _get_repository() -> Optional[Repository]:
    """Get repository object from config."""

@log_function_call
def create_pull_request(title: str, body: str, head: str, base: str = "main") -> dict:
    """Create a pull request and return number/url."""

@log_function_call  
def get_pull_request(pr_number: int) -> dict:
    """Get PR details and return structured data."""

@log_function_call
def close_pull_request(pr_number: int) -> dict:
    """Close PR and return updated state."""
```

## ALGORITHM
```
1. Get GitHub token and repo URL from config
2. Initialize GitHub client and repository objects
3. For create: repo.create_pull() → extract number/url
4. For get: repo.get_pull() → extract details to dict
5. For close: pull.edit(state="closed") → return state
6. Handle errors gracefully, return empty dict on failure
```

## DATA
- **create_pull_request returns**: `{'number': pr.number, 'url': pr.html_url}`
- **get_pull_request returns**: `{'number': pr.number, 'title': pr.title, 'state': pr.state, 'url': pr.html_url}`
- **close_pull_request returns**: `{'number': pr.number, 'state': pr.state}`
- **Error handling**: Return `{}` on any exception

## LLM Prompt
```
You are implementing Step 4 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Replace the empty implementations in src/mcp_coder/utils/github_operations.py with actual PyGithub functionality to make the failing test pass.

Requirements:
- Add PyGithub imports (from github import Github, etc.)
- Create helper functions _get_github_client() and _get_repository()
- Use get_config_value("github", "token") and get_config_value("github", "test_repo_url")
- Implement the three main functions to return the exact dict structures expected by tests
- Handle errors gracefully by returning empty dict {} 
- Keep implementation minimal - just enough to pass the test
- Follow the @log_function_call decorator pattern

The test is currently failing because functions return empty dicts. Your implementation should make it pass by returning the correct data structures with actual GitHub API data.
```

## Verification
- [ ] PyGithub imports added
- [ ] Helper functions implemented for client/repo initialization
- [ ] create_pull_request creates actual PR and returns number/url
- [ ] get_pull_request retrieves PR data and returns structured dict
- [ ] close_pull_request closes PR and returns updated state
- [ ] Error handling returns empty dict on failures
- [ ] Integration test now passes
- [ ] Configuration reading works correctly
