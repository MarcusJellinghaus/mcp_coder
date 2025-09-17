# Step 6: Implement Commit Clipboard Command

## Objective
Implement the `commit clipboard` command that reads commit messages from clipboard and creates commits.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and previous steps, implement Step 6: Create the commit clipboard command.

Requirements:
- Add clipboard functionality to src/mcp_coder/cli/commands/commit.py
- Use clipboard utilities from Step 4 (utils/clipboard.py)
- Use existing git operations for staging and committing
- Validate clipboard commit message format
- Follow existing error handling patterns
- Integrate with main.py argument parser

The command should: get clipboard → validate format → stage changes → commit.
```

## WHERE (File Structure)
```
src/mcp_coder/cli/commands/commit.py (updated)
src/mcp_coder/cli/main.py (updated)
```

## WHAT (Functions & Classes)

### `src/mcp_coder/cli/commands/commit.py` (additions)
```python
def execute_commit_clipboard(args: argparse.Namespace) -> int:
    """Execute commit clipboard command. Returns exit code."""

def get_commit_message_from_clipboard() -> tuple[bool, str, Optional[str]]:
    """Get and validate commit message from clipboard."""
```

### Updated command exports
```python
# In __init__.py
from .commit import execute_commit_auto, execute_commit_clipboard

__all__ = ["execute_help", "execute_commit_auto", "execute_commit_clipboard"]
```

## HOW (Integration Points)

### main.py Updates
```python
# Add clipboard subcommand to existing commit parser
clipboard_parser = commit_subparsers.add_parser('clipboard', help='Use commit message from clipboard')

# Command routing (add to existing routing)
elif args.command == 'commit' and args.commit_mode == 'clipboard':
    return execute_commit_clipboard(args)
```

### Import Additions
```python
# Add to existing imports in commit.py
from ...utils.clipboard import get_clipboard_text, validate_commit_message, parse_commit_message
```

## ALGORITHM (Core Logic)

### execute_commit_clipboard()
```
1. Validate current directory is git repository
2. Get commit message from clipboard and validate format
3. Stage all changes using stage_all_changes()
4. Commit changes using commit_staged_files()
5. Return appropriate exit code with user feedback
```

### get_commit_message_from_clipboard()
```
1. Get text from clipboard using get_clipboard_text()
2. Validate commit message format using validate_commit_message()
3. Parse message into summary and body if valid
4. Return success status, formatted message, and error
```

## DATA (Return Values)

### execute_commit_clipboard() → int
- `0`: Success (commit created with clipboard message)
- `1`: User error (not git repo, invalid clipboard, no changes)
- `2`: System error (git failure, clipboard access failure)

### get_commit_message_from_clipboard() → tuple[bool, str, Optional[str]]
- `(True, "formatted commit message", None)`: Success
- `(False, "", "error message")`: Failure

## Tests Required

### `tests/cli/commands/test_commit.py` (additions)
```python
def test_execute_commit_clipboard_success(mock_git_repo, mock_clipboard):
    """Test successful commit clipboard execution."""

def test_execute_commit_clipboard_empty_clipboard():
    """Test commit clipboard with empty clipboard."""

def test_execute_commit_clipboard_invalid_format(mock_clipboard):
    """Test commit clipboard with invalid message format."""

def test_execute_commit_clipboard_not_git_repo(mock_clipboard):
    """Test commit clipboard in non-git directory."""

def test_get_commit_message_from_clipboard_success(mock_clipboard):
    """Test successful clipboard message retrieval."""

def test_get_commit_message_from_clipboard_validation_error(mock_clipboard):
    """Test clipboard message validation failure."""
```

## Error Handling

### Clipboard Access Errors
```python
success, clipboard_text, error = get_clipboard_text()
if not success:
    print(f"Error: {error}", file=sys.stderr)
    return 1
```

### Message Validation Errors
```python
is_valid, validation_error = validate_commit_message(clipboard_text)
if not is_valid:
    print(f"Error: Invalid commit message format - {validation_error}", file=sys.stderr)
    return 1
```

### Git Repository Validation
```python
# Reuse validation logic from execute_commit_auto()
is_valid, error = validate_git_repository(project_dir)
if not is_valid:
    print(f"Error: {error}", file=sys.stderr)
    return 1
```

## User Feedback

### Success Messages
```python
print(f"✓ Successfully committed with message: {commit_summary}")
if commit_result["commit_hash"]:
    print(f"✓ Commit hash: {commit_result['commit_hash']}")
```

### Error Messages
```python
# Clear, actionable error messages
print("Error: Clipboard is empty or inaccessible", file=sys.stderr)
print("Error: Multi-line commit message must have empty second line", file=sys.stderr)
print("Error: No changes to commit", file=sys.stderr)
```

## Integration with Existing Code

### Reuse git validation from Step 5
```python
# Use same validate_git_repository() function
is_valid, error = validate_git_repository(Path.cwd())
```

### Reuse staging and commit logic
```python
# Same staging and commit flow as auto command
if not stage_all_changes(project_dir):
    return 2

commit_result = commit_staged_files(commit_message, project_dir)
```

## Message Format Examples

### Valid Clipboard Content:
```
fix: resolve authentication timeout issue
```

```
feat: add user profile management

Implements CRUD operations for user profiles with validation.
```

### Invalid Clipboard Content:
```
feat: add user profiles
This implements user profile management
```
*(Missing empty second line)*

## Acceptance Criteria
1. ✅ Commit clipboard command implemented and integrated
2. ✅ Uses clipboard utilities from Step 4
3. ✅ Validates commit message format before staging
4. ✅ Reuses git operations and validation logic
5. ✅ `mcp-coder commit clipboard` works with valid clipboard content
6. ✅ Clear error messages for invalid clipboard content
7. ✅ All tests pass with comprehensive scenarios
8. ✅ Consistent user experience with commit auto command
