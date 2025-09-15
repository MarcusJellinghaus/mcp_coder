"""
Prompt manager for mcp-coder project.

This module provides functionality to retrieve and validate prompts from markdown files.
Supports file paths, directories/wildcards, and string content with auto-detection.

Main functions:
- get_prompt(source, header): Get prompt from markdown source
- validate_prompt_markdown(source): Validate markdown structure  
- validate_prompt_directory(directory): Validate all markdown files in directory
"""

import os
import re
import glob
from typing import Dict, List, Any, Union
from pathlib import Path


def get_prompt(source: str, header: str) -> str:
    """
    Get prompt from markdown source (file path, directory/wildcard, or string content).
    
    Args:
        source: File path, directory path, wildcard pattern, or string content
        header: Header name to search for (any level: #, ##, ###, ####)
        
    Returns:
        str: The code block content following the header
        
    Raises:
        ValueError: If header not found, duplicate headers found, or no code block after header
        FileNotFoundError: If file path doesn't exist
    """
    # Auto-detect input type and get content
    content = _load_content(source)
    
    # Find all headers and their positions
    headers = _extract_headers(content)
    
    # Check for duplicate headers
    header_names = [h['name'] for h in headers]
    duplicates = _find_duplicates(header_names)
    if duplicates:
        duplicate_locations = []
        for dup_name in duplicates:
            locations = [f"line {h['line']}" for h in headers if h['name'] == dup_name]
            duplicate_locations.append(f"'{dup_name}' found at: {', '.join(locations)}")
        raise ValueError(f"Duplicate header(s) found: {'; '.join(duplicate_locations)}")
    
    # Find the target header
    target_header = None
    for h in headers:
        if h['name'] == header:
            target_header = h
            break
            
    if target_header is None:
        available_headers = [h['name'] for h in headers]
        raise ValueError(f"Header '{header}' not found. Available headers: {available_headers}")
    
    # Extract code block after the header
    code_block = _extract_code_block_after_header(content, target_header)
    if code_block is None:
        raise ValueError(f"No code block found after header '{header}' at line {target_header['line']}")
        
    return code_block


def validate_prompt_markdown(source: str) -> Dict[str, Any]:
    """
    Validate prompt markdown structure, return detailed results.
    
    Args:
        source: File path or string content
        
    Returns:
        dict: Validation results with keys:
            - valid: bool indicating if valid
            - errors: list of error messages
            - headers: list of found headers
            - source_type: 'file' or 'string'
    """
    try:
        content = _load_content(source)
        source_type = 'file' if _is_file_path(source) else 'string'
    except FileNotFoundError as e:
        return {
            'valid': False,
            'errors': [str(e)],
            'headers': [],
            'source_type': 'file'
        }
    
    errors = []
    headers = _extract_headers(content)
    
    # Check for duplicate headers
    header_names = [h['name'] for h in headers]
    duplicates = _find_duplicates(header_names)
    if duplicates:
        for dup_name in duplicates:
            locations = [f"line {h['line']}" for h in headers if h['name'] == dup_name]
            errors.append(f"Duplicate header '{dup_name}' found at: {', '.join(locations)}")
    
    # Check that each header has a code block
    for header in headers:
        code_block = _extract_code_block_after_header(content, header)
        if code_block is None:
            errors.append(f"No code block found after header '{header['name']}' at line {header['line']}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'headers': headers,
        'source_type': source_type
    }


def validate_prompt_directory(directory: str) -> Dict[str, Any]:
    """
    Validate all markdown files in directory including cross-file duplicates.
    
    Args:
        directory: Directory path to validate
        
    Returns:
        dict: Validation results with keys:
            - valid: bool indicating if valid
            - errors: list of error messages
            - files_checked: number of markdown files checked
            - individual_results: dict of per-file validation results
    """
    if not os.path.isdir(directory):
        return {
            'valid': False,
            'errors': [f"Directory '{directory}' does not exist"],
            'files_checked': 0,
            'individual_results': {}
        }
    
    # Find all markdown files
    md_files = glob.glob(os.path.join(directory, "*.md"))
    
    if not md_files:
        return {
            'valid': True,
            'errors': [],
            'files_checked': 0,
            'individual_results': {}
        }
    
    # Validate individual files
    individual_results = {}
    all_errors = []
    
    for file_path in md_files:
        file_result = validate_prompt_markdown(file_path)
        filename = os.path.basename(file_path)
        individual_results[filename] = file_result
        
        # Add file context to errors
        for error in file_result['errors']:
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
                header_name = header['name']
                if header_name not in file_headers:
                    file_headers[header_name] = []
                file_headers[header_name].append(filename)
        
        # Check for cross-file duplicates
        for header_name, files in file_headers.items():
            if len(files) > 1:
                all_errors.append(f"Header '{header_name}' appears in multiple files: {', '.join(files)}")
                
        # Also check using the concatenated approach for consistency with get_prompt
        combined_content = _load_content(directory)  # This will concatenate all .md files
        combined_headers = _extract_headers(combined_content)
        header_names = [h['name'] for h in combined_headers]
        duplicates = _find_duplicates(header_names)
        if duplicates:
            for dup_name in duplicates:
                # Only add if not already added above
                if not any(dup_name in error for error in all_errors):
                    all_errors.append(f"Duplicate header '{dup_name}' found across files")
                
    except Exception as e:
        all_errors.append(f"Error checking cross-file duplicates: {str(e)}")
    
    return {
        'valid': len(all_errors) == 0,
        'errors': all_errors,
        'files_checked': len(md_files),
        'individual_results': individual_results
    }


def _load_content(source: str) -> str:
    """
    Load content from source (auto-detect file path vs string content).
    For directories/wildcards, concatenate all .md files.
    
    Args:
        source: File path, directory, wildcard, or string content
        
    Returns:
        str: The loaded content
        
    Raises:
        FileNotFoundError: If file/directory doesn't exist
    """
    if _is_file_path(source):
        if os.path.isdir(source):
            # Directory - load all .md files
            md_files = glob.glob(os.path.join(source, "*.md"))
            if not md_files:
                return ""
            
            combined_content = []
            for file_path in sorted(md_files):  # Sort for consistent ordering
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        combined_content.append(content)
                except Exception as e:
                    raise FileNotFoundError(f"Error reading file {file_path}: {str(e)}")
            
            return '\n\n'.join(combined_content)
            
        elif '*' in source or '?' in source:
            # Wildcard pattern
            matched_files = glob.glob(source)
            if not matched_files:
                return ""
            
            combined_content = []
            for file_path in sorted(matched_files):
                if file_path.endswith('.md'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            combined_content.append(content)
                    except Exception as e:
                        raise FileNotFoundError(f"Error reading file {file_path}: {str(e)}")
            
            return '\n\n'.join(combined_content)
            
        else:
            # Single file
            try:
                with open(source, 'r', encoding='utf-8') as f:
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
    
    Args:
        source: Input string to check
        
    Returns:
        bool: True if likely a file path, False if likely string content
    """
    # If it contains newlines or starts with #, treat as content
    if '\n' in source or source.strip().startswith('#'):
        return False
    
    # If it looks like a path (has path separators or file extensions), treat as file path
    if ('/' in source or '\\' in source or '.' in source or 
        '*' in source or '?' in source):
        return True
    
    # Default to treating short strings as file paths
    return len(source) < 200


def _extract_headers(content: str) -> List[Dict[str, Any]]:
    """
    Extract all headers from markdown content.
    
    Args:
        content: Markdown content
        
    Returns:
        list: List of header dictionaries with keys: name, level, line, position
    """
    headers = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Match headers with any level (# ## ### #### #####)
        match = re.match(r'^(#{1,5})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            name = match.group(2).strip()
            
            headers.append({
                'name': name,
                'level': level,
                'line': line_num,
                'position': line_num - 1  # 0-based index for lines array
            })
    
    return headers


def _extract_code_block_after_header(content: str, header: Dict[str, Any]) -> Union[str, None]:
    """
    Extract the first code block after a header.
    
    Args:
        content: Full markdown content
        header: Header dictionary with position info
        
    Returns:
        str or None: Code block content, or None if no code block found
    """
    lines = content.split('\n')
    start_line = header['position'] + 1  # Start searching after the header
    
    # Look for the start of a code block (```)
    code_start = None
    for i in range(start_line, len(lines)):
        if lines[i].strip().startswith('```'):
            code_start = i
            break
        # Stop if we hit another header
        if re.match(r'^#{1,5}\s+', lines[i].strip()):
            break
    
    if code_start is None:
        return None
    
    # Find the end of the code block
    code_end = None
    for i in range(code_start + 1, len(lines)):
        if lines[i].strip() == '```':
            code_end = i
            break
    
    if code_end is None:
        return None
    
    # Extract the code content (excluding the ``` lines)
    code_lines = lines[code_start + 1:code_end]
    return '\n'.join(code_lines)


def _find_duplicates(items: List[str]) -> List[str]:
    """
    Find duplicate items in a list.
    
    Args:
        items: List of items to check
        
    Returns:
        list: List of items that appear more than once
    """
    seen = set()
    duplicates = set()
    
    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    
    return list(duplicates)
