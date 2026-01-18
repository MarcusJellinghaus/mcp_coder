# Claude Code Configuration

TODO - to be reviewed
TODO - check mcp-server config - with environment variables and batch file, also required for implement
TODO - setings in folder .claude - explain what could be added to each project

TODO folder / repo specific
.gitignore specific folders, including logs
pr_info


Complete setup and configuration guide for Claude Code CLI to work with MCP Coder workflows.

## Overview

Claude Code CLI is the primary LLM interface for MCP Coder's automated workflows. This guide covers installation, MCP server configuration, and integration with mcp-coder commands.

## Quick Reference

| Topic | Description |
|-------|-------------|
| **Installation** | Claude Code CLI installation and verification |
| **MCP Servers** | Configuring specialized servers for code operations |
| **Authentication** | API key setup and authentication |
| **Platform Files** | `.mcp.*.json` configuration files |

## Installation

### Prerequisites

- **Anthropic API Key**: Required for Claude API access
- **Python 3.11+**: For MCP server compatibility
- **Git**: For repository operations

### Claude Code CLI Installation

Follow the official installation guide:

```bash
# Visit Anthropic's documentation
https://docs.anthropic.com/en/docs/claude-code
```

**Verification:**
```bash
# Verify installation
claude --version

# Test basic functionality
claude -p "Hello, Claude!"
```

## Authentication

### API Key Setup

1. **Get API Key**: Visit [Anthropic Console](https://console.anthropic.com) to create an API key

2. **Configure Authentication**: Claude Code CLI will prompt for API key on first use

3. **Verify Authentication**:
   ```bash
   mcp-coder verify
   ```

## MCP Server Configuration

### What are MCP Servers?

Model Context Protocol (MCP) servers provide specialized tools for Claude Code:

- **mcp-code-checker**: Pylint, pytest, mypy integration
- **mcp-server-filesystem**: Enhanced file operations
- **Custom servers**: Project-specific tools

### Platform-Specific Configuration Files

Create platform-specific MCP configuration files in your project root:

| Platform | File | Purpose |
|----------|------|---------|
| **Linux** | `.mcp.linux.json` | Linux-specific server paths |
| **Windows** | `.mcp.windows.json` | Windows-specific server paths |
| **macOS** | `.mcp.macos.json` | macOS-specific server paths |

### Basic MCP Configuration

**Example `.mcp.linux.json`:**

```json
{
  "mcpServers": {
    "code-checker": {
      "command": "python",
      "args": ["-m", "mcp_code_checker"],
      "env": {
        "PYTHONPATH": "/path/to/project"
      }
    },
    "filesystem": {
      "command": "python", 
      "args": ["-m", "mcp_server_filesystem"],
      "env": {}
    }
  }
}
```

**Example `.mcp.windows.json`:**

```json
{
  "mcpServers": {
    "code-checker": {
      "command": "python",
      "args": ["-m", "mcp_code_checker"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\project"
      }
    },
    "filesystem": {
      "command": "python",
      "args": ["-m", "mcp_server_filesystem"],
      "env": {}
    }
  }
}
```

### Required MCP Servers for MCP Coder

#### 1. mcp-code-checker

**Purpose**: Provides pylint, pytest, and mypy integration

**Installation:**
```bash
pip install mcp-code-checker
```

**Configuration:**
```json
{
  "mcpServers": {
    "code-checker": {
      "command": "python",
      "args": ["-m", "mcp_code_checker"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

**Features:**
- Automated code quality checks
- Test execution with detailed output
- Type checking with mypy
- Configurable check parameters

#### 2. mcp-server-filesystem

**Purpose**: Enhanced file operations with proper permissions

**Installation:**
```bash
pip install mcp-server-filesystem
```

**Configuration:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["-m", "mcp_server_filesystem"],
      "env": {}
    }
  }
}
```

**Features:**
- Secure file read/write operations
- Directory listing and navigation
- File move/rename operations
- Proper access control

## Using MCP Configuration with mcp-coder

### Command Integration

All major mcp-coder commands support MCP configuration:

```bash
# Use specific MCP config
mcp-coder prompt "Analyze code" --mcp-config .mcp.linux.json
mcp-coder implement --mcp-config .mcp.linux.json
mcp-coder create-plan 123 --mcp-config .mcp.linux.json
mcp-coder create-pr --mcp-config .mcp.linux.json
```

### Automatic Platform Detection

**Recommended approach**: Create all platform files and let mcp-coder choose automatically:

```bash
# Create platform-specific configs
touch .mcp.linux.json .mcp.windows.json .mcp.macos.json

# mcp-coder will automatically use the right one
mcp-coder implement
```

## Advanced Configuration

### Environment Variables

**Common environment variables for MCP servers:**

```json
{
  "mcpServers": {
    "code-checker": {
      "command": "python",
      "args": ["-m", "mcp_code_checker"],
      "env": {
        "PYTHONPATH": "/path/to/project",
        "PYTEST_MARKERS": "not integration",
        "PYLINT_CONFIG": ".pylintrc"
      }
    }
  }
}
```

### Custom Server Configuration

**Adding project-specific MCP servers:**

```json
{
  "mcpServers": {
    "code-checker": {
      "command": "python",
      "args": ["-m", "mcp_code_checker"],
      "env": {}
    },
    "filesystem": {
      "command": "python",
      "args": ["-m", "mcp_server_filesystem"],
      "env": {}
    },
    "custom-tools": {
      "command": "python",
      "args": ["-m", "my_custom_mcp_server"],
      "env": {
        "CONFIG_PATH": "/path/to/custom/config"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

#### Error: MCP servers not found

**Symptoms:**
```
Error: MCP server 'code-checker' not accessible
```

**Solutions:**
1. **Verify installation**:
   ```bash
   python -m mcp_code_checker --help
   python -m mcp_server_filesystem --help
   ```

2. **Check Python path**:
   ```bash
   which python
   pip list | grep mcp
   ```

3. **Update configuration paths**:
   ```json
   {
     "mcpServers": {
       "code-checker": {
         "command": "/full/path/to/python",
         "args": ["-m", "mcp_code_checker"]
       }
     }
   }
   ```

#### Error: Permission denied

**Symptoms:**
```
Error: Permission denied accessing project files
```

**Solutions:**
1. **Check file permissions**:
   ```bash
   ls -la .mcp.*.json
   chmod 644 .mcp.*.json
   ```

2. **Verify project path**:
   ```json
   {
     "mcpServers": {
       "filesystem": {
         "command": "python",
         "args": ["-m", "mcp_server_filesystem"],
         "env": {
           "PROJECT_ROOT": "/absolute/path/to/project"
         }
       }
     }
   }
   ```

#### Error: Configuration not found

**Symptoms:**
```
Warning: No MCP configuration found, using default settings
```

**Solutions:**
1. **Create platform-specific config**:
   ```bash
   # Linux/macOS
   cp .mcp.example.json .mcp.linux.json
   
   # Windows
   cp .mcp.example.json .mcp.windows.json
   ```

2. **Specify config explicitly**:
   ```bash
   mcp-coder implement --mcp-config .mcp.linux.json
   ```

### Testing Configuration

**Verify MCP setup:**

```bash
# Test Claude Code CLI
claude mcp list

# Test MCP servers
claude -p "List files in current directory" --mcp-config .mcp.linux.json

# Test mcp-coder integration
mcp-coder prompt "Run code quality checks" --mcp-config .mcp.linux.json
```

## Security Considerations

### API Key Protection

- **Never commit** `.anthropic` folder or API keys
- Use **environment variables** in CI/CD
- **Rotate keys** regularly

### MCP Configuration Security

- **Add to .gitignore**:
  ```gitignore
  # MCP configuration files (may contain sensitive paths)
  .mcp.*.json
  ```

- **Use relative paths** when possible
- **Avoid hardcoded credentials** in MCP configs

## Integration with Development Workflows

### With mcp-coder implement

```bash
# Full implementation workflow with MCP
mcp-coder implement --mcp-config .mcp.linux.json --update-labels
```

**What happens:**
1. Claude Code CLI loads specified MCP servers
2. Implementation uses code-checker for quality validation
3. Filesystem operations go through mcp-server-filesystem
4. All code changes are validated before commits

### With mcp-coder create-plan

```bash
# Plan creation with codebase analysis
mcp-coder create-plan 123 --mcp-config .mcp.linux.json
```

**What happens:**
1. Filesystem MCP server provides secure file access
2. Code-checker MCP server analyzes existing code quality
3. Plan generation includes quality gate requirements

## Related Documentation

- **[Configuration Guide](config.md)** - General mcp-coder configuration
- **[Claude Desktop Configuration](claude-desktop.md)** - Alternative Claude interface setup
- **[Repository Setup](../repository-setup.md)** - Complete project setup guide
- **[Development Process](../processes-prompts/development-process.md)** - Workflow methodology

## External Resources

- **[Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)** - Official Anthropic documentation
- **[MCP Protocol](https://spec.modelcontextprotocol.io/)** - Model Context Protocol specification
- **[mcp-code-checker](https://github.com/MarcusJellinghaus/mcp-code-checker)** - Code quality MCP server
- **[mcp-server-filesystem](https://github.com/MarcusJellinghaus/mcp_server_filesystem)** - Filesystem MCP server