"""
Prompt manager for mcp-coder project.

This module provides functionality to retrieve and validate prompts from markdown files.
Supports file paths, directories/wildcards, and string content with auto-detection.

Main functions:
- get_prompt(source, header): Get prompt from markdown source
- validate_prompt_markdown(source): Validate markdown structure
- validate_prompt_directory(directory): Validate all markdown files in directory

Key Features:
- Supports multiple input types: string content, file paths, directories, wildcards, package-relative paths
- Auto-detection of input type (file path vs string content)
- Package-relative path resolution for both development and installed environments
- Cross-file duplicate header detection when using directories/wildcards
- Clear error messages with file locations and line numbers
- Comprehensive validation with detailed results

Markdown Format Requirements:
- Headers: Use # ## ### #### ##### (1-5 levels)
- Code blocks: Use ``` fenced code blocks immediately after headers
- Headers must be unique within and across files
- Each header should be followed by exactly one code block

Usage Examples:
    # From string content
    prompt = get_prompt('# Test\\n```\\nHello World\\n```', 'Test')

    # From file
    prompt = get_prompt('prompts/prompts.md', 'Short Commit')
    
    # From package-relative path (auto-resolves in dev/installed environments)
    prompt = get_prompt('mcp_coder/prompts/prompts.md', 'Git Commit Message Generation')

    # From directory (all .md files)
    prompt = get_prompt('prompts/', 'Short Commit')

    # From wildcard pattern
    prompt = get_prompt('prompts/*.md', 'Short Commit')

    # Validation examples
    result = validate_prompt_markdown('prompts/prompts.md')
    if not result['valid']:
        print(f"Errors: {result['errors']}")

    # Directory validation with cross-file checking
    result = validate_prompt_directory('prompts/')
    if not result['valid']:
        for error in result['errors']:
            print(f"Error: {error}")

Error Handling Examples:
    # Handle missing headers
    try:
        prompt = get_prompt('prompts/prompts.md', 'NonExistent')
    except ValueError as e:
        print(f"Header not found: {e}")

    # Handle missing files
    try:
        prompt = get_prompt('missing_file.md', 'Test')
    except FileNotFoundError as e:
        print(f"File error: {e}")

    # Comprehensive validation
    result = validate_prompt_markdown('prompts/prompts.md')
    if result['valid']:
        print(f"Found {len(result['headers'])} valid headers")
    else:
        print("Validation failed:")
        for error in result['errors']:
            print(f"  - {error}")
"""

import glob
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .utils.data_files import find_data_file


def get_prompt(source: str, header: str) -> str:
    """
    Get prompt from markdown source (file path, directory/wildcard, or string content).

    This function supports multiple input types and automatically detects whether the
    source is a file path, directory, wildcard pattern, or string content. For
    directories and wildcards, it concatenates all .md files and searches across them.

    Args:
        source: File path, directory path, wildcard pattern, or string content
            - File path: 'prompts/prompts.md'
            - Directory: 'prompts/' (searches all .md files)
            - Wildcard: 'prompts/*.md' or 'docs/section*.md'
            - String content: '# Header\\n```\\ncode\\n```'
        header: Header name to search for (any level: #, ##, ###, ####, #####)
            - Case-sensitive exact match
            - Should not include the # symbols
            - Examples: 'Short Commit', 'API Documentation', 'Error Handling'

    Returns:
        str: The code block content following the header, with leading/trailing
             whitespace preserved from the original markdown

    Raises:
        ValueError: If header not found, duplicate headers found, or no code block after header
            - Includes available headers in error message when header not found
            - Shows line numbers and locations for duplicate headers
            - Indicates specific line where code block is missing
        FileNotFoundError: If file path doesn't exist or cannot be read
            - Includes specific file path and underlying error details

    Examples:
        # From string content with inline markdown
        markdown_content = '''# Test Header
        ```python
        print("Hello World")
        ```

        # Another Header
        ```bash
        echo "test"
        ```'''
        prompt = get_prompt(markdown_content, 'Test Header')
        # Returns: 'print("Hello World")'

        # From single file
        prompt = get_prompt('prompts/git_prompts.md', 'Short Commit')
        
        # From package-relative path (works in both dev and installed environments)
        prompt = get_prompt('mcp_coder/prompts/prompts.md', 'Git Commit Message Generation')

        # From directory (searches all .md files)
        prompt = get_prompt('prompts/', 'Short Commit')

        # From wildcard pattern
        prompt = get_prompt('docs/api_*.md', 'Error Handling')

        # Error handling example
        try:
            prompt = get_prompt('prompts/prompts.md', 'NonExistent Header')
        except ValueError as e:
            print(f"Error: {e}")
            # Prints available headers for reference
    """
    # Auto-detect input type and get content
    content = _load_content(source)

    # Find all headers and their positions
    headers = _extract_headers(content)

    # Check for duplicate headers
    header_names = [h["name"] for h in headers]
    duplicates = _find_duplicates(header_names)
    if duplicates:
        duplicate_locations = []
        for dup_name in duplicates:
            locations = [f"line {h['line']}" for h in headers if h["name"] == dup_name]
            duplicate_locations.append(f"'{dup_name}' found at: {', '.join(locations)}")
        raise ValueError(f"Duplicate header(s) found: {'; '.join(duplicate_locations)}")

    # Find the target header
    target_header = None
    for h in headers:
        if h["name"] == header:
            target_header = h
            break

    if target_header is None:
        available_headers = [h["name"] for h in headers]
        raise ValueError(
            f"Header '{header}' not found. Available headers: {available_headers}"
        )

    # Extract code block after the header
    code_block = _extract_code_block_after_header(content, target_header)
    if code_block is None:
        raise ValueError(
            f"No code block found after header '{header}' at line {target_header['line']}"
        )

    return code_block


def validate_prompt_markdown(source: str) -> Dict[str, Any]:
    """
    Validate prompt markdown structure and return detailed results.

    This function checks that the markdown follows the expected format:
    each header followed by exactly one code block, no duplicate headers,
    and proper markdown syntax.

    Args:
        source: File path or string content to validate
            - File path: 'prompts/prompts.md'
            - String content: '# Header\\n```\\ncode\\n```'

    Returns:
        dict: Validation results with the following keys:
            - valid (bool): True if all validation checks pass
            - errors (List[str]): List of error messages (empty if valid)
            - headers (List[Dict]): List of found headers with metadata:
                * name (str): Header text
                * level (int): Header level (1-5)
                * line (int): Line number in source
                * position (int): 0-based line index
            - source_type (str): 'file' or 'string' indicating input type

    Examples:
        # Validate a file
        result = validate_prompt_markdown('prompts/prompts.md')
        if result['valid']:
            print(f"✓ Valid markdown with {len(result['headers'])} headers")
            for header in result['headers']:
                print(f"  - {header['name']} (line {header['line']})")
        else:
            print("✗ Validation failed:")
            for error in result['errors']:
                print(f"  - {error}")

        # Validate string content
        markdown = '''# Header 1
        ```
        code block 1
        ```

        # Header 1
        ```
        duplicate header - this will cause validation error
        ```'''
        result = validate_prompt_markdown(markdown)
        # result['valid'] will be False due to duplicate header

        # Handle file not found
        result = validate_prompt_markdown('nonexistent.md')
        # result['valid'] will be False with file error in result['errors']
    """
    try:
        content = _load_content(source)
        source_type = "file" if _is_file_path(source) else "string"
    except FileNotFoundError as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "headers": [],
            "source_type": "file",
        }

    errors = []
    headers = _extract_headers(content)

    # Check for duplicate headers
    header_names = [h["name"] for h in headers]
    duplicates = _find_duplicates(header_names)
    if duplicates:
        for dup_name in duplicates:
            locations = [f"line {h['line']}" for h in headers if h["name"] == dup_name]
            errors.append(
                f"Duplicate header '{dup_name}' found at: {', '.join(locations)}"
            )

    # Check that each header has a code block
    for header in headers:
        code_block = _extract_code_block_after_header(content, header)
        if code_block is None:
            errors.append(
                f"No code block found after header '{header['name']}' at line {header['line']}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "headers": headers,
        "source_type": source_type,
    }


def validate_prompt_directory(directory: str) -> Dict[str, Any]:
    """
    Validate all markdown files in directory including cross-file duplicate detection.

    This function performs comprehensive validation across multiple files:
    - Validates each individual .md file
    - Checks for duplicate headers across different files
    - Provides detailed per-file and aggregate results

    Args:
        directory: Directory path to validate
            - Must be an existing directory
            - Only .md files are processed
            - Subdirectories are not recursively searched

    Returns:
        dict: Comprehensive validation results with keys:
            - valid (bool): True if all files and cross-file checks pass
            - errors (List[str]): All errors found, with file context
            - files_checked (int): Number of .md files processed
            - individual_results (Dict[str, Dict]): Per-file validation results
                * Key: filename (e.g., 'prompts.md')
                * Value: Same structure as validate_prompt_markdown() return

    Examples:
        # Validate entire prompts directory
        result = validate_prompt_directory('prompts/')

        if result['valid']:
            print(f"✓ All {result['files_checked']} files valid")
        else:
            print(f"✗ Found {len(result['errors'])} errors across {result['files_checked']} files:")
            for error in result['errors']:
                print(f"  - {error}")

        # Check individual file results
        for filename, file_result in result['individual_results'].items():
            if not file_result['valid']:
                print(f"Issues in {filename}:")
                for error in file_result['errors']:
                    print(f"  - {error}")

        # Handle directory not found
        result = validate_prompt_directory('nonexistent_dir/')
        # result['valid'] will be False with directory error

        # Empty directory (no .md files)
        result = validate_prompt_directory('empty_dir/')
        # result['valid'] will be True, files_checked will be 0
    """
    if not os.path.isdir(directory):
        return {
            "valid": False,
            "errors": [f"Directory '{directory}' does not exist"],
            "files_checked": 0,
            "individual_results": {},
        }

    # Find all markdown files
    md_files = glob.glob(os.path.join(directory, "*.md"))

    if not md_files:
        return {
            "valid": True,
            "errors": [],
            "files_checked": 0,
            "individual_results": {},
        }

    # Validate individual files
    individual_results = {}
    all_errors = []

    for file_path in md_files:
        file_result = validate_prompt_markdown(file_path)
        filename = os.path.basename(file_path)
        individual_results[filename] = file_result

        # Add file context to errors
        for error in file_result["errors"]:
            all_errors.append(f"{filename}: {error}")

    # Check for cross-file duplicates
    try:
        # Track which file each header came from
        file_headers: Dict[str, List[str]] = {}

        for file_path in sorted(md_files):  # Sort for consistent ordering
            file_content = _load_content(file_path)
            file_headers_list = _extract_headers(file_content)
            filename = os.path.basename(file_path)

            for header in file_headers_list:
                header_name = header["name"]
                if header_name not in file_headers:
                    file_headers[header_name] = []
                file_headers[header_name].append(filename)

        # Check for cross-file duplicates
        for header_name, files in file_headers.items():
            if len(files) > 1:
                all_errors.append(
                    f"Header '{header_name}' appears in multiple files: {', '.join(files)}"
                )

        # Also check using the concatenated approach for consistency with get_prompt
        combined_content = _load_content(
            directory
        )  # This will concatenate all .md files
        combined_headers = _extract_headers(combined_content)
        header_names = [h["name"] for h in combined_headers]
        duplicates = _find_duplicates(header_names)
        if duplicates:
            for dup_name in duplicates:
                # Only add if not already added above
                if not any(dup_name in error for error in all_errors):
                    all_errors.append(
                        f"Duplicate header '{dup_name}' found across files"
                    )

    except Exception as e:
        all_errors.append(f"Error checking cross-file duplicates: {str(e)}")

    return {
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "files_checked": len(md_files),
        "individual_results": individual_results,
    }


def _is_package_relative_path(source: str) -> bool:
    """
    Detect if source is a package-relative path that should use find_data_file.
    
    Package-relative paths typically start with a package name (like 'mcp_coder/prompts/...')
    and don't contain '..' or start with '/' or '\' (which would indicate absolute paths
    or relative paths from current directory).
    
    Args:
        source: Path string to check
        
    Returns:
        bool: True if this looks like a package-relative path
    """
    if not _is_file_path(source):
        return False
        
    # Skip if it's a directory, wildcard, or absolute path
    if (
        source.endswith('/') or 
        source.endswith('\\') or
        '*' in source or 
        '?' in source or
        source.startswith('/') or
        source.startswith('\\') or
        (len(source) > 1 and source[1] == ':')  # Windows drive letter
    ):
        return False
        
    # Skip relative paths that go up directories
    if '..' in source:
        return False
        
    # Check if it looks like a package path (contains at least one slash and doesn't start with .)
    return ('/' in source or '\\' in source) and not source.startswith('.')


def _resolve_package_path(source: str) -> Optional[Path]:
    """
    Resolve a package-relative path using find_data_file.
    
    This function attempts to parse the source as 'package_name/relative_path'
    and use find_data_file to locate it robustly.
    
    Args:
        source: Package-relative path like 'mcp_coder/prompts/prompts.md'
        
    Returns:
        Path: Resolved path to the file, or None if resolution failed
    """
    try:
        # Normalize path separators
        normalized_source = source.replace('\\', '/')
        parts = normalized_source.split('/')
        
        if len(parts) < 2:
            return None
            
        # Try different package name combinations
        # First try: first part as package name
        package_name = parts[0]
        relative_path = '/'.join(parts[1:])
        
        try:
            resolved_file = find_data_file(
                package_name=package_name,
                relative_path=relative_path,
                development_base_dir=None  # Auto-detect environment
            )
            return resolved_file
        except (FileNotFoundError, ImportError):
            pass
            
        # Second try: first two parts as package name (e.g., 'mcp_coder.prompts')
        if len(parts) >= 3:
            package_name = f"{parts[0]}.{parts[1]}"
            relative_path = '/'.join(parts[2:])
            
            try:
                resolved_file = find_data_file(
                    package_name=package_name,
                    relative_path=relative_path,
                    development_base_dir=None
                )
                return resolved_file
            except (FileNotFoundError, ImportError):
                pass
                
    except Exception:
        # If anything goes wrong with package resolution, fall back to normal path handling
        pass
        
    return None


def _load_content(source: str) -> str:
    """
    Load content from source (auto-detect file path vs string content).
    For directories/wildcards, concatenate all .md files.

    This is an internal function that handles the complexity of determining
    whether the input is a file path, directory, wildcard pattern, or
    string content, and loads the appropriate content.

    Args:
        source: File path, directory, wildcard, or string content

    Returns:
        str: The loaded content. For directories/wildcards, this is the
             concatenated content of all matching .md files separated by
             double newlines.

    Raises:
        FileNotFoundError: If file/directory doesn't exist or cannot be read
    """
    if _is_file_path(source):
        # First, try to resolve as package-relative path
        if _is_package_relative_path(source):
            resolved_path = _resolve_package_path(source)
            if resolved_path and resolved_path.exists():
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as e:
                    # Fall through to normal path handling if package resolution fails
                    pass
                    
        if os.path.isdir(source):
            # Directory - load all .md files
            md_files = glob.glob(os.path.join(source, "*.md"))
            if not md_files:
                return ""

            combined_content = []
            for file_path in sorted(md_files):  # Sort for consistent ordering
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        combined_content.append(content)
                except Exception as e:
                    raise FileNotFoundError(f"Error reading file {file_path}: {str(e)}")

            return "\n\n".join(combined_content)

        elif "*" in source or "?" in source:
            # Wildcard pattern
            matched_files = glob.glob(source)
            if not matched_files:
                return ""

            combined_content = []
            for file_path in sorted(matched_files):
                if file_path.endswith(".md"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            combined_content.append(content)
                    except Exception as e:
                        raise FileNotFoundError(
                            f"Error reading file {file_path}: {str(e)}"
                        )

            return "\n\n".join(combined_content)

        else:
            # Single file
            try:
                with open(source, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"File '{source}' not found")
            except Exception as e:
                raise FileNotFoundError(f"Error reading file '{source}': {str(e)}")
    else:
        # String content
        return source


def _is_file_path(source: str) -> bool:
    """
    Detect if source is a file path vs string content using simple heuristics.

    This function uses several heuristics to distinguish between file paths
    and markdown content strings:
    - Presence of newlines or # at start indicates content
    - Path separators, extensions, wildcards indicate file paths
    - Short strings without markdown indicators are assumed to be paths

    Args:
        source: Input string to check

    Returns:
        bool: True if likely a file path, False if likely string content
    """
    # If it contains newlines or starts with #, treat as content
    if "\n" in source or source.strip().startswith("#"):
        return False

    # If it looks like a path (has path separators or file extensions), treat as file path
    if (
        "/" in source
        or "\\" in source
        or "." in source
        or "*" in source
        or "?" in source
    ):
        return True

    # Default to treating short strings as file paths
    return len(source) < 200


def _extract_headers(content: str) -> List[Dict[str, Any]]:
    """
    Extract all headers from markdown content.

    This function finds all markdown headers (levels 1-5) and returns
    detailed information about each one including position data.

    Args:
        content: Markdown content

    Returns:
        list: List of header dictionaries with keys:
            - name (str): Header text without # symbols
            - level (int): Header level (1-5)
            - line (int): 1-based line number
            - position (int): 0-based line index
    """
    headers = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Match headers with any level (# ## ### #### #####)
        match = re.match(r"^(#{1,5})\s+(.+)$", line.strip())
        if match:
            level = len(match.group(1))
            name = match.group(2).strip()

            headers.append(
                {
                    "name": name,
                    "level": level,
                    "line": line_num,
                    "position": line_num - 1,  # 0-based index for lines array
                }
            )

    return headers


def _extract_code_block_after_header(
    content: str, header: Dict[str, Any]
) -> Union[str, None]:
    """
    Extract the first code block after a header.

    This function looks for the first ``` fenced code block that appears
    after the given header, stopping if it encounters another header first.

    Args:
        content: Full markdown content
        header: Header dictionary with position info

    Returns:
        str or None: Code block content (excluding ``` markers), or None
                     if no code block found before the next header
    """
    lines = content.split("\n")
    start_line = header["position"] + 1  # Start searching after the header

    # Look for the start of a code block (```)
    code_start = None
    for i in range(start_line, len(lines)):
        if lines[i].strip().startswith("```"):
            code_start = i
            break
        # Stop if we hit another header
        if re.match(r"^#{1,5}\s+", lines[i].strip()):
            break

    if code_start is None:
        return None

    # Find the end of the code block
    code_end = None
    for i in range(code_start + 1, len(lines)):
        if lines[i].strip() == "```":
            code_end = i
            break

    if code_end is None:
        return None

    # Extract the code content (excluding the ``` lines)
    code_lines = lines[code_start + 1 : code_end]
    return "\n".join(code_lines)


def _find_duplicates(items: List[str]) -> List[str]:
    """
    Find duplicate items in a list.

    Args:
        items: List of items to check

    Returns:
        list: List of items that appear more than once (unique duplicates)
    """
    seen = set()
    duplicates = set()

    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)

    return list(duplicates)
