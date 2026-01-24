#!/usr/bin/env python3
"""Fix import statements in test files."""

import re
import sys
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix import statements in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace src.mcp_coder with mcp_coder
    original_content = content
    content = re.sub(r'from src\.mcp_coder\.', 'from mcp_coder.', content)
    content = re.sub(r'import src\.mcp_coder\.', 'import mcp_coder.', content)
    content = re.sub(r'"src\.mcp_coder\.', '"mcp_coder.', content)
    content = re.sub(r"'src\.mcp_coder\.", "'mcp_coder.", content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed imports in {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

def main():
    """Fix imports in test files."""
    test_files = [
        "tests/utils/test_branch_status.py",
        "tests/cli/commands/test_check_branch_status.py"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            fix_imports_in_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()