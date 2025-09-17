# Step 5: Implement Commit Auto Command

## Objective
Implement the `commit auto` command that stages changes, generates commit messages using LLM, and creates commits.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and previous steps, implement Step 5: Create the commit auto command.

Requirements:
- Implement commit auto functionality in src/mcp_coder/cli/commands/commit.py
- Use existing git operations from utils/git_operations.py
- Use existing LLM interface from llm_interface.py
- Use the commit prompt from prompts.md (Step 3)
- Follow existing error handling patterns
- Integrate with main.py argument parser

The command should: stage all changes → get diff → send to LLM → parse response → commit.
```

## WHERE (File Structure)
```
src/mcp_coder/cli/commands/
├── __init__.py (updated)
└── commit.py (new)

src/mcp_coder/cli/main.py (updated)
```

## WHAT (Functions & Classes)

### `src/mcp_coder/cli/commands/commit.py`
```python
def execute_commit_auto(args: argparse.Namespace) -> int:
    """Execute commit auto command with optional preview. Returns exit code."""

def generate_commit_message_with_llm(project_dir: Path) -> tuple[bool, str, Optional[str]]:
    """Generate commit message using LLM. Returns (success, message, error)."""

def parse_llm_commit_response(response: str) -> tuple[str, Optional[str]]:
    """Parse LLM response into commit summary and body."""

def validate_git_repository(project_dir: Path) -> tuple[bool, Optional[str]]:
    """Validate current directory is git repo with changes."""
```

### `src/mcp_coder/cli/commands/__init__.py` (updated)
```python
"""CLI command modules."""
from .help import execute_help
from .commit import execute_commit_auto

__all__ = ["execute_help", "execute_commit_auto"]
```

## HOW (Integration Points)

### main.py Updates
```python
# Add commit subparser with auto subcommand
commit_parser = subparsers.add_parser('commit', help='Git commit operations')
commit_subparsers = commit_parser.add_subparsers(dest='commit_mode')
auto_parser = commit_subparsers.add_parser('auto', help='Auto-generate commit message')
auto_parser.add_argument('--preview', action='store_true', help='Show generated message and ask for confirmation')

# Command routing
if args.command == 'commit' and args.commit_mode == 'auto':
    return execute_commit_auto(args)
```

### Import Pattern
```python
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple

from ...utils.git_operations import (
    is_git_repository,
    stage_all_changes, 
    get_git_diff_for_commit,
    commit_staged_files
)
from ...llm_interface import ask_llm
from ...prompt_manager import get_prompt
from ...log_utils import get_logger

logger = logging.getLogger(__name__)
```

## ALGORITHM (Core Logic)

### execute_commit_auto()
```
1. Validate current directory is git repository
2. Stage all changes using stage_all_changes()
3. Generate commit message using LLM
4. Parse and validate LLM response
5. If preview mode: show commit message and ask for confirmation
   - If user cancels: exit with code 0 (user choice)
6. Commit changes using commit_staged_files()
7. Return appropriate exit code
```

### generate_commit_message_with_llm()
```
1. Get git diff using get_git_diff_for_commit()
2. Load commit prompt using get_prompt()
3. Combine prompt with git diff data
4. Send to LLM using ask_llm()
5. Return success status, message, and error
```

## DATA (Return Values)

### execute_commit_auto() → int
- `0`: Success (commit created)
- `1`: User error (not git repo, no changes, invalid LLM response)
- `2`: System error (git failure, LLM failure)

### generate_commit_message_with_llm() → tuple[bool, str, Optional[str]]
- `(True, "commit message", None)`: Success
- `(False, "", "error message")`: Failure

### parse_llm_commit_response() → tuple[str, Optional[str]]
- `("summary", None)`: Single line commit
- `("summary", "body")`: Multi-line commit

### validate_git_repository() → tuple[bool, Optional[str]]
- `(True, None)`: Valid git repo with changes
- `(False, "error message")`: Invalid or no changes

## Tests Required

### `tests/cli/commands/test_commit.py`
```python
def test_execute_commit_auto_success(mock_git_repo, mock_llm):
    """Test successful commit auto execution."""

def test_execute_commit_auto_with_preview_confirmed(mock_git_repo, mock_llm, mock_input):
    """Test commit auto with preview mode - user confirms."""

def test_execute_commit_auto_with_preview_cancelled(mock_git_repo, mock_llm, mock_input):
    """Test commit auto with preview mode - user cancels."""

def test_execute_commit_auto_not_git_repo():
    """Test commit auto in non-git directory."""

def test_execute_commit_auto_no_changes(mock_git_repo):
    """Test commit auto with no staged changes."""

def test_generate_commit_message_with_llm_success(mock_llm):
    """Test successful LLM commit message generation."""

def test_generate_commit_message_with_llm_failure(mock_llm_error):
    """Test LLM failure handling."""

def test_parse_llm_commit_response_single_line():
    """Test parsing single line LLM response."""

def test_parse_llm_commit_response_multi_line():
    """Test parsing multi-line LLM response."""

def test_validate_git_repository_valid():
    """Test git repository validation success."""

def test_validate_git_repository_invalid():
    """Test git repository validation failure."""
```

## Error Handling

### Git Repository Validation
```python
if not is_git_repository(project_dir):
    print("Error: Not a git repository", file=sys.stderr)
    return 1
```

### LLM Communication Errors
```python
try:
    response = ask_llm(prompt_text)
except Exception as e:
    logger.error(f"LLM communication failed: {e}")
    return 2
```

### Commit Creation Errors
```python
commit_result = commit_staged_files(commit_message, project_dir)
if not commit_result["success"]:
    print(f"Error: {commit_result['error']}", file=sys.stderr)
    return 2
```

## LLM Integration

### Prompt Construction
```python
base_prompt = get_prompt("Git Commit Message Generation")
git_diff = get_git_diff_for_commit(project_dir)
full_prompt = f"{base_prompt}\n\n=== GIT DIFF ===\n{git_diff}"

# Use API method as decided
response = ask_llm(full_prompt, provider="claude", method="api")
```

### Response Processing
```python
# Extract commit message from LLM response
# Handle various response formats
# Validate message format before committing
```

## Preview Mode Implementation

### Streamlined Inline Confirmation
```python
def execute_commit_auto(args: argparse.Namespace) -> int:
    """Execute commit auto command with optional preview."""
    logger.info("Starting commit auto", preview=args.preview)
    
    # 1. Validate git repository
    if not validate_git_repository():
        print("Error: Not a git repository", file=sys.stderr)
        return 1
    
    # 2. Stage changes and generate commit message
    success, commit_message, error = generate_commit_message_with_llm()
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        return 2
        
    # 3. Preview mode - simple inline confirmation
    if args.preview:
        print(f"\nGenerated commit message:")
        print(f"{'='*50}")
        print(commit_message)
        print(f"{'='*50}")
        
        if input("\nProceed with commit? (y/N): ").lower() != 'y':
            print("Commit cancelled.")
            return 0
    
    # 4. Create commit
    commit_result = commit_staged_files(commit_message)
    if not commit_result["success"]:
        print(f"Error: {commit_result['error']}", file=sys.stderr)
        return 2
        
    print(f"✅ Commit created: {commit_message.split()[0]}...")
    return 0
```

## Acceptance Criteria
1. ✅ Commit auto command implemented and integrated
2. ✅ Uses existing git operations for staging and committing
3. ✅ LLM integration using ask_llm with API method default
4. ✅ Preview mode with --preview flag implemented using inline confirmation
5. ✅ Comprehensive error handling for all failure modes
6. ✅ `mcp-coder commit auto` works in git repositories
7. ✅ `mcp-coder commit auto --preview` shows message and asks confirmation
8. ✅ Single function handles both auto and preview modes
9. ✅ Appropriate exit codes for different scenarios
10. ✅ All tests pass with mocked dependencies
11. ✅ Proper structured logging and user feedback
