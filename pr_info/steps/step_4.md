# Step 4: Update Documentation and Docstrings

## Overview
Update module and function docstrings to clarify the expected repository identifier formats and document the simplified approach.

## LLM Prompt
```
Update documentation in coordinator.py as specified in pr_info/steps/summary.md.

Requirements:
1. Add terminology definitions to module docstring
2. Add terminology table as comment near _split_repo_identifier() function (already done in Step 2)
3. Update get_cached_eligible_issues() docstring to clarify repo_full_name format
4. Ensure documentation reflects the simplified approach
5. Maintain consistency with existing documentation style

Focus on clarity and helping future developers understand the expected data formats.
```

## WHERE: File Paths
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Sections**: Module docstring (at top of file), `_split_repo_identifier()` function docstring (already added in Step 2), `get_cached_eligible_issues()` function docstring

## WHAT: Main Documentation Updates

### Module Docstring Addition
Add terminology section to existing module docstring:
```python
"""Coordinator CLI commands for automated workflow orchestration.

[Existing content...]

Repository Identifier Terminology:
| Term | Format | Example |
|------|--------|---------|
| `repo_url` | Full GitHub URL | `https://github.com/owner/repo.git` |
| `repo_full_name` | owner/repo | `MarcusJellinghaus/mcp_coder` |
| `repo_name` | Just the repo | `mcp_coder` |
| `owner` | Just the owner | `MarcusJellinghaus` |

GitHub API Caching:
[Existing caching documentation...]
"""
```

### Function Docstring Updates
```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Get eligible issues using cache for performance and duplicate protection.

    Args:
        repo_full_name: Repository in "owner/repo" format (e.g., "MarcusJellinghaus/mcp_coder")
        issue_manager: IssueManager for GitHub API calls
        force_refresh: Bypass cache entirely
        cache_refresh_minutes: Full refresh threshold (default: 1440 = 24 hours)

    Returns:
        List of eligible issues (open state, meeting bot pickup criteria)
    """
```

## HOW: Integration Points
- **Style Consistency**: Match existing docstring format and tone
- **Links**: Maintain references to existing GitHub API caching documentation
- **Examples**: Use real repository names from the codebase

## ALGORITHM: Documentation Process
```python
# Documentation updates:
1. Locate module docstring at top of coordinator.py
2. Insert terminology table after existing intro
3. Find get_cached_eligible_issues() function docstring
4. Update Args section to clarify repo_full_name format
5. Verify formatting consistency with project standards
```

## DATA: Documentation Content

### Terminology Table
| Field | Description | Purpose |
|-------|-------------|---------|
| `repo_url` | Full GitHub URLs with protocol | Used at entry points for parsing |
| `repo_full_name` | Standardized "owner/repo" format | Used internally for cache and API calls |
| `repo_name` | Repository name only | Used for cache file naming |
| `owner` | Repository owner/organization | Used for cache file naming |

### Updated Parameter Documentation
```python
Args:
    repo_full_name: Repository in "owner/repo" format (e.g., "MarcusJellinghaus/mcp_coder")
        This parameter expects the standardized internal format, not a full URL.
        The format is validated and parsed using simple string operations.
```

## Implementation Notes

### Style Guidelines
- **Format**: Use existing table markdown style for terminology
- **Examples**: Reference actual repositories from the codebase
- **Tone**: Maintain technical but accessible language

### Validation
- **Consistency**: Check docstring format matches other functions
- **Accuracy**: Ensure examples match actual usage patterns
- **Completeness**: Cover all important parameter constraints

### Cross-References
- **Related Functions**: Reference `_get_cache_file_path()` behavior
- **Caching Logic**: Link to existing caching documentation
- **Error Handling**: Document fallback behavior