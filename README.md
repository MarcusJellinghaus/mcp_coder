# MCP Coder

An AI-powered software development automation toolkit using Claude Code CLI and MCP servers for intelligent code analysis, testing, and implementation workflows.

> ⚠️ **Currently in active development** - Core features are being implemented

## 🎯 Vision

Automated software feature development with stringent quality controls using AI-powered code analysis and proven testing methodologies.

## ✨ Current Features

- **Claude Code Integration**: Programmatic interaction with Claude Code CLI
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
from mcp_coder.claude_client import ask_claude

# Ask Claude to analyze code or provide implementation guidance
response = ask_claude("How should I structure this new feature?")
print(response)
```

## 🛠️ Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## 📚 Documentation

- [Development Process](PR_Info/DEVELOPMENT_PROCESS.md) - Detailed methodology
- [Project Vision](project_idea.md) - Comprehensive project overview

## 🔗 Related Projects

- [mcp-code-checker](https://github.com/MarcusJellinghaus/mcp-code-checker) - Code quality MCP server
- [mcp_server_filesystem](https://github.com/MarcusJellinghaus/mcp_server_filesystem) - File system MCP server

---

*Built with ❤️ and AI by [Marcus Jellinghaus](https://github.com/MarcusJellinghaus)*