"""Comprehensive test suite for prompt_manager module.

Tests cover:
- Basic prompt retrieval from string content and file paths
- Wildcard and directory handling
- Error handling for missing headers and duplicates
- Validation functions for markdown structure
- Header level matching (any level: #, ##, ###, ####)
"""

import os
import tempfile

from mcp_coder.prompt_manager import (
    get_prompt,
    get_prompt_with_substitutions,
    validate_prompt_directory,
    validate_prompt_markdown,
)


class TestGetPromptFromString:
    """Test basic prompt retrieval from string content."""

    def test_get_prompt_from_string_basic(self) -> None:
        """Test basic prompt retrieval from string content."""
        content = """
# Test Header
This is some text before the code block.

```python
def test_function():
    return "test"
```

# Another Header
More content here.

```bash
echo "hello"
```
"""
        result = get_prompt(content, "Test Header")
        assert result.strip() == 'def test_function():\n    return "test"'

    def test_get_prompt_from_string_different_header_levels(self) -> None:
        """Test that any header level matches (#, ##, ###, ####)."""
        content = """
# Level 1 Header
```python
level1_code = "test1"
```

## Level 2 Header  
```python
level2_code = "test2"
```

### Level 3 Header
```python
level3_code = "test3"
```

#### Level 4 Header
```python
level4_code = "test4"
```
"""
        # Test each level can be found
        assert 'level1_code = "test1"' in get_prompt(content, "Level 1 Header")
        assert 'level2_code = "test2"' in get_prompt(content, "Level 2 Header")
        assert 'level3_code = "test3"' in get_prompt(content, "Level 3 Header")
        assert 'level4_code = "test4"' in get_prompt(content, "Level 4 Header")

    def test_get_prompt_case_sensitive(self) -> None:
        """Test that header matching is case sensitive."""
        content = """
# Test Header
```python
correct_code = "test"
```

# test header
```python
wrong_code = "wrong"
```
"""
        result = get_prompt(content, "Test Header")
        assert 'correct_code = "test"' in result

    def test_get_prompt_with_spaces_in_header(self) -> None:
        """Test headers with spaces and special characters."""
        content = """
# My Complex Header Name
```python
complex_code = "test"
```

# Another-Header_With.Special@Chars
```python
special_code = "special"
```
"""
        result = get_prompt(content, "My Complex Header Name")
        assert 'complex_code = "test"' in result

        result = get_prompt(content, "Another-Header_With.Special@Chars")
        assert 'special_code = "special"' in result


class TestValidatePromptMarkdown:
    """Test validation of markdown structure."""

    def test_validate_prompt_markdown_valid(self) -> None:
        """Test validation of properly formatted markdown."""
        content = """
# Valid Header 1
```python
code1 = "test1"
```

# Valid Header 2
```bash
echo "test2"
```
"""
        result = validate_prompt_markdown(content)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert "headers" in result
        assert len(result["headers"]) == 2

    def test_validate_prompt_markdown_invalid_duplicates(self) -> None:
        """Test validation of markdown with duplicate headers."""
        content = """
# Duplicate Header
```python
code1 = "test1"
```

# Duplicate Header
```python
code2 = "test2"
```
"""
        result = validate_prompt_markdown(content)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("duplicate" in error.lower() for error in result["errors"])

    def test_validate_prompt_markdown_missing_code_blocks(self) -> None:
        """Test validation when headers don't have code blocks."""
        content = """
# Header Without Code
Just some text here.

# Another Header
```python
valid_code = "test"
```
"""
        result = validate_prompt_markdown(content)
        assert result["valid"] is False
        assert any("no code block" in error.lower() for error in result["errors"])

    def test_validate_prompt_markdown_from_file(self) -> None:
        """Test validation from file path."""
        content = """
# File Header
```python
file_code = "test"
```
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            temp_name = f.name

        try:
            result = validate_prompt_markdown(temp_name)
            assert result["valid"] is True
            assert len(result["errors"]) == 0
        finally:
            os.unlink(temp_name)


class TestValidatePromptDirectory:
    """Test validation of all markdown files in directory."""

    def test_validate_prompt_directory_valid(self) -> None:
        """Test validation of directory with valid markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first valid file
            file1_content = """
# Header1
```python
code1 = "test1"
```
"""
            file1_path = os.path.join(temp_dir, "file1.md")
            with open(file1_path, "w", encoding="utf-8") as f:
                f.write(file1_content)

            # Create second valid file
            file2_content = """
# Header2
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, "w", encoding="utf-8") as f:
                f.write(file2_content)

            result = validate_prompt_directory(temp_dir)
            assert result["valid"] is True
            assert len(result["errors"]) == 0
            assert "files_checked" in result
            assert result["files_checked"] == 2

    def test_validate_prompt_directory_cross_file_duplicates(self) -> None:
        """Test validation detects cross-file duplicate headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first file
            file1_content = """
# Shared Header
```python
code1 = "test1"
```
"""
            file1_path = os.path.join(temp_dir, "file1.md")
            with open(file1_path, "w", encoding="utf-8") as f:
                f.write(file1_content)

            # Create second file with duplicate header
            file2_content = """
# Shared Header
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, "w", encoding="utf-8") as f:
                f.write(file2_content)

            result = validate_prompt_directory(temp_dir)
            # Debug the result
            assert (
                result["valid"] is False
            ), f"Expected False but got {result['valid']}. Errors: {result['errors']}"
            assert (
                len(result["errors"]) > 0
            ), f"Expected errors but got none. Result: {result}"
            assert any(
                "appears in multiple files" in error.lower()
                for error in result["errors"]
            ), f"No duplicate error found. Errors: {result['errors']}"

    def test_validate_prompt_directory_no_markdown_files(self) -> None:
        """Test validation of directory with no markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-markdown file
            txt_path = os.path.join(temp_dir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("Not markdown")

            result = validate_prompt_directory(temp_dir)
            assert result["valid"] is True  # No markdown files is valid
            assert result["files_checked"] == 0


class TestGetPromptWithSubstitutions:
    """Tests for get_prompt_with_substitutions function."""

    def test_substitutes_single_placeholder(self) -> None:
        """Should replace a single [placeholder] with value."""
        content = """# Test Prompt
```
Hello [name], welcome!
```"""
        result = get_prompt_with_substitutions(
            content, "Test Prompt", {"name": "World"}
        )
        assert result == "Hello World, welcome!"

    def test_substitutes_multiple_placeholders(self) -> None:
        """Should replace multiple [placeholder] values."""
        content = """# Test Prompt
```
Job: [job_name], Step: [step_name]
```"""
        result = get_prompt_with_substitutions(
            content, "Test Prompt", {"job_name": "test", "step_name": "Run tests"}
        )
        assert result == "Job: test, Step: Run tests"

    def test_empty_substitutions_returns_unchanged(self) -> None:
        """Empty substitutions dict should return prompt unchanged."""
        content = """# Test Prompt
```
Hello [name]!
```"""
        result = get_prompt_with_substitutions(content, "Test Prompt", {})
        assert result == "Hello [name]!"

    def test_missing_placeholder_unchanged(self) -> None:
        """Placeholders not in dict should remain unchanged."""
        content = """# Test Prompt
```
Hello [name] and [other]!
```"""
        result = get_prompt_with_substitutions(
            content, "Test Prompt", {"name": "World"}
        )
        assert result == "Hello World and [other]!"
