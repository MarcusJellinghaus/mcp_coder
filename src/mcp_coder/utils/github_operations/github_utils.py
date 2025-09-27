"""GitHub utility functions for URL parsing and validation.

This module provides utility functions for working with GitHub URLs and repositories.
"""

import re
from typing import Optional, Tuple


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """Parse GitHub URL and extract owner/repository name.
    
    Supports multiple GitHub URL formats:
    - HTTPS: https://github.com/owner/repo
    - HTTPS with .git: https://github.com/owner/repo.git
    - SSH: git@github.com:owner/repo.git
    - Short format: owner/repo
    
    Args:
        url: GitHub repository URL in various formats
        
    Returns:
        Tuple of (owner, repo_name) if valid GitHub URL, None otherwise
        
    Examples:
        >>> parse_github_url("https://github.com/user/repo")
        ('user', 'repo')
        >>> parse_github_url("git@github.com:user/repo.git")
        ('user', 'repo')
        >>> parse_github_url("user/repo")
        ('user', 'repo')
        >>> parse_github_url("invalid-url")
        None
    """
    if not isinstance(url, str) or not url.strip():
        return None
    
    # Pattern to match GitHub URLs in various formats
    # HTTPS: https://github.com/owner/repo(.git)?
    # SSH: git@github.com:owner/repo(.git)?  
    # Short: owner/repo
    github_pattern = r"(?:https://github\.com/|git@github\.com:|^)([^/]+)/([^/\.]+)(?:\.git)?/?$"
    match = re.match(github_pattern, url.strip())
    
    if not match:
        return None
        
    owner, repo_name = match.groups()
    return owner, repo_name


def format_github_https_url(owner: str, repo_name: str) -> str:
    """Format owner/repo into standard GitHub HTTPS URL.
    
    Args:
        owner: Repository owner/organization name
        repo_name: Repository name
        
    Returns:
        Standard GitHub HTTPS URL
        
    Examples:
        >>> format_github_https_url("user", "repo")
        'https://github.com/user/repo'
    """
    return f"https://github.com/{owner}/{repo_name}"


def get_repo_full_name(url: str) -> Optional[str]:
    """Get repository full name (owner/repo) from GitHub URL.
    
    Args:
        url: GitHub repository URL in various formats
        
    Returns:
        Repository full name as "owner/repo" or None if invalid
        
    Examples:
        >>> get_repo_full_name("https://github.com/user/repo")
        'user/repo'
        >>> get_repo_full_name("git@github.com:user/repo.git")
        'user/repo'
        >>> get_repo_full_name("invalid-url")
        None
    """
    parsed = parse_github_url(url)
    if parsed is None:
        return None
        
    owner, repo_name = parsed
    return f"{owner}/{repo_name}"