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

## 🔮 Planned Features

- **Automated Testing**: Integration with pytest, pylint, and mypy via MCP servers
- **Git Operations**: Automated commit workflows with AI-generated commit messages
- **Feature Planning**: AI-driven analysis and planning from GitHub issues
- **Implementation Workflows**: Automated TDD with test-first development
- **Pull Request Management**: Automated branch creation, PR summaries, and reviews

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

## 📋 API Reference

### High-Level Interface

#### `ask_llm(question, provider="claude", method="cli", timeout=30)`

Main entry point for LLM interactions with extensible provider support.

**Parameters:**
- `question` (str): The question to ask the LLM
- `provider` (str): LLM provider to use (currently supports "claude")
- `method` (str): Implementation method ("cli" or "api")
- `timeout` (int): Request timeout in seconds (default: 30)

**Returns:** LLM response as string

### Claude-Specific Interface

#### `ask_claude_code(question, method="cli", timeout=30)`

Claude Code interface with routing between CLI and API methods.

**Parameters:**
- `question` (str): The question to ask Claude
- `method` (str): Implementation method ("cli" or "api")
- `timeout` (int): Request timeout in seconds (default: 30)

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

#### `ask_claude(question, timeout=30)`

Backward-compatible interface using CLI method.

**Parameters:**
- `question` (str): The question to ask Claude
- `timeout` (int): Request timeout in seconds (default: 30)

**Returns:** Claude's response as string

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