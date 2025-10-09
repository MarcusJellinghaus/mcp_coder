#!/usr/bin/env python3
"""Script to fix mypy type errors in test_issue_branch_manager.py"""

import re
from pathlib import Path

file_path = Path("tests/utils/github_operations/test_issue_branch_manager.py")

# Read the file
content = file_path.read_text(encoding="utf-8")

# Fix 1: Add type ignore to all _Github__requester accesses that don't have it
content = re.sub(
    r'(mock_manager\._github_client\._Github__requester = Mock\(\))(?!\s*#)',
    r'\1  # type: ignore[attr-defined]',
    content
)

content = re.sub(
    r'(mock_manager\._github_client\._Github__requester\.graphql_query = Mock\()(?!\s*#)',
    r'\1  # type: ignore[attr-defined]',
    content
)

content = re.sub(
    r'(mock_manager\._github_client\._Github__requester\.graphql_named_mutation = Mock\()(?!\s*#)',
    r'\1  # type: ignore[attr-defined]',
    content
)

# Fix 2: Add type ignore to all get_linked_branches method assignments that don't have it
content = re.sub(
    r'(mock_manager\.get_linked_branches = Mock\([^)]*\))(?!\s*#)',
    r'\1  # type: ignore[method-assign]',
    content
)

# Fix 3: Add type ignore to all _get_repository method assignments that don't have it
content = re.sub(
    r'(mock_manager\._get_repository = Mock\([^)]*\))(?!\s*#)',
    r'\1  # type: ignore[method-assign]',
    content
)

# Fix 4: Add type annotations for query_response variables
content = re.sub(
    r'^(\s+)(query_response) = \{$',
    r'\1\2: dict[str, Any] = {',
    content,
    flags=re.MULTILINE
)

# Write the fixed content
file_path.write_text(content, encoding="utf-8")

print("Fixed mypy errors in test_issue_branch_manager.py")
