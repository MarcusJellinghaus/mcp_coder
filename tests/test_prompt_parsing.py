"""Test suite for markdown parsing behavior of the prompt manager.

Tests cover:
- Error handling for missing headers
- Duplicate header detection
- Header level matching (any level: #, ##, ###, ####)
"""

import pytest

from mcp_coder.prompt_manager import get_prompt


class TestGetPromptMissingHeader:
    """Test error handling for missing headers."""

    def test_get_prompt_missing_header(self) -> None:
        """Test error handling for missing headers."""
        content = """
# Existing Header
```python
existing_code = "test"
```
"""
        with pytest.raises(ValueError, match="Header 'Missing Header' not found"):
            get_prompt(content, "Missing Header")

    def test_get_prompt_header_without_code_block(self) -> None:
        """Test error handling when header exists but no code block follows."""
        content = """
# Header Without Code
This is just text, no code block.

# Another Header
More text.
"""
        with pytest.raises(ValueError, match="No code block found after header"):
            get_prompt(content, "Header Without Code")


class TestGetPromptDuplicateHeaders:
    """Test error handling for duplicate headers."""

    def test_get_prompt_duplicate_headers_same_file(self) -> None:
        """Test error handling for duplicate headers in same content."""
        content = """
# Duplicate Header
```python
first_code = "test1"
```

# Duplicate Header
```python
second_code = "test2"
```
"""
        with pytest.raises(ValueError, match="Duplicate header"):
            get_prompt(content, "Duplicate Header")

    def test_get_prompt_duplicate_headers_different_levels(self) -> None:
        """Test that different header levels with same text are considered duplicates."""
        content = """
# Same Name
```python
level1_code = "test1"
```

## Same Name
```python
level2_code = "test2"
```
"""
        with pytest.raises(ValueError, match="Duplicate header"):
            get_prompt(content, "Same Name")


class TestHeaderLevelMatching:
    """Test that any header level matches for the same prompt name."""

    def test_header_level_matching_all_levels(self) -> None:
        """Test that any header level matches (#, ##, ###, ####)."""
        content = """
# Level1 Header
```python
level1 = "test"
```

## Level2 Header
```python
level2 = "test"
```

### Level3 Header
```python
level3 = "test"
```

#### Level4 Header
```python
level4 = "test"
```

##### Level5 Header
```python
level5 = "test"
```
"""
        # All levels should be findable
        assert 'level1 = "test"' in get_prompt(content, "Level1 Header")
        assert 'level2 = "test"' in get_prompt(content, "Level2 Header")
        assert 'level3 = "test"' in get_prompt(content, "Level3 Header")
        assert 'level4 = "test"' in get_prompt(content, "Level4 Header")
        assert 'level5 = "test"' in get_prompt(content, "Level5 Header")

    def test_header_level_independence(self) -> None:
        """Test that header level doesn't affect matching - only the text matters."""
        content1 = """
# Same Name
```python
code_level1 = "test"
```
"""
        content2 = """
#### Same Name
```python
code_level4 = "test"
```
"""
        # Both should be found regardless of level
        result1 = get_prompt(content1, "Same Name")
        result2 = get_prompt(content2, "Same Name")

        assert 'code_level1 = "test"' in result1
        assert 'code_level4 = "test"' in result2
