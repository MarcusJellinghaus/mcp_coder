# Step 1: Write Unit Tests for Command Building Logic

## LLM Prompt
```
Implement Step 1 from the MCP Config File Selection Support plan (see pr_info/steps/summary.md).

Write unit tests for the command building logic in claude_code_cli.py that will accept an optional mcp_config parameter and append it to the Claude CLI command.

Follow TDD: Write tests FIRST before any implementation.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

## Objective
Create comprehensive unit tests for `build_cli_command()` function to verify correct command construction with and without `mcp_config` parameter.

## WHERE
**File to create:**
- `tests/unit/llm/providers/claude/test_claude_mcp_config.py`

**Dependencies:**
- `pytest` framework
- Existing test fixtures from `tests/unit/llm/providers/claude/` (if any)

## WHAT

### Main Test Functions

```python
def test_build_cli_command_without_mcp_config() -> None:
    """Verify command built correctly without mcp_config parameter"""

def test_build_cli_command_with_mcp_config() -> None:
    """Verify command includes --mcp-config and --strict-mcp-config when specified"""

def test_build_cli_command_with_session_and_mcp_config() -> None:
    """Verify both --resume and --mcp-config work together"""

def test_ask_claude_code_cli_passes_mcp_config() -> None:
    """Verify ask_claude_code_cli() accepts and passes mcp_config to build_cli_command()"""
```

## HOW

### Integration Points
```python
# Imports
import pytest
from unittest.mock import patch, MagicMock
from mcp_coder.llm.providers.claude.claude_code_cli import (
    build_cli_command,
    ask_claude_code_cli
)

# Test structure
class TestClaudeMcpConfig:
    """Test suite for MCP config parameter handling"""
```

### Test Fixtures (if needed)
```python
@pytest.fixture
def mock_claude_executable() -> str:
    """Provide mock Claude CLI path"""
    return "/usr/bin/claude"
```

## ALGORITHM

### Test Case: Without MCP Config
```
1. Call build_cli_command(claude_cmd="claude", prompt="test")
2. Assert command = ["claude", "-p", "", "--output-format", "json"]
3. Assert "--mcp-config" NOT in command
4. Assert "--strict-mcp-config" NOT in command
```

### Test Case: With MCP Config
```
1. Call build_cli_command(claude_cmd="claude", prompt="test", mcp_config=".mcp.linux.json")
2. Assert command contains ["claude", "-p", "", "--output-format", "json"]
3. Assert "--mcp-config" in command
4. Assert ".mcp.linux.json" follows "--mcp-config"
5. Assert "--strict-mcp-config" in command
```

### Test Case: With Session and MCP Config
```
1. Call build_cli_command(claude_cmd="claude", prompt="test", session_id="abc123", mcp_config=".mcp.linux.json")
2. Assert "--resume" and "abc123" in command
3. Assert "--mcp-config" and ".mcp.linux.json" in command
4. Assert "--strict-mcp-config" in command
```

### Test Case: ask_claude_code_cli Integration
```
1. Mock subprocess.run to return success
2. Call ask_claude_code_cli(prompt="test", mcp_config=".mcp.linux.json")
3. Assert subprocess.run called with command containing "--mcp-config"
4. Assert subprocess.run called with command containing "--strict-mcp-config"
```

## DATA

### Input Data
```python
# Test parameters
prompt: str = "Test prompt"
session_id: Optional[str] = None | "abc123"
mcp_config: Optional[str] = None | ".mcp.linux.json"
claude_cmd: str = "claude"
```

### Expected Output Data
```python
# Expected command structure (list of strings)
command_without_config = [
    "claude", 
    "-p", 
    "", 
    "--output-format", 
    "json"
]

command_with_config = [
    "claude",
    "-p",
    "",
    "--output-format",
    "json",
    "--mcp-config",
    ".mcp.linux.json",
    "--strict-mcp-config"
]
```

## Implementation Checklist
- [ ] Create test file with proper imports
- [ ] Implement test_build_cli_command_without_mcp_config()
- [ ] Implement test_build_cli_command_with_mcp_config()
- [ ] Implement test_build_cli_command_with_session_and_mcp_config()
- [ ] Implement test_ask_claude_code_cli_passes_mcp_config()
- [ ] Run tests (they should FAIL - no implementation yet)
- [ ] Verify test structure with pylint/mypy

## Expected Result
All tests FAIL because `build_cli_command()` and `ask_claude_code_cli()` don't yet accept `mcp_config` parameter.

This is correct TDD behavior - tests first, implementation second.
