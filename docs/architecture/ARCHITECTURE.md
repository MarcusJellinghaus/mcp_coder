# MCP Coder Architecture Documentation

## Document Metadata

**Framework**: Arc42 Template  
**Version**: 1.0  
**Last Updated**: 2025-01-15  
**Status**: Complete (Sections 1-8)  
**Maintainer**: Marcus Jellinghaus  
**Review Frequency**: Quarterly or on major changes  

---

## 1. Introduction & Goals

### System Purpose
AI-powered software development automation toolkit that orchestrates end-to-end GitHub issue workflows from planning through implementation to pull request creation.

### Key Features
- **LLM Integration**: Multi-provider interface with Claude Code CLI/API support
- **GitHub Automation**: Issue-driven workflow automation with status label transitions
- **Git Operations**: Automated repository management and version control
- **Code Quality**: Integrated testing with pylint, pytest, mypy via MCP servers
- **MCP Architecture**: Leverages specialized MCP servers for file operations and quality checks

### Quality Goals
- **Reliability**: Consistent automation workflows with error handling
- **Extensibility**: Support for multiple LLM providers and MCP servers
- **Ease of Use**: Simple CLI interface with clear workflow stages

### Stakeholders
- **Developers**: Primary users for AI-assisted development workflows
- **AI Systems**: Claude Code as the main AI worker component
- **Automation Users**: Teams implementing GitHub issue automation

---

## 2. Architecture Constraints

### Technical Constraints
- **Python 3.11+**: Minimum required Python version
- **Claude Code CLI**: External dependency for AI functionality
- **MCP Server Dependencies**:
  - `mcp-code-checker`: Quality checks (pylint, pytest, mypy)
  - `mcp-file-server`: File operations and management
  - `mcp-config`: Configuration management helper
  - `mcp-shared-utils`: Common components (future)

### Organizational Constraints
- **Single Developer Project**: Individual development and maintenance
- **GitHub-Based Development**: Issue tracking and PR workflows
- **Integration Testing**: Separate repository at `mcpy_coder_integration_test`

### Conventions
- **Mandatory MCP Tool Usage**: No direct bash commands for code quality
- **Code Quality Gates**: All three checks (pylint, pytest, mypy) must pass
- **Documentation as Code**: Version-controlled architecture documentation

---

## 3. Context & Scope

### System Boundary

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐
│ GitHub  │◄──►│  mcp_coder  │◄──►│ Claude Code │◄──►│   MCP Servers       │
│         │    │             │    │             │    │                     │
│ Issues  │    │ (orchestr.) │    │ (AI worker) │    │ • mcp-code-checker  │
│ Labels  │    │             │    │             │    │ • mcp-file-server   │
│ PRs     │    │             │    │             │    │                     │
│ Comments│    │             │    │             │    │                     │
└─────────┘    └─────────────┘    └─────────────┘    └─────────────────────┘
```

***Additional libraries**: mcp-config (configuration helper), mcp-shared-utils (common components)*

### External Systems
- **GitHub Issues API**: Source of workflow triggers and status updates
- **Claude Code CLI**: AI reasoning and content generation
- **Git Repositories**: Version control and code management
- **Integration Test Repository**: External testing environment

### Data Flow
1. **GitHub → mcp_coder**: Issue status changes, requirements
2. **mcp_coder → Claude Code**: Orchestration commands, structured prompts
3. **Claude Code → MCP Servers**: File operations, quality checks, configuration
4. **Claude Code → mcp_coder**: Project plans, code, PR reviews, PR summaries
5. **mcp_coder → GitHub**: Comments, label updates, PR creation

### Component Outputs
- **Claude Code**: Project plans, code implementations, PR reviews, PR summaries
- **MCP Servers**: Quality check results, file operation confirmations
- **mcp_coder**: GitHub interactions (comments, labels, PRs)

---

## 4. Solution Strategy

### Component Responsibilities
- **mcp_coder**: GitHub orchestrator + workflow logic
  - Event-driven automation based on GitHub label changes
  - Workflow state management and transitions
  - GitHub API integration and content posting
- **Claude Code**: AI reasoning + content creation
  - Implementation planning and code generation
  - Code review and PR summary creation
  - MCP server coordination for specialized tasks

### Key Strategies
- **Orchestration Pattern**: Event-driven automation with human decision points
- **AI Delegation**: mcp_coder provides context, Claude Code creates content
- **Tool Abstraction**: Claude Code handles all MCP server interactions
- **Human-AI Collaboration**: Strategic review points (plan review, code review)

### Architecture Patterns
- **Provider Abstraction**: Extensible LLM interface supporting multiple providers
- **Command Pattern**: CLI subcommand structure with consistent interfaces
- **MCP Integration**: Specialized servers for file operations and quality checks

---

## 5. Building Block View

### Core System (`src/mcp_coder/`)
- **Main interface**: `llm_interface.py` - Multi-provider LLM abstraction
- **Prompt management**: `prompt_manager.py` - Template and validation system
- **Code quality**: `mcp_code_checker.py` - Quality check integration

### CLI System (`src/mcp_coder/cli/`)
- **CLI entry point**: `cli/main.py` - Command routing and parsing
- **Command implementations**: `cli/commands/` - Individual CLI commands
- **Help system**: `cli/commands/help.py` - Documentation and usage

### LLM Integration (`src/mcp_coder/llm_providers/`)
- **Claude interface**: `llm_providers/claude/claude_code_interface.py` - Method routing
- **CLI implementation**: `llm_providers/claude/claude_code_cli.py` - Subprocess execution  
- **API implementation**: `llm_providers/claude/claude_code_api.py` - SDK integration
- **Executable finder**: `llm_providers/claude/claude_executable_finder.py` - Installation detection
- **CLI verification**: `llm_providers/claude/claude_cli_verification.py` - Installation validation

### Automation & Operations (`src/mcp_coder/utils/`)
- **Git operations**: `utils/git_operations.py` - Repository automation
- **GitHub integration**: `utils/github_operations/` - API interactions
- **User configuration**: `utils/user_config.py` - TOML settings management
- **Task tracking**: `workflow_utils/task_tracker.py` - Progress management

### Code Quality & Formatting (`src/mcp_coder/formatters/`)
- **Formatter integration**: `formatters/` - Black, isort automation
- **Configuration reading**: `formatters/config_reader.py` - Tool settings

---

## 6. Runtime View

### Scenario 1: GitHub Issue → Implementation Planning
1. **mcp_coder** detects `status:awaiting-planning` label change
2. **mcp_coder** → **Claude Code**: "Create implementation plan for issue X"
3. **Claude Code** → **MCP servers**: Read issue content, analyze codebase
4. **Claude Code** → **mcp_coder**: Returns structured implementation plan
5. **mcp_coder** → **GitHub**: Posts plan as comment, changes label to `status:plan-review`

### Scenario 2: Code Implementation Execution
1. Human approves plan → label changed to `status:plan-ready`
2. **mcp_coder** → **Claude Code**: "Implement according to approved plan"
3. **Claude Code** → **MCP servers**: File operations, code writing, quality checks
4. **Claude Code** → **mcp_coder**: Implementation complete notification
5. **mcp_coder** → **GitHub**: Update status to `status:code-review`

### Scenario 3: Pull Request Creation
1. Human approves code → label changed to `status:ready-pr`
2. **mcp_coder** → **Claude Code**: "Create pull request with summary"
3. **Claude Code** → **MCP servers**: Generate PR description, final quality checks
4. **Claude Code** → **mcp_coder**: PR content and metadata
5. **mcp_coder** → **GitHub**: Create PR, update label to `status:pr-created`

---

## 7. Deployment View

### Local Development Environment
- **Runtime**: Python 3.11+ with pip package installation
- **Dependencies**: Claude Code CLI installation required
- **MCP Servers**: Deployed as separate services
- **Configuration**: User config in `~/.mcp_coder/config.toml`
- **Project Configuration**: `.claude/CLAUDE.md` for project-specific instructions

### Integration Testing
- **Separate Repository**: `mcpy_coder_integration_test` for external testing
- **External Dependencies**: Git repositories, GitHub API access
- **Authentication**: Claude Code CLI authentication, GitHub API tokens

---

## 8. Cross-cutting Concepts

### Testing Strategy & Markers
- **Test categories**: Defined in `pyproject.toml` with specific markers
  - `git_integration`: File system git operations (repos, commits)
    - **When to use**: Testing git workflow automation, repository operations
    - **Requirements**: Local git environment, test repositories
  - `claude_integration`: Claude CLI/API tests (network, auth needed)
    - **When to use**: Testing Claude Code CLI integration, API functionality
    - **Requirements**: Claude Code CLI installed, authentication configured
  - `formatter_integration`: Code formatter integration (black, isort)
    - **When to use**: Testing code formatting automation, tool integration
    - **Requirements**: Formatter tools installed
  - `github_integration`: GitHub API access (network, auth needed)
    - **When to use**: Testing GitHub operations, PR management, issue workflows
    - **Requirements**: GitHub API tokens, network access
- **Fast development**: Use exclusion pattern to skip slow integration tests
- **Parallel execution**: Always use `extra_args: ["-n", "auto"]`
- **Recommended**: `"-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"`
- **Integration testing**: Use specific markers when developing integration features
- **CI/CD**: Run all tests including integration tests in automated pipelines

### Logging Strategy
- **Centralized configuration**: `utils/log_utils.py` - Single point for logging setup
- **Log level reservation**: INFO level reserved for workflow status and progress
- **CLI integration**: `--log-level` parameter in `cli/main.py` for user control

### Configuration Management
- **User config**: TOML files in `~/.mcp_coder/config.toml`
- **Project config**: `.claude/CLAUDE.md` for project-specific instructions
- **File**: `utils/user_config.py` - Configuration access patterns
- **Security**: Never commit tokens, use environment variables for CI/CD

### Quality Gates (Mandatory Pattern)
- **Always run**: pylint, pytest, mypy after code changes
- **MCP integration**: Use `mcp__code-checker__*` tools exclusively
- **Architecture access**: `mcp_code_checker.py` - Quality check orchestration with direct API access for mcp_coder workflows
- **Enforcement**: Documented in `CLAUDE.md` as mandatory requirements

### Command Pattern (CLI)
- **File organization**: `cli/commands/` - One command per file

---

## Appendix

### Key Files Reference
For quick LLM navigation to core architectural components:

**Core Interfaces:**
- `src/mcp_coder/llm_interface.py` - Main LLM abstraction
- `src/mcp_coder/llm_providers/claude/claude_code_interface.py` - Claude routing

**Workflow Engine:**
- `src/mcp_coder/cli/main.py` - CLI entry and command routing
- `src/mcp_coder/utils/git_operations.py` - Git automation
- `src/mcp_coder/utils/github_operations/` - GitHub API integration

**Configuration:**
- `.claude/CLAUDE.md` - Project configuration and mandatory patterns
- `src/mcp_coder/utils/user_config.py` - User configuration management
- `pyproject.toml` - Testing markers and tool configuration