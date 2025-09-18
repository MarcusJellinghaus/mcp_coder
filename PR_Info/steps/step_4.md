# Step 4: Build Minimal Automation Framework

## Objective
Automate only the pieces we've proven work manually in Steps 0-3. Create a minimal but reliable automation framework based on our exploration findings.

## WHERE
- **Config Helper**: `src/mcp_coder/mcp/config_helper.py` (minimal MCP configuration)
- **Test Suite**: `tests/integration/test_mcp_automated.py` (automated versions of manual tests)
- **Test Runner**: Update existing pytest configuration for MCP tests

## WHAT
### Core Automation Components
```python
class MinimalMCPHelper:
    def setup_test_mcp_config(self, project_dir: Path) -> bool:
        """Set up MCP config for testing based on Step 0 learnings"""
    
    def restore_original_config(self) -> bool:
        """Restore original Claude Desktop config"""
    
    def verify_mcp_connection(self) -> bool:
        """Check if MCP server is connected (based on Step 0 findings)"""

class AutomatedMCPTests:
    def test_file_operations_automated(self):
        """Automated version of Step 1 successful operations"""
    
    def test_response_parsing_automated(self):
        """Automated validation using Step 2 response parsing"""
    
    def test_cleanup_and_isolation(self):
        """Automated version of Step 3 cleanup verification"""
```

### Integration Points
- **Use Step 1 Findings**: Implement only operations that worked reliably
- **Use Step 2 Parsing**: Apply response analysis functions
- **Use Step 3 Cleanup**: Apply proven cleanup strategies

## HOW
### Automation Strategy
- **Conservative Approach**: Only automate what we verified works manually
- **Simple Configuration**: Minimal MCP config changes based on Step 0 learning
- **Reliable Cleanup**: Use proven cleanup methods from Step 3
- **Response Validation**: Use parsing functions from Step 2

### Implementation Priorities
1. **Config Management**: Simple, reliable MCP setup/teardown
2. **Test Automation**: Automated versions of successful manual tests
3. **Validation Pipeline**: Automated response analysis and verification
4. **Error Handling**: Handle known failure modes from exploration

## ALGORITHM
```
For each proven operation from Steps 1-3:
1. Set up test environment using Step 3 utilities
2. Configure MCP server using Step 0 manual process (automated)
3. Execute operation using prompts from Step 1
4. Validate response using Step 2 parsing functions
5. Verify file system changes using Step 3 verification
6. Clean up using Step 3 cleanup methods
```

## DATA
### Automation Configuration
```python
PROVEN_OPERATIONS = [
    # Only include operations that worked reliably in Step 1
    {
        "name": "file_read",
        "prompt_template": "Read the contents of {filename}",
        "expected_tool": "read_file",
        "validation": "content_in_response"
    },
    # Add others based on Step 1 success results
]

AUTOMATION_CONFIG = {
    "mcp_server": "mcp-server-filesystem",  # Based on Step 0 success
    "timeout_seconds": 30,  # Based on Step 1 timing observations
    "max_retries": 2,  # Conservative retry policy
    "cleanup_verification": True  # Based on Step 3 requirements
}
```

## LLM Prompt
```
Please review the exploratory implementation plan in PR_Info, especially step_4.md and the findings from steps 0-3.

I need you to build minimal automation for the MCP operations we've proven work manually.

Key requirements:
1. Create `src/mcp_coder/mcp/config_helper.py` with simple MCP configuration management
2. Build automated tests in `tests/integration/test_mcp_automated.py` 
3. Only automate operations that worked reliably in the exploration steps
4. Use the response parsing functions from Step 2
5. Apply the cleanup strategies from Step 3
6. Keep the automation simple and focused on reliability

This is about automating proven functionality, not adding new features or complex logic.

Please ensure the automated tests match the results of the successful manual tests.
```

## Implementation Notes
- **Build on Success**: Only automate operations that worked in exploration
- **Keep Simple**: Resist adding features not proven in manual testing
- **Error Handling**: Handle known failure modes from exploration steps
- **Test Reliability**: Automated tests should be as reliable as manual tests were
- **Documentation**: Document any differences between manual and automated approaches

## Success Criteria
- ✅ Automated tests produce same results as successful manual tests
- ✅ MCP configuration setup/teardown works reliably without manual intervention
- ✅ Response validation automatically detects MCP usage
- ✅ Test cleanup works automatically and completely
- ✅ Test suite runs reliably without hanging or failing due to infrastructure issues

## Expected Outcomes
- Working automated test suite for proven MCP operations
- Reliable MCP configuration management for testing
- Foundation for expanding automated testing in Step 5
- Clear documentation of what's automated vs what still needs manual setup
- Confidence that automation matches manual testing results

This step transforms our exploration learnings into a reliable automated testing foundation.
