#!/usr/bin/env python3
"""Add __all__ exports to git_operations.py if missing."""

file_path = "src/mcp_coder/utils/git_operations.py"

# Read the file
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Check if __all__ already exists
if "__all__" in content:
    print("__all__ already exists in file")
    # Count occurrences
    count = content.count("__all__")
    print(f"Found {count} occurrences of __all__")
else:
    print("__all__ not found, adding it")

    # Add __all__ at the end
    exports = '''

# Explicit exports for mypy
__all__ = [
    "CommitResult",
    "PushResult",
    "branch_exists",
    "checkout_branch",
    "commit_all_changes",
    "commit_staged_files",
    "create_branch",
    "fetch_remote",
    "get_branch_diff",
    "get_current_branch_name",
    "get_default_branch_name",
    "get_full_status",
    "get_git_diff_for_commit",
    "get_github_repository_url",
    "get_parent_branch_name",
    "get_staged_changes",
    "get_unstaged_changes",
    "git_move",
    "git_push",
    "is_file_tracked",
    "is_git_repository",
    "is_working_directory_clean",
    "push_branch",
    "stage_all_changes",
    "stage_specific_files",
]
'''

    # Write the updated content
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(exports)

    print(f"Added __all__ to {file_path}")
