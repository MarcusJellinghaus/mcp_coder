# Step 3: Implement Core Diff Generation Logic

## LLM Prompt
```
I'm implementing a git diff function as described in pr_info/steps/summary.md. This is Step 3 - implement the core diff generation logic.

The function structure from Step 2 should be in place with basic validation. Now I need to:
- Replace the placeholder return with actual diff generation
- Use read-only git operations to get staged, unstaged, and untracked file diffs
- Combine all diffs into a single formatted string
- Use GitPython's repo.git interface for git commands

Focus on the core diff generation - error handling will be refined in Step 4.
```

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py`
- **Location**: Replace placeholder logic in `get_git_diff_for_commit()` function

## WHAT
Replace placeholder with diff generation:
```python
# Inside get_git_diff_for_commit() after validation
repo = Repo(project_dir, search_parent_directories=False)

# Get staged changes diff
staged_diff = repo.git.diff("--cached", "--unified=5", "--no-prefix")

# Get unstaged changes diff  
unstaged_diff = repo.git.diff("--unified=5", "--no-prefix")

# Get untracked files diff
untracked_diff = generate_untracked_files_diff(repo, project_dir)

# Combine all diffs
return combine_diff_sections(staged_diff, unstaged_diff, untracked_diff)
```

## HOW
- **Git operations**: Use `repo.git.diff()` with read-only parameters
- **Helper functions**: Create small helper functions for untracked files and combining
- **Format**: Use same parameters as batch file (`--unified=5`, `--no-prefix`)

## ALGORITHM
```
1. Create Repo object from project_dir
2. Get staged diff using git diff --cached
3. Get unstaged diff using git diff
4. For each untracked file, generate diff vs /dev/null
5. Combine all diff sections with headers
```

## DATA
**Git command parameters**:
- `--unified=5` - 5 lines of context
- `--no-prefix` - remove a/ b/ prefixes
- `--cached` - for staged changes only

**Return format**:
```
=== STAGED CHANGES ===
[staged diff content]

=== UNSTAGED CHANGES ===  
[unstaged diff content]

=== UNTRACKED FILES ===
[untracked files diff content]
```

**Helper functions needed**:
- Generate untracked file diffs using `git diff --no-index /dev/null filename`
- Combine diff sections with appropriate headers
