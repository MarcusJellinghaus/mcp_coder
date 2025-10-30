# Step 3: Write Integration Tests for CLI Argument Parsing

## LLM Prompt
```
Implement Step 3 from the MCP Config File Selection Support plan (see pr_info/steps/summary.md).

Write integration tests to verify that the --mcp-config CLI argument is properly parsed and passed through to the Claude CLI provider.

Follow TDD: Write tests FIRST before CLI implementation.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

## Objective
Create integration tests that verify end-to-end flow from CLI argument parsing to command execution.

## WHERE
**File to create:**
- `tests/integration/test_mcp_config_integration.py`

**Dependencies:**
- Existing CLI test utilities
- Mock subprocess execution
- Temporary file/directory fixtures

## WHAT

### Main Test Functions

**Minimal Test Approach:** Test two representative commands (implement = most complex, prompt = simplest) to prove the pattern works without redundant tests.

```python
def test_implement_with_mcp_config_argument() -> None:
    """Verify implement command (most complex) accepts and uses --mcp-config"""

def test_prompt_with_mcp_config_argument() -> None:
    """Verify prompt command (simplest) accepts and uses --mcp-config"""

def test_mcp_config_not_required() -> None:
    """Verify commands work without --mcp-config (backward compatibility)"""

def test_mcp_config_with_relative_path() -> None:
    """Verify relative paths work for --mcp-config"""
```

## HOW

### Integration Points

```python
# Imports
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from mcp_coder.cli.main import main
from mcp_coder.cli.commands.implement import implement_command
from mcp_coder.cli.commands.prompt import prompt_command
```

### Test Fixtures

```python
@pytest.fixture
def mock_claude_cli_success():
    """Mock successful Claude CLI execution"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"answer": "test", "sessionId": "123"}'
        )
        yield mock_run

@pytest.fixture
def temp_mcp_config(tmp_path):
    """Create temporary MCP config file"""
    config_file = tmp_path / ".mcp.test.json"
    config_file.write_text('{"mcpServers": {}}')
    return str(config_file)
```

### Mock Strategy
- Mock `subprocess.run` to avoid actual Claude CLI execution
- Mock file system operations if needed
- Capture and verify command arguments passed to subprocess

## ALGORITHM

### Test Case: implement with MCP Config
```
1. Mock subprocess.run to capture command
2. Call implement_command with mcp_config parameter
3. Assert subprocess.run called
4. Extract command from call args
5. Assert "--mcp-config" in command
6. Assert config file path in command
7. Assert "--strict-mcp-config" in command
```

### Test Case: Backward Compatibility
```
1. Mock subprocess.run
2. Call command WITHOUT mcp_config parameter
3. Assert subprocess.run called successfully
4. Extract command from call args
5. Assert "--mcp-config" NOT in command
6. Assert "--strict-mcp-config" NOT in command
```

### Test Case: Relative vs Absolute Paths
```
1. Create temp config file
2. Test with relative path: "./.mcp.test.json"
3. Verify command contains path
4. Test with absolute path: "/tmp/.mcp.test.json"
5. Verify command contains path
```

## DATA

### Input Data
```python
# CLI arguments simulation
args_with_config = {
    'issue_number': '123',
    'project_dir': Path('/test/project'),
    'mcp_config': '.mcp.linux.json'
}

args_without_config = {
    'issue_number': '123',
    'project_dir': Path('/test/project'),
    'mcp_config': None
}
```

### Expected Command Patterns
```python
# Pattern with mcp_config
expected_command_parts = [
    'claude',
    '-p',
    '--output-format', 'json',
    '--mcp-config', '.mcp.linux.json',
    '--strict-mcp-config'
]

# Pattern without mcp_config (should not contain these)
unexpected_parts = ['--mcp-config', '--strict-mcp-config']
```

### Mock Response Data
```python
# Successful Claude CLI response
mock_response = {
    'returncode': 0,
    'stdout': '{"answer": "Plan created", "sessionId": "abc123"}'
}
```

## Implementation Checklist
- [ ] Create integration test file
- [ ] Implement fixtures for mocking
- [ ] Implement test_implement_with_mcp_config_argument()
- [ ] Implement test_prompt_with_mcp_config_argument()
- [ ] Implement test_mcp_config_not_required()
- [ ] Implement test_mcp_config_with_relative_path()
- [ ] Run tests (should FAIL - CLI implementation not done yet)

## Testing Notes

### Scope
- **Integration level:** Test CLI → Command → LLM Provider flow
- **Not testing:** Actual Claude CLI execution (mocked)
- **Focus:** Argument parsing and command construction

### Exclusions
- Don't test file validation (Claude CLI does this)
- Don't test JSON parsing (Claude CLI does this)
- Don't test network/subprocess errors (separate concern)

## Expected Result
All tests FAIL because CLI parsers don't yet have `--mcp-config` argument and commands don't accept the parameter.

This is correct TDD behavior - integration tests define expected behavior before implementation.

## Verification Command
```bash
# Run integration tests (should fail before Step 4)
pytest tests/integration/test_mcp_config_integration.py -v

# Expected: All tests FAIL with "unrecognized arguments: --mcp-config"
```
