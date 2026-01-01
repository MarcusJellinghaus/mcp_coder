# Step 2: Implement `RepoIdentifier` Class

## Overview
Implement the `RepoIdentifier` dataclass with factory methods for parsing repository identifiers from different formats.

## LLM Prompt
```
Implement the RepoIdentifier class as specified in pr_info/steps/summary.md.

Requirements:
1. Add RepoIdentifier dataclass to src/mcp_coder/utils/github_operations/github_utils.py
2. Implement from_full_name() factory method with validation
3. Implement from_repo_url() factory method that parses HTTPS and SSH GitHub URLs
4. Implement full_name and cache_safe_name properties
5. Raise ValueError for invalid input (no slash, multiple slashes, empty parts, invalid URLs)
6. Run tests from Step 1 to verify behavior

The goal is to create a single source of truth for repository identifier parsing.
```

## WHERE: File Paths
- **Primary**: `src/mcp_coder/utils/github_operations/github_utils.py`

## WHAT: New Class

### RepoIdentifier Dataclass
```python
from dataclasses import dataclass
import re

@dataclass
class RepoIdentifier:
    """Repository identifier with owner and repo name.
    
    Provides a single source of truth for repository identifier parsing.
    Use factory methods to create instances from different input formats.
    
    Attributes:
        owner: Repository owner (e.g., "MarcusJellinghaus")
        repo_name: Repository name (e.g., "mcp_coder")
    
    Properties:
        full_name: Returns "owner/repo" format
        cache_safe_name: Returns "owner_repo" format for filenames
    """
    owner: str
    repo_name: str
    
    @property
    def full_name(self) -> str:
        """Return repository in 'owner/repo' format."""
        return f"{self.owner}/{self.repo_name}"
    
    @property
    def cache_safe_name(self) -> str:
        """Return repository in 'owner_repo' format (safe for filenames)."""
        return f"{self.owner}_{self.repo_name}"
    
    def __str__(self) -> str:
        """Return string representation (full_name format)."""
        return self.full_name
    
    @classmethod
    def from_full_name(cls, full_name: str) -> "RepoIdentifier":
        """Parse 'owner/repo' format into RepoIdentifier.
        
        Args:
            full_name: Repository in "owner/repo" format
            
        Returns:
            RepoIdentifier instance
            
        Raises:
            ValueError: If input doesn't contain exactly one slash,
                       or if owner or repo_name is empty
        """
        slash_count = full_name.count("/")
        if slash_count != 1:
            raise ValueError(
                f"Invalid repo identifier '{full_name}': expected 'owner/repo' format "
                f"(exactly one slash), got {slash_count} slashes"
            )
        
        owner, repo_name = full_name.split("/")
        
        if not owner:
            raise ValueError(
                f"Invalid repo identifier '{full_name}': owner cannot be empty"
            )
        if not repo_name:
            raise ValueError(
                f"Invalid repo identifier '{full_name}': repo_name cannot be empty"
            )
        
        return cls(owner=owner, repo_name=repo_name)
    
    @classmethod
    def from_repo_url(cls, url: str) -> "RepoIdentifier":
        """Parse GitHub URL into RepoIdentifier.
        
        Supports both HTTPS and SSH URL formats:
        - https://github.com/owner/repo(.git)?
        - git@github.com:owner/repo(.git)?
        
        Args:
            url: GitHub repository URL
            
        Returns:
            RepoIdentifier instance
            
        Raises:
            ValueError: If URL is not a valid GitHub URL
        """
        if not isinstance(url, str):
            raise ValueError(
                f"Invalid repo URL: expected string, got {type(url).__name__}"
            )
        
        # Pattern for HTTPS URLs: https://github.com/owner/repo(.git)?
        https_pattern = r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
        https_match = re.match(https_pattern, url)
        if https_match:
            owner, repo_name = https_match.groups()
            return cls.from_full_name(f"{owner}/{repo_name}")
        
        # Pattern for SSH URLs: git@github.com:owner/repo(.git)?
        ssh_pattern = r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$"
        ssh_match = re.match(ssh_pattern, url)
        if ssh_match:
            owner, repo_name = ssh_match.groups()
            return cls.from_full_name(f"{owner}/{repo_name}")
        
        raise ValueError(
            f"Invalid GitHub URL '{url}': expected 'https://github.com/owner/repo' "
            f"or 'git@github.com:owner/repo' format"
        )
```

## HOW: Integration Points
- **Imports**: Add `from dataclasses import dataclass` and `import re` if not present
- **Location**: Add class near top of file after imports
- **Export**: Add `RepoIdentifier` to `src/mcp_coder/utils/github_operations/__init__.py`

## ALGORITHM: Parsing Logic

### from_full_name()
```
1. Count slashes in input
2. If slash_count != 1: raise ValueError
3. Split on "/" to get owner and repo_name
4. If owner is empty: raise ValueError
5. If repo_name is empty: raise ValueError
6. Return RepoIdentifier(owner, repo_name)
```

### from_repo_url()
```
1. Check input is string, else raise ValueError
2. Try HTTPS pattern match
3. If match: extract owner/repo, call from_full_name()
4. Try SSH pattern match
5. If match: extract owner/repo, call from_full_name()
6. No match: raise ValueError with helpful message
```

## DATA: Expected Behavior

### Valid Inputs
| Input | Method | Result |
|-------|--------|--------|
| `"owner/repo"` | `from_full_name` | `RepoIdentifier("owner", "repo")` |
| `"https://github.com/owner/repo"` | `from_repo_url` | `RepoIdentifier("owner", "repo")` |
| `"https://github.com/owner/repo.git"` | `from_repo_url` | `RepoIdentifier("owner", "repo")` |
| `"git@github.com:owner/repo"` | `from_repo_url` | `RepoIdentifier("owner", "repo")` |
| `"git@github.com:owner/repo.git"` | `from_repo_url` | `RepoIdentifier("owner", "repo")` |

### Invalid Inputs (all raise ValueError)
| Input | Method | Error Reason |
|-------|--------|--------------|
| `"just-repo"` | `from_full_name` | No slash |
| `"a/b/c"` | `from_full_name` | Multiple slashes |
| `"/repo"` | `from_full_name` | Empty owner |
| `"owner/"` | `from_full_name` | Empty repo_name |
| `"https://gitlab.com/owner/repo"` | `from_repo_url` | Not GitHub URL |
| `"invalid"` | `from_repo_url` | Not a URL |

## Implementation Notes
- **Reuse**: `from_repo_url()` calls `from_full_name()` to avoid duplicating validation
- **Error Messages**: Include the invalid input in error messages for debugging
- **Type Safety**: Check for string type in `from_repo_url()` to handle Mock objects gracefully
