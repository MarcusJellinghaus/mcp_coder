# Add MCP Config File Selection Support - Implementation Summary

## Issue
**Number:** #161  
**Title:** Add MCP Config File Selection Support

## Problem Statement
Claude Code CLI supports `--mcp-config` parameter to specify alternative MCP configuration files, but mcp-coder doesn't pass this through. This blocks platform-specific configurations (e.g., `.mcp.linux.json` for CI/CD vs `.mcp.json` for local development).

## Solution Overview
Add `--mcp-config` CLI parameter to mcp-coder that passes through to Claude CLI with automatic `--strict-mcp-config` flag.

## Architectural & Design Changes

### 1. CLI Layer (`src/mcp_coder/cli/main.py`)
**Change:** Add `--mcp-config` argument to command parsers
- **Affected commands:** `prompt`, `implement`, `create-plan`, `create-pr`
- **Design:** Optional string parameter, stored in `args.mcp_config`
- **Validation:** None at CLI level (KISS - let Claude CLI validate)

### 2. LLM Provider Layer (`src/mcp_coder/llm/providers/claude/claude_code_cli.py`)
**Change:** Accept and use `mcp_config` parameter in command building
- **Functions affected:**
  - `ask_claude_code_cli()` - Add optional parameter
  - `build_cli_command()` - Append `--mcp-config` and `--strict-mcp-config` to command
- **Design:** Simple string passthrough, no validation logic
- **Integration:** Command list construction

### 3. Command Implementations (4 files)
**Change:** Pass `args.mcp_config` to `ask_llm()` calls
- **Files:**
  - `src/mcp_coder/cli/commands/prompt.py`
  - `src/mcp_coder/cli/commands/implement.py`
  - `src/mcp_coder/cli/commands/create_plan.py`
  - `src/mcp_coder/cli/commands/create_pr.py`
- **Design:** Thread parameter from CLI args to LLM provider

### 4. Coordinator Templates (`src/mcp_coder/cli/commands/coordinator.py`)
**Change:** Hardcode `--mcp-config /workspace/repo/.mcp.linux.json` in templates
- **Affected templates:** All command templates that invoke mcp-coder
- **Design:** Static configuration for Jenkins container environment

### 5. Configuration (`/.gitignore`)
**Change:** Add platform-specific MCP config patterns
- **Patterns:** `.mcp.linux.json`, `.mcp.windows.json`, `.mcp.macos.json`
- **Reason:** Keep platform-specific configs out of version control

## Design Principles Applied

### KISS (Keep It Simple, Stupid)
1. **No intermediate validation** - Let Claude CLI validate file existence and JSON structure
2. **Direct parameter threading** - Pass string through function calls, no complex objects
3. **No abstraction changes** - Keep existing architecture, just add optional parameter
4. **Minimal error handling** - Claude CLI provides clear error messages

### Single Responsibility
- CLI layer: Parse arguments
- Provider layer: Build command with parameters
- Claude CLI: Validate config file

### Fail Fast
- Missing/invalid config files cause Claude CLI to fail immediately with clear message
- No silent fallbacks or degraded behavior

## Files to Create or Modify

### Files to Modify (8 total)
1. `src/mcp_coder/cli/main.py` - Add CLI argument
2. `src/mcp_coder/llm/providers/claude/claude_code_cli.py` - Update command building
3. `src/mcp_coder/cli/commands/prompt.py` - Pass parameter
4. `src/mcp_coder/cli/commands/implement.py` - Pass parameter
5. `src/mcp_coder/cli/commands/create_plan.py` - Pass parameter
6. `src/mcp_coder/cli/commands/create_pr.py` - Pass parameter
7. `src/mcp_coder/cli/commands/coordinator.py` - Update templates
8. `.gitignore` - Add config patterns

### Files to Create (Tests - 2 total)
1. `tests/unit/llm/providers/claude/test_claude_mcp_config.py` - Command building tests
2. `tests/integration/test_mcp_config_integration.py` - End-to-end CLI tests

### No New Modules
- All changes fit within existing module structure
- No new packages or subdirectories needed

## Implementation Strategy

### Test-Driven Development Approach
1. **Step 1:** Write unit tests for command building logic
2. **Step 2:** Implement command building with mcp_config parameter
3. **Step 3:** Write integration tests for CLI argument parsing
4. **Step 4:** Implement CLI argument and thread through commands
5. **Step 5:** Update coordinator templates
6. **Step 6:** Update .gitignore

### Verification Criteria
- All unit tests pass (pytest with markers exclusion)
- All integration tests pass
- Code quality checks pass (pylint, pytest, mypy)
- Backward compatibility maintained (parameter optional)
- Coordinator templates use Linux config

## Risk Assessment

### Low Risk
- **Optional parameter** - No breaking changes to existing functionality
- **Simple passthrough** - Minimal logic to introduce bugs
- **Claude CLI validation** - Errors handled by existing robust code

### Testing Coverage
- Unit tests verify command construction
- Integration tests verify end-to-end flow
- Existing tests ensure no regression

## Success Metrics
- [ ] `mcp-coder --mcp-config .mcp.linux.json create-plan 123` works
- [ ] Claude CLI receives `--mcp-config <path> --strict-mcp-config`
- [ ] Coordinator templates include hardcoded Linux config path
- [ ] All code quality checks pass
- [ ] No regression in existing functionality
