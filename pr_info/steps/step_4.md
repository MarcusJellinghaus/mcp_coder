# Step 4: Implement GitHub Operations (Make Tests Pass)

## Objective
Implement the actual GitHub operations using PyGithub to make the failing test pass.

## WHERE
- Files: 
  - `src/mcp_coder/utils/github_operations/__init__.py` (modify existing)
  - `src/mcp_coder/utils/github_operations/gh_pull_requests.py` (modify existing)

## WHAT
- Add PyGithub imports and GitHub client initialization
- Implement create_pull_request with actual GitHub API calls
- Implement get_pull_request with PR data retrieval
- Implement close_pull_request with state updates
- Implement list_pull_requests with PR listing and filtering

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
def create_pull_request(repo_url: str, title: str, body: str, head: str, base: str = "main") -> dict:
    """Create a pull request and return number/url."""

@log_function_call  
def get_pull_request(repo_url: str, pr_number: int) -> dict:
    """Get PR details and return structured data."""

@log_function_call
def list_pull_requests(repo_url: str, state: str = "open") -> list:
    """List PRs and return filtered results."""

@log_function_call
def close_pull_request(repo_url: str, pr_number: int) -> dict:
    """Close PR and return updated state."""
```

## ALGORITHM
```
1. Parse repo_url parameter to get repository information
2. Get GitHub token from config
3. Initialize GitHub client and repository objects from repo_url
4. For create: repo.create_pull() → extract number/url
5. For get: repo.get_pull() → extract details to dict
6. For list: repo.get_pulls(state=state) → extract list of PR summaries
7. For close: pull.edit(state="closed") → return state
8. Handle errors gracefully, return empty dict/list on failure
```

## DATA
- **create_pull_request returns**: `{'number': pr.number, 'url': pr.html_url}`
- **get_pull_request returns**: `{'number': pr.number, 'title': pr.title, 'state': pr.state, 'url': pr.html_url}`
- **list_pull_requests returns**: `[{'number': pr.number, 'title': pr.title, 'state': pr.state}]`
- **close_pull_request returns**: `{'number': pr.number, 'state': pr.state}`
- **Error handling**: Return `{}` or `[]` on any exception

## LLM Prompt
```
You are implementing Step 4 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Replace the empty implementations in the GitHub operations package with actual PyGithub functionality to make the failing test pass.

Requirements:
- Add PyGithub imports (from github import Github, etc.)
- Create helper functions _get_github_client() and _get_repository()
- Use get_config_value("github", "token") for authentication
- Parse repo_url parameter to get repository (e.g., "https://github.com/user/repo")
- Implement the four main functions to return the exact dict/list structures expected by tests
- Handle errors gracefully by returning empty dict {} or list []
- Keep implementation minimal - just enough to pass the test
- Follow the @log_function_call decorator pattern

The test is currently failing because functions return empty dicts/lists. Your implementation should make it pass by returning the correct data structures with actual GitHub API data.
```

## Verification
- [ ] PyGithub imports added
- [ ] Helper functions implemented for client/repo initialization
- [ ] create_pull_request creates actual PR and returns number/url
- [ ] get_pull_request retrieves PR data and returns structured dict
- [ ] list_pull_requests retrieves PR list and returns structured list
- [ ] close_pull_request closes PR and returns updated state
- [ ] Error handling returns empty dict/list on failures
- [ ] Integration test now passes
- [ ] Configuration reading works correctly
