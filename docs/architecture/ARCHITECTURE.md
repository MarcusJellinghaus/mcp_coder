# MCP Coder Architecture Documentation

## Document Metadata

**Framework**: Arc42 Template  
**Version**: 1.7  
**Last Updated**: 2025-10-26  
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
- **Python Library Dependencies**:
  - `PyGithub>=1.59.0`: GitHub API integration for PR management and issue workflows

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
- **Prompt management**: `prompt_manager.py` - Template and validation system (tests: `test_prompt_manager.py`)
- **Code quality**: `mcp_code_checker.py` - Quality check integration (tests: `test_mcp_code_checker_integration.py`)
- **Constants**: `constants.py` - Project-wide constants and paths (tests: ❌ missing)

### LLM System (`src/mcp_coder/llm/`)
- **Interface**: `llm/interface.py` - Multi-provider LLM abstraction (tests: `llm/test_interface.py`)
- **Environment**: `llm/env.py` - Runner environment detection and environment variable preparation for LLM subprocess (tests: `llm/test_env.py`)
  - **Design Decision**: Simplified from filesystem detection to environment variables (Oct 2025)
    - **Rationale**: Use Python's built-in environment information (`VIRTUAL_ENV`, `CONDA_PREFIX`, `sys.prefix`) instead of complex filesystem searches
    - **Benefits**: Universal compatibility (venv/conda/system Python), simpler code (~90% less complexity), more reliable
    - **Key Change**: `MCP_CODER_VENV_DIR` now points to runner environment (where mcp-coder executes), not project directory
- **Formatting**: `llm/formatting/` - Response formatters and SDK utilities
  - `formatters.py` - Text/verbose/raw output formatting (tests: `llm/formatting/test_formatters.py`)
  - `sdk_serialization.py` - SDK message object handling (tests: `llm/formatting/test_sdk_serialization.py`)
- **Storage**: `llm/storage/` - Session persistence
  - `session_storage.py` - Store/load session data (tests: `llm/storage/test_session_storage.py`)
  - `session_finder.py` - Find latest session files (tests: `llm/storage/test_session_finder.py`)
- **Session**: `llm/session/` - Session management
  - `resolver.py` - LLM method parsing and session resolution (tests: `llm/session/test_resolver.py`)
- **Providers**: `llm/providers/` - Provider implementations
  - `claude/` - Claude Code CLI/API integration (tests: `llm/providers/claude/test_*.py`)

### CLI System (`src/mcp_coder/cli/`)
- **CLI entry point**: `cli/main.py` - Command routing and parsing (tests: `cli/test_main.py`)
- **Commands**: `cli/commands/` - Command implementations
  - `prompt.py` - Interactive LLM prompting (tests: `cli/commands/test_prompt.py`)
  - `implement.py` - Implementation workflow executor (tests: `cli/commands/test_implement.py`)
  - `commit.py` - Git commit operations (tests: `cli/commands/test_commit.py`)
  - `help.py` - Documentation and usage (tests: `cli/commands/test_help.py`)
  - `verify.py` - System verification (tests: `cli/commands/test_verify.py`)



### Automation & Operations (`src/mcp_coder/utils/`)
- **Git operations**: `utils/git_operations/` - Modular git automation (tests: `utils/git_operations/test_*.py` 🏷️ git_integration)
  - **Design Decision**: Refactored from single `git_operations.py` file to modular package (Oct 2025)
    - **Rationale**: Improve maintainability by separating concerns into focused modules
    - **Benefits**: Enhanced LLM navigation, isolated testing, clearer responsibility boundaries
    - **Added functionality**: `delete_branch()` for complete branch lifecycle management
  - `branches.py` - Branch management (create, delete, checkout, exists, get current/default/parent)
  - `commits.py` - Commit automation
  - `core.py` - Core types (CommitResult, PushResult) and context utilities
  - `diffs.py` - Diff generation for commits and branches
  - `file_tracking.py` - File status tracking
  - `remotes.py` - Remote operations (fetch, push, GitHub URLs)
  - `repository.py` - Repository queries and status
  - `staging.py` - File staging operations
- **GitHub integration**: `utils/github_operations/` - API interactions (tests: `utils/github_operations/test_*.py` 🏷️ github_integration)
  - `base_manager.py` - Base class for GitHub managers
  - `github_utils.py` - GitHub URL parsing and validation
  - `issue_manager.py` - Issue management operations (tests: `test_issue_manager.py`, `test_issue_manager_integration.py`)
  - `labels_manager.py` - Label management operations (tests: `test_labels_manager.py`)
  - `pr_manager.py` - Pull request management via PyGithub API (tests: `test_pr_manager.py`)
  - Smoke tests: `test_github_integration_smoke.py` - Basic GitHub API connectivity validation
- **User configuration**: `utils/user_config.py` - TOML settings management (tests: `utils/test_user_config*.py`)
- **Task tracking**: `workflow_utils/task_tracker.py` - Progress management (tests: `workflow_utils/test_task_tracker.py`)
- **Clipboard operations**: `utils/clipboard.py` - Commit message clipboard utilities (tests: `utils/test_clipboard.py`)
- **Data file utilities**: `utils/data_files.py` - Package data file location (tests: `utils/test_data_files.py`)
- **Subprocess execution**: `utils/subprocess_runner.py` - MCP STDIO isolation support (tests: ❌ missing)

### Code Quality & Formatting (`src/mcp_coder/formatters/`)
- **Formatter integration**: `formatters/` - Black, isort automation (tests: `formatters/test_*.py` 🏷️ formatter_integration)
- **Configuration reading**: `formatters/config_reader.py` - Tool settings (tests: `formatters/test_config_reader.py` 🏷️ formatter_integration)

### Workflow Automation (`src/mcp_coder/workflows/`)
- **Implementation workflow**: `workflows/implement/` - Modular task automation (tests: `workflows/implement/test_*.py`)
  - **Design Decision**: Converted from standalone script to integrated CLI command (Oct 2025)
    - **Rationale**: Enable direct CLI access via `mcp-coder implement` command
    - **Benefits**: Better integration, shared utilities, consistent error handling
  - `core.py` - Main workflow orchestration and task loop
  - `prerequisites.py` - Git status and prerequisite validation
  - `task_processing.py` - Individual task processing, mypy checks, formatting
  - **CLI Integration**: Accessible via `cli/commands/implement.py`

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
**Legend**: 🏷️ = pytest integration marker, ❌ = missing test coverage

- **Test categories**: Defined in `pyproject.toml` with specific markers
  - `git_integration`: File system git operations (repos, commits) in `utils/git_operations/test_*.py`
    - **When to use**: Testing git workflow automation, repository operations
    - **Requirements**: Local git environment, test repositories
  - `claude_cli_integration`: Claude CLI tests (network, auth needed) in `llm_providers/claude/` + `cli/commands/`
    - **When to use**: Testing Claude Code CLI integration, executable detection
    - **Requirements**: Claude Code CLI installed, authentication configured
  - `claude_api_integration`: Claude API tests (network, auth needed) in `llm_providers/claude/`
    - **When to use**: Testing Claude Code API integration, SDK functionality
    - **Requirements**: Claude Code API access, authentication configured
  - `formatter_integration`: Code formatter integration (black, isort) in `formatters/test_*.py`
    - **When to use**: Testing code formatting automation, tool integration
    - **Requirements**: Formatter tools installed
  - `github_integration`: GitHub API access (network, auth needed) in `utils/github_operations/test_*.py`
    - **When to use**: Testing GitHub operations, PR management, issue workflows
    - **Requirements**: GitHub API tokens, network access
- **Fast development**: Use exclusion pattern to skip slow integration tests
- **Parallel execution**: Always use `extra_args: ["-n", "auto"]`
- **Recommended**: `"-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"`
- **Integration testing**: Use specific markers when developing integration features
- **CI/CD**: Run all tests including integration tests in automated pipelines

### Test Performance & Profiling
**Tools for test optimization and performance tracking**

- **Performance Statistics**: `tools/get_pytest_performance_stats.bat` - Collects runtime statistics for all tests
- **Test Profiler**: `tools/test_profiler_plugin/` - pytest plugin for detailed profiling
  - `test_profiler.bat` - Run tests with profiling enabled
  - `test_profiler_generate_only.bat` - Generate reports from existing profile data
  - `generate_report.py` - Report generation engine
  - Documentation: `tools/test_profiler.md` - Usage and analysis guide
- **Performance Documentation**: `docs/tests/` - Performance analysis and tracking
  - `runtime_statistics.md` - Current runtime statistics and historical data
  - `runtime_statistics_review_process.md` - Process for reviewing test performance
  - `slow_test_review_methodology.md` - Methodology for identifying and optimizing slow tests
  - `performance_data/` - Historical performance data and profiling reports
- **Purpose**: Identify slow tests, track performance regressions, optimize test suite execution time

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
- `src/mcp_coder/llm/interface.py` - Main LLM abstraction
- `src/mcp_coder/llm/providers/claude/claude_code_interface.py` - Claude routing

**Workflow Engine:**
- `src/mcp_coder/cli/main.py` - CLI entry and command routing
- `src/mcp_coder/utils/git_operations/` - Git automation (modular package)
- `src/mcp_coder/utils/github_operations/` - GitHub API integration

**Configuration:**
- `.claude/CLAUDE.md` - Project configuration and mandatory patterns
- `src/mcp_coder/utils/user_config.py` - User configuration management
- `pyproject.toml` - Testing markers and tool configuration
