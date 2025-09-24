# MCP Coder

An AI-powered software development automation toolkit using Claude Code CLI and MCP servers for intelligent code analysis, testing, and implementation workflows.

> ⚠️ **Currently in active development** - Core features are being implemented

## 🎯 Vision

Automated software feature development with stringent quality controls using AI-powered code analysis and proven testing methodologies.

## ✨ Current Features

- **Extensible LLM Interface**: Multi-provider LLM integration with `ask_llm()` function
- **Claude Code Integration**: Both CLI and Python SDK support via `ask_claude_code()`
- **Dual Implementation Methods**: Choose between CLI (`method="cli"`) or API (`method="api"`)
- **Intelligent Queries**: Ask Claude about code analysis and implementation strategies
- **Git Operations**: Automated git workflows with staging, committing, and status checking
- **Automated Testing**: Integration with pytest, pylint, and mypy via MCP servers

## 🔮 Planned Features

- **Feature Planning**: AI-driven analysis and planning from GitHub issues
- **Implementation Workflows**: Automated TDD with test-first development
- **Pull Request Management**: Automated branch creation, PR summaries, and reviews
- **AI-Generated Commit Messages**: Smart commit message generation based on changes

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Coder     │    │   Claude Code    │    │  MCP Servers    │
│   (Python)      │◄──►│     CLI          │◄──►│                 │
│                 │    │                  │    │ • Code Checker  │
│ • Workflows     │    │ • AI Planning    │    │ • File System   │
│ • Automation    │    │ • Code Analysis  │    │ • More...       │
│                 │    │ • Implementation │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Claude Code CLI**: Install from [Anthropic's documentation](https://docs.anthropic.com/en/docs/claude-code)
- **Python 3.11+**

### Installation

```bash
git clone https://github.com/MarcusJellinghaus/mcp_coder.git
cd mcp_coder
pip install -e ".[dev]"
```

### Usage

```python
# New extensible interface (recommended)
from mcp_coder import ask_llm

# Ask Claude using CLI method (default)
response = ask_llm("How should I structure this new feature?", provider="claude", method="cli")
print(response)

# Ask Claude using Python SDK method
response = ask_llm("Explain this code pattern", provider="claude", method="api")
print(response)

# Claude-specific interface
from mcp_coder.claude_code_interface import ask_claude_code

# Use CLI method
response = ask_claude_code("Review my code", method="cli")
print(response)

# Use API method
response = ask_claude_code("Optimize this function", method="api")
print(response)

# Legacy interface (still supported)
from mcp_coder import ask_claude
response = ask_claude("How should I structure this new feature?")
print(response)
```

### Session Storage and Continuation

```bash
# Start a conversation and store the response
mcp-coder prompt "Start project planning" --store-response

# Continue from a specific session file
mcp-coder prompt "What's next?" --continue-from response_2025-09-19T14-30-22.json

# Continue from the most recent session (automatic discovery)
mcp-coder prompt "What's next?" --continue
```

### Git Operations

```python
from mcp_coder import (
    is_git_repository,
    get_full_status,
    commit_all_changes,
    commit_staged_files,
    git_push
)
from pathlib import Path

# Check if directory is a git repository
repo_path = Path(".")
if is_git_repository(repo_path):
    print("This is a git repository")
    
    # Get repository status
    status = get_full_status(repo_path)
    print(f"Staged: {status['staged']}")
    print(f"Modified: {status['modified']}")
    print(f"Untracked: {status['untracked']}")
    
    # Commit all changes
    result = commit_all_changes("Add new feature", repo_path)
    if result.success:
        print(f"Successfully committed: {result.commit_hash}")
    else:
        print(f"Commit failed: {result.error}")
        
    # Or commit only staged files
    staged_result = commit_staged_files("Fix bug in parser", repo_path)
    if staged_result.success:
        print(f"Staged files committed: {staged_result.commit_hash}")
        
    # Complete commit + push workflow
    commit_result = commit_all_changes("Add new feature", repo_path)
    if commit_result.success:
        push_result = git_push(repo_path)
        if push_result["success"]:
            print("Successfully committed and pushed changes")
        else:
            print(f"Push failed: {push_result['error']}")
    else:
        print(f"Commit failed: {commit_result.error}")
```

## 📋 API Reference

### High-Level Interface

#### `ask_llm(question, provider="claude", method="cli", timeout=60)`

Main entry point for LLM interactions with extensible provider support.

**Parameters:**
- `question` (str): The question to ask the LLM
- `provider` (str): LLM provider to use (currently supports "claude")
- `method` (str): Implementation method ("cli" or "api")
- `timeout` (int): Request timeout in seconds (default: 60)

**Returns:** LLM response as string

### Claude-Specific Interface

#### `ask_claude_code(question, method="cli", timeout=60)`

Claude Code interface with routing between CLI and API methods.

**Parameters:**
- `question` (str): The question to ask Claude
- `method` (str): Implementation method ("cli" or "api")
- `timeout` (int): Request timeout in seconds (default: 60)

**Returns:** Claude's response as string

### Implementation Methods

- **CLI Method** (`method="cli"`): Uses Claude Code CLI executable
  - Requires Claude Code CLI installation
  - Uses existing CLI subscription authentication
  - Subprocess-based execution

- **API Method** (`method="api"`): Uses Claude Code Python SDK
  - Leverages existing CLI authentication automatically
  - Direct Python API integration
  - Enhanced error handling and response parsing

### Legacy Interface

#### `ask_claude(question, timeout=60)`

Backward-compatible interface using CLI method.

**Parameters:**
- `question` (str): The question to ask Claude
- `timeout` (int): Request timeout in seconds (default: 60)

**Returns:** Claude's response as string

### Git Operations

#### `is_git_repository(repo_path)`

Check if a directory is a git repository.

**Parameters:**
- `repo_path` (Path): Path to the directory to check

**Returns:** Boolean indicating if directory is a git repository

#### `get_full_status(repo_path)`

Get comprehensive git repository status including staged, modified, and untracked files.

**Parameters:**
- `repo_path` (Path): Path to the git repository

**Returns:** Dictionary with 'staged', 'modified', and 'untracked' file lists

#### `commit_all_changes(message, repo_path)`

Stage all changes and create a commit.

**Parameters:**
- `message` (str): Commit message
- `repo_path` (Path): Path to the git repository

**Returns:** CommitResult object with success status, commit hash, and error details

#### `commit_staged_files(message, repo_path)`

Commit only the currently staged files.

**Parameters:**
- `message` (str): Commit message
- `repo_path` (Path): Path to the git repository

**Returns:** CommitResult object with success status, commit hash, and error details

#### Additional Git Functions

For more advanced git operations, import from `mcp_coder.utils`:

- `get_staged_changes()`: Get list of staged files
- `get_unstaged_changes()`: Get modified and untracked files
- `stage_specific_files()`: Stage selected files
- `stage_all_changes()`: Stage all unstaged changes
- `git_move()`: Move/rename files with git tracking
- `is_file_tracked()`: Check if file is tracked by git

## 🛠️ Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run code quality checks
pylint src/
mypy src/
```

## 📚 Documentation

- [Development Process](PR_Info/DEVELOPMENT_PROCESS.md) - Detailed methodology
- [Project Vision](project_idea.md) - Comprehensive project overview

## 🔗 Related Projects

- [mcp-code-checker](https://github.com/MarcusJellinghaus/mcp-code-checker) - Code quality MCP server
- [mcp_server_filesystem](https://github.com/MarcusJellinghaus/mcp_server_filesystem) - File system MCP server

---

*Built with ❤️ and AI by [Marcus Jellinghaus](https://github.com/MarcusJellinghaus)*