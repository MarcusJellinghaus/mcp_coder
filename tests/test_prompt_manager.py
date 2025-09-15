"""
Comprehensive test suite for prompt_manager module.

Tests cover:
- Basic prompt retrieval from string content and file paths
- Wildcard and directory handling
- Error handling for missing headers and duplicates
- Validation functions for markdown structure
- Header level matching (any level: #, ##, ###, ####)
"""

import os
import tempfile
import pytest
from unittest.mock import patch
from pathlib import Path

from mcp_coder.prompt_manager import (
    get_prompt,
    validate_prompt_markdown,
    validate_prompt_directory,
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
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
            with open(file1_path, 'w') as f:
                f.write(file1_content)
                
            # Create second file
            file2_content = """
# Header2
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, 'w') as f:
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
            with open(md_path, 'w') as f:
                f.write(md_content)
                
            # Create text file (should be ignored)
            txt_path = os.path.join(temp_dir, "test.txt")
            with open(txt_path, 'w') as f:
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
            with open(file1_path, 'w') as f:
                f.write(file1_content)
                
            # Create second file with same header
            file2_content = """
# Duplicate Header
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, 'w') as f:
                f.write(file2_content)
                
            # Should raise ValueError due to duplicate headers
            with pytest.raises(ValueError, match="Duplicate header"):
                get_prompt(temp_dir, "Duplicate Header")


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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
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
            with open(file1_path, 'w') as f:
                f.write(file1_content)
                
            # Create second valid file
            file2_content = """
# Header2
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, 'w') as f:
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
            with open(file1_path, 'w') as f:
                f.write(file1_content)
                
            # Create second file with duplicate header
            file2_content = """
# Shared Header
```python
code2 = "test2"
```
"""
            file2_path = os.path.join(temp_dir, "file2.md")
            with open(file2_path, 'w') as f:
                f.write(file2_content)
                
            result = validate_prompt_directory(temp_dir)
            # Debug the result
            assert result["valid"] is False, f"Expected False but got {result['valid']}. Errors: {result['errors']}"
            assert len(result["errors"]) > 0, f"Expected errors but got none. Result: {result}"
            assert any("appears in multiple files" in error.lower() for error in result["errors"]), f"No duplicate error found. Errors: {result['errors']}"
            
    def test_validate_prompt_directory_no_markdown_files(self) -> None:
        """Test validation of directory with no markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-markdown file
            txt_path = os.path.join(temp_dir, "test.txt")
            with open(txt_path, 'w') as f:
                f.write("Not markdown")
                
            result = validate_prompt_directory(temp_dir)
            assert result["valid"] is True  # No markdown files is valid
            assert result["files_checked"] == 0


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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
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
            assert expected in header_names, f"Expected header '{expected}' not found in {header_names}"
            
    def test_real_prompt_directory_validation(self) -> None:
        """Test directory validation with real prompts directory (will include both files)."""
        import mcp_coder
        package_dir = Path(mcp_coder.__file__).parent
        prompts_dir = package_dir / "prompts"
        
        # Test directory validation - will have errors due to doc headers without code blocks
        result = validate_prompt_directory(str(prompts_dir))
        # Directory validation will show errors for documentation headers, which is expected
        assert result["files_checked"] >= 2  # Should find at least prompts.md and prompts_testdata.md
