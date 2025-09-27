# Step 4: Implement PullRequestManager (Make Tests Pass)

## Objective
Implement the actual PullRequestManager functionality using PyGithub to make the failing tests pass.

## WHERE
- Files: 
  - `src/mcp_coder/utils/github_operations/__init__.py` (modify existing)
  - `src/mcp_coder/utils/github_operations/pr_manager.py` (modify existing)

## WHAT
- Add PyGithub imports and GitHub client initialization in __init__
- Implement PullRequestManager methods with actual GitHub API calls
- Add repository URL parsing and validation
- Implement all methods: create, get, list, close, merge
- Implement properties: repository_name, default_branch

## HOW
### Implementation Structure
```python
# pr_manager.py
from typing import Optional, List, Dict, Any
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from mcp_coder.utils.log_utils import log_function_call
from mcp_coder.utils.user_config import get_config_value

class PullRequestManager:
    """Manages GitHub pull request operations for a specific repository."""
    
    def __init__(self, repo_url: str, token: Optional[str] = None):
        """Initialize the PullRequestManager."""
        self.repo_url = repo_url
        self._token = token or get_config_value("github.token")
        if not self._token:
            raise ValueError("GitHub token must be provided or configured")
            
        self._github = Github(self._token)
        self._repo = self._parse_and_get_repo(repo_url)
    
    def _parse_and_get_repo(self, repo_url: str) -> Repository:
        """Parse repository URL and get GitHub repository object."""
        # Implementation to handle different URL formats
    
    @log_function_call
    def create_pull_request(self, title: str, body: str, head: str, base: str = "main") -> Dict[str, Any]:
        """Create a pull request and return details."""
        pr = self._repo.create_pull(title=title, body=body, head=head, base=base)
        return {
            'number': pr.number,
            'url': pr.html_url,
            'title': pr.title
        }

    # ... other methods with actual implementations
```

## ALGORITHM
```
1. Add PyGithub imports to pr_manager.py
2. Enhance __init__ to:
   - Get token from config or parameter
   - Validate token exists
   - Initialize GitHub client
   - Parse repo_url and get repository object
3. Implement _parse_and_get_repo helper:
   - Handle https://github.com/owner/repo format
   - Handle git@github.com:owner/repo.git format
   - Handle owner/repo format
   - Return Repository object
4. For create_pull_request:
   - Use repo.create_pull() API
   - Extract number, url, title from result
   - Return structured dict
5. For get_pull_request:
   - Use repo.get_pull(number) API
   - Extract all relevant fields
   - Return structured dict
6. For list_pull_requests:
   - Use repo.get_pulls(state=state) API
   - Extract fields from each PR
   - Return list of dicts
7. For close_pull_request:
   - Get PR object and call edit(state="closed")
   - Return number and updated state
8. For merge_pull_request:
   - Get PR object and call merge()
   - Return merge result details
9. For properties:
   - repository_name: return self._repo.full_name
   - default_branch: return self._repo.default_branch
10. Handle errors gracefully with try/except
```

## DATA
- **create_pull_request returns**: `{'number': pr.number, 'url': pr.html_url, 'title': pr.title}`
- **get_pull_request returns**: `{'number': pr.number, 'title': pr.title, 'state': pr.state, 'url': pr.html_url, 'body': pr.body, 'head': pr.head.ref, 'base': pr.base.ref}`
- **list_pull_requests returns**: `[{'number': pr.number, 'title': pr.title, 'state': pr.state, 'url': pr.html_url, 'head': pr.head.ref, 'base': pr.base.ref}]`
- **close_pull_request returns**: `{'number': pr.number, 'state': pr.state}`
- **merge_pull_request returns**: `{'merged': result.merged, 'sha': result.sha, 'message': result.message}`
- **Error handling**: Return `{}` or `[]` on any exception, log errors

## LLM Prompt
```
You are implementing Step 4 of the GitHub Pull Request Operations feature using the updated PullRequestManager approach.

Replace the empty implementations in the PullRequestManager class with actual PyGithub functionality to make the failing tests pass.

Requirements:
- Add PyGithub imports (from github import Github, Repository, PullRequest)
- Enhance __init__ method to:
  - Validate GitHub token (raise ValueError if missing)
  - Initialize GitHub client with token
  - Parse repo_url and get Repository object
- Implement _parse_and_get_repo helper method to handle:
  - https://github.com/owner/repo URLs
  - git@github.com:owner/repo.git URLs  
  - owner/repo format
- Implement all five methods to return the exact dict/list structures expected by tests
- Implement both properties to return actual repository information
- Handle errors gracefully by returning empty dict {} or list [] and logging errors
- Keep implementation focused - just enough to pass the integration tests
- Follow the @log_function_call decorator pattern
- Use proper type hints and docstrings

The integration tests are currently failing because methods return empty dicts/lists. Your implementation should make them pass by returning the correct data structures with actual GitHub API data.

Focus on making the test_pr_manager_lifecycle test pass completely.
```

## Verification
- [ ] PyGithub imports added
- [ ] __init__ method enhanced with client initialization
- [ ] _parse_and_get_repo helper method implemented
- [ ] Token validation raises ValueError when missing
- [ ] create_pull_request creates actual PR and returns number/url/title
- [ ] get_pull_request retrieves PR data and returns structured dict
- [ ] list_pull_requests retrieves PR list and returns structured list
- [ ] close_pull_request closes PR and returns updated state
- [ ] merge_pull_request merges PR and returns result (bonus feature)
- [ ] repository_name property returns actual repo full name
- [ ] default_branch property returns actual default branch
- [ ] Error handling returns empty dict/list on failures
- [ ] Integration test now passes completely
- [ ] Configuration reading works correctly
