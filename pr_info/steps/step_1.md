# Step 1: Core Parsing Function `_parse_base_branch()`

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 1.

Implement the `_parse_base_branch()` function in issue_manager.py with TDD approach:
1. First write the unit tests
2. Then implement the function to pass those tests
3. Run tests to verify

Follow the specifications in this step file exactly.
```

---

## Overview

Add a private function to parse the `### Base Branch` section from GitHub issue body text.

---

## WHERE: File Paths

| File | Action |
|------|--------|
| `src/mcp_coder/utils/github_operations/issue_manager.py` | Add `_parse_base_branch()` function |
| `tests/utils/github_operations/test_issue_manager.py` | Add test class `TestParseBaseBranch` |

---

## WHAT: Function Signature

```python
def _parse_base_branch(body: str) -> Optional[str]:
    """Parse base branch from issue body.

    Args:
        body: GitHub issue body text

    Returns:
        Branch name if found and valid, None if not specified or empty

    Raises:
        ValueError: If base branch section contains multiple lines (malformed)
    """
```

---

## HOW: Integration Points

### Imports to Add (issue_manager.py)

```python
import re  # Already imported at top of file
```

### Function Location

Place `_parse_base_branch()` as a module-level private function, before the `IssueManager` class definition (around line 30, after the existing imports and before the class).

---

## ALGORITHM: Pseudocode

```python
def _parse_base_branch(body: str) -> Optional[str]:
    # 1. If body is empty/None, return None
    # 2. Use regex to find case-insensitive "#+\s*base\s*branch" header
    # 3. Capture content until next "#" header (or end of string)
    # 4. Strip whitespace from captured content
    # 5. If empty after strip, return None
    # 6. If content contains newlines (multi-line), raise ValueError
    # 7. Return the branch name
```

### Regex Pattern

```python
# Case-insensitive match for any heading level with "Base Branch"
# Captures content until next heading or end of string
pattern = r"(?i)^#{1,6}\s*base\s*branch\s*\n(.*?)(?=^#{1,6}\s|\Z)"
```

---

## DATA: Test Cases

### Test Class Structure

```python
class TestParseBaseBranch:
    """Tests for _parse_base_branch() function."""

    # Valid base branches
    def test_parse_base_branch_with_h3_header(self):
        body = "### Base Branch\n\nfeature/v2\n\n### Description\n\nContent"
        assert _parse_base_branch(body) == "feature/v2"

    def test_parse_base_branch_case_insensitive(self):
        body = "# base branch\n\nmain\n\n# Description"
        assert _parse_base_branch(body) == "main"

    def test_parse_base_branch_uppercase(self):
        body = "## BASE BRANCH\n\nrelease/2.0\n\n## Description"
        assert _parse_base_branch(body) == "release/2.0"

    def test_parse_base_branch_with_h1_header(self):
        body = "# Base Branch\n\nhotfix/urgent\n\n# Other"
        assert _parse_base_branch(body) == "hotfix/urgent"

    # No base branch (returns None)
    def test_parse_base_branch_no_section(self):
        body = "### Description\n\nNo base branch section here"
        assert _parse_base_branch(body) is None

    def test_parse_base_branch_empty_body(self):
        assert _parse_base_branch("") is None

    def test_parse_base_branch_none_body(self):
        assert _parse_base_branch(None) is None  # type: ignore

    def test_parse_base_branch_empty_content(self):
        body = "### Base Branch\n\n\n\n### Description"
        assert _parse_base_branch(body) is None

    def test_parse_base_branch_whitespace_only(self):
        body = "### Base Branch\n\n   \n\n### Description"
        assert _parse_base_branch(body) is None

    # Error cases (raises ValueError)
    def test_parse_base_branch_multiline_raises_error(self):
        body = "### Base Branch\n\nline1\nline2\n\n### Description"
        with pytest.raises(ValueError, match="multiple lines"):
            _parse_base_branch(body)

    def test_parse_base_branch_multiline_with_spaces_raises_error(self):
        body = "### Base Branch\n\nbranch1\n  branch2\n\n### Description"
        with pytest.raises(ValueError, match="multiple lines"):
            _parse_base_branch(body)
```

---

## Implementation Details

### Full Function Implementation

```python
def _parse_base_branch(body: str) -> Optional[str]:
    """Parse base branch from issue body.

    Looks for a markdown heading (any level) containing "Base Branch" (case-insensitive)
    and extracts the content until the next heading.

    Args:
        body: GitHub issue body text

    Returns:
        Branch name if found and valid, None if not specified or empty

    Raises:
        ValueError: If base branch section contains multiple lines (malformed input)

    Example:
        >>> _parse_base_branch("### Base Branch\\n\\nfeature/v2\\n\\n### Description")
        'feature/v2'
        >>> _parse_base_branch("### Description\\n\\nNo base branch")
        None
    """
    if not body:
        return None

    # Case-insensitive match for any heading level (# to ######) with "Base Branch"
    # MULTILINE flag for ^ to match line starts, DOTALL for . to match newlines
    pattern = r"(?im)^#{1,6}\s*base\s*branch\s*\n(.*?)(?=^#{1,6}\s|\Z)"
    match = re.search(pattern, body, re.MULTILINE | re.DOTALL)

    if not match:
        return None

    content = match.group(1).strip()

    if not content:
        return None

    # Check for multi-line content (malformed input)
    if "\n" in content:
        raise ValueError(
            f"Base branch section contains multiple lines (malformed): {content!r}"
        )

    return content
```

---

## Verification

After implementation, run:

```bash
pytest tests/utils/github_operations/test_issue_manager.py::TestParseBaseBranch -v
```

Expected: All tests pass.
