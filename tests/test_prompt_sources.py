import os
import tempfile
from pathlib import Path

import pytest

from mcp_coder.prompt_manager import (
    get_prompt,
    validate_prompt_directory,
    validate_prompt_markdown,
)


class TestGetPromptFromFile:
    """Test prompt retrieval from file path."""

    def test_get_prompt_from_file(self) -> None:
        """Test prompt retrieval from file path."""
        content = """
# File Header
```python
file_code = "from_file"
```
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            temp_name = f.name

        try:
            result = get_prompt(temp_name, "File Header")
            assert 'file_code = "from_file"' in result
        finally:
            os.unlink(temp_name)

    def test_get_prompt_file_not_found(self) -> None:
        """Test error handling when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_prompt("nonexistent_file.md", "Any Header")


class TestGetPromptWildcard:
    """Test wildcard and directory handling."""

    def test_get_prompt_from_directory(self) -> None:
        """Test prompt retrieval from directory (auto-expands to *.md)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first file
            file1_content = """
# Header1
```python
code1 = "test1"
```
"""
            file1_path = os.path.join(temp_dir, "file1.md")
            with open(file1_path, "w", encoding="utf-8") as f:
                f.write(file1_content)

            # Create second file
            file2_content = """
# Header2
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, "w", encoding="utf-8") as f:
                f.write(file2_content)

            # Test finding prompt from first file
            result = get_prompt(temp_dir, "Header1")
            assert 'code1 = "test1"' in result

            # Test finding prompt from second file
            result = get_prompt(temp_dir, "Header2")
            assert 'code2 = "test2"' in result

    def test_get_prompt_from_wildcard(self) -> None:
        """Test prompt retrieval using wildcard patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create markdown file
            md_content = """
# MD Header
```python
md_code = "markdown"
```
"""
            md_path = os.path.join(temp_dir, "test.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            # Create text file (should be ignored)
            txt_path = os.path.join(temp_dir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("# TXT Header\n```\ntxt_code\n```")

            # Test wildcard *.md
            wildcard_pattern = os.path.join(temp_dir, "*.md")
            result = get_prompt(wildcard_pattern, "MD Header")
            assert 'md_code = "markdown"' in result

    def test_get_prompt_cross_file_duplicate_detection(self) -> None:
        """Test that duplicates across files are detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first file with header
            file1_content = """
# Duplicate Header
```python
code1 = "test1"
```
"""
            file1_path = os.path.join(temp_dir, "file1.md")
            with open(file1_path, "w", encoding="utf-8") as f:
                f.write(file1_content)

            # Create second file with same header
            file2_content = """
# Duplicate Header
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, "w", encoding="utf-8") as f:
                f.write(file2_content)

            # Should raise ValueError due to duplicate headers
            with pytest.raises(ValueError, match="Duplicate header"):
                get_prompt(temp_dir, "Duplicate Header")


class TestInputAutoDetection:
    """Test auto-detection of file path vs string content."""

    def test_string_content_detection(self) -> None:
        """Test that content with newlines is detected as string content."""
        content = """
# Test Header
```python
test_code = "string_content"
```
"""
        result = get_prompt(content, "Test Header")
        assert 'test_code = "string_content"' in result

    def test_string_content_starting_with_hash(self) -> None:
        """Test that content starting with # is detected as string content."""
        content = "# Simple Header\n```\ncode\n```"
        result = get_prompt(content, "Simple Header")
        assert "code" in result

    def test_file_path_detection(self) -> None:
        """Test that simple paths without newlines are detected as file paths."""
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
            # Should be detected as file path, not content
            result = get_prompt(temp_name, "File Header")
            assert 'file_code = "test"' in result
        finally:
            os.unlink(temp_name)


class TestPackageIntegration:
    """Test package integration with real prompt files."""

    def test_package_imports(self) -> None:
        """Test that all functions can be imported from the package."""
        # This test is implicitly run by importing at the top of this file
        # If import failed, this test file wouldn't run
        assert get_prompt is not None
        assert validate_prompt_markdown is not None
        assert validate_prompt_directory is not None

    def test_real_prompt_file_access(self) -> None:
        """Test accessing prompts from the real test data file."""
        # Get the path to the test data file
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_file = package_dir / "prompts" / "prompts_testdata.md"

        # Test that the file exists
        assert prompts_file.exists(), f"Test data file not found at {prompts_file}"

        # Test reading a prompt from the test data file
        result = get_prompt(str(prompts_file), "Test Prompt AAA")
        assert result is not None
        assert "This is test prompt AAA" in result
        assert "Keep responses under 50 characters" in result

    def test_real_prompt_file_directory_access(self) -> None:
        """Test accessing prompts via directory path."""
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_dir = package_dir / "prompts"

        # Test that directory access works
        result = get_prompt(str(prompts_dir), "Test Prompt BBB")
        assert result is not None
        assert "This is test prompt BBB" in result

    def test_real_prompt_file_wildcard_access(self) -> None:
        """Test accessing prompts via wildcard pattern."""
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_pattern = str(package_dir / "prompts" / "*.md")

        # Test that wildcard access works
        result = get_prompt(prompts_pattern, "Test Prompt CCC")
        assert result is not None
        assert "This is test prompt CCC" in result

    def test_real_prompt_file_validation(self) -> None:
        """Test validation functions with real test data file."""
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_file = package_dir / "prompts" / "prompts_testdata.md"

        # Test markdown validation - this will show validation errors for doc headers
        # but should still extract headers correctly
        result = validate_prompt_markdown(str(prompts_file))
        # The file has documentation headers without code blocks, which is expected
        # So validation will fail, but headers should be extracted
        assert len(result["headers"]) > 0

        # Verify specific headers are found
        header_names = [h["name"] for h in result["headers"]]
        expected_headers = ["Test Prompt AAA", "Test Prompt BBB", "Test Prompt CCC"]
        for expected in expected_headers:
            assert (
                expected in header_names
            ), f"Expected header '{expected}' not found in {header_names}"

    def test_real_prompt_directory_validation(self) -> None:
        """Test directory validation with real prompts directory (will include both files)."""
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_dir = package_dir / "prompts"

        # Test directory validation - will have errors due to doc headers without code blocks
        result = validate_prompt_directory(str(prompts_dir))
        # Directory validation will show errors for documentation headers, which is expected
        assert (
            result["files_checked"] >= 2
        )  # Should find at least prompts.md and prompts_testdata.md

    def test_commit_prompt_exists(self) -> None:
        """Test that commit message generation prompt exists and is loadable."""
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_file = package_dir / "prompts" / "prompts.md"

        # Test that the commit prompt can be loaded
        result = get_prompt(str(prompts_file), "Git Commit Message Generation")
        assert result is not None
        assert len(result.strip()) > 0

    def test_commit_prompt_format(self) -> None:
        """Test that commit prompt follows expected format."""
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_file = package_dir / "prompts" / "prompts.md"

        # Test that the commit prompt contains key sections
        result = get_prompt(str(prompts_file), "Git Commit Message Generation")
        assert "RULES:" in result
        assert "OUTPUT:" in result
        assert "EXAMPLES:" in result

    def test_commit_prompt_content(self) -> None:
        """Test that commit prompt contains key instructions."""
        import mcp_coder

        package_dir = Path(mcp_coder.__file__).parent
        prompts_file = package_dir / "prompts" / "prompts.md"

        # Test that the commit prompt contains essential content
        result = get_prompt(str(prompts_file), "Git Commit Message Generation")

        # Check for conventional commit format guidance
        assert "conventional commit format" in result
        assert "type(scope): description" in result

        # Check for commit types
        assert "feat, fix, docs, style, refactor, test, chore" in result

        # Check for analysis guidance
        assert "git diff" in result

        # Check for length guidance
        assert "50 characters" in result

        # Check for examples
        assert "feat(" in result
        assert "fix(" in result
