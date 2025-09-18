# Step 2: Create MCP Session Response Validator

## Objective
Implement a response validator that can analyze Claude Code API responses to verify MCP tool usage, extract session information, and validate that MCP server operations actually occurred.

## WHERE
- **File**: `src/mcp_coder/mcp/session_validator.py`
- **Test File**: `tests/mcp/test_session_validator.py`
- **Integration**: Used by integration tests to verify MCP functionality

## WHAT
### Main Functions
```python
class MCPSessionValidator:
    def validate_mcp_response(self, response: dict[str, Any]) -> MCPValidationResult
    def extract_mcp_tools_used(self, response: dict[str, Any]) -> list[str]
    def get_mcp_server_status(self, response: dict[str, Any]) -> dict[str, str]
    def verify_file_operations(self, project_dir: Path, expected_operations: list[dict]) -> bool
    def analyze_session_performance(self, response: dict[str, Any]) -> MCPPerformanceInfo
```

### Data Structures
```python
MCPValidationResult = {
    "mcp_detected": bool,
    "tools_used": list[str],
    "server_status": dict[str, str],
    "file_operations_verified": bool,
    "performance_info": dict[str, Any],
    "errors": list[str]
}

MCPPerformanceInfo = {
    "duration_ms": int,
    "cost_usd": float,
    "tokens_used": dict[str, int],
    "mcp_server_count": int
}
```

## HOW
### Integration Points
- **Import**: From `mcp_coder.llm_providers.claude.claude_code_api` import response types
- **Validation**: Use existing `structlog` for structured logging of validation results
- **File System**: Direct file system checks to verify operations occurred
- **Type Safety**: Use existing `typing` imports and type hints

### Response Analysis Strategy
- Parse `session_info` for MCP server details
- Extract tool usage from response metadata
- Cross-reference expected vs actual file operations
- Calculate performance metrics from response timing data

## ALGORITHM
```
1. Parse Claude Code API detailed response structure
2. Extract MCP server list and connection status
3. Identify tools used during the session
4. Verify file system changes match expected operations
5. Calculate performance and cost metrics
```

## DATA
### Input Parameters
- `response: dict[str, Any]` - Claude Code API detailed response
- `project_dir: Path` - Directory to verify file operations
- `expected_operations: list[dict]` - Expected file operations to verify

### Return Values
- **Success**: `MCPValidationResult` with comprehensive validation details
- **Partial**: Results with warnings for unverified operations
- **Failure**: Results with errors and diagnostic information

## LLM Prompt
```
Please review the implementation plan in PR_Info, especially the summary and step_2.md.

I need you to implement the MCP Session Response Validator that will analyze Claude Code API responses to verify MCP integration is working correctly.

Key requirements:
1. Create `src/mcp_coder/mcp/session_validator.py` with the MCPSessionValidator class
2. Parse Claude Code API detailed responses (as returned by ask_claude_code_api_detailed_sync)
3. Extract MCP server connection status and tools used
4. Verify actual file operations occurred by checking the filesystem
5. Calculate performance metrics (duration, cost, tokens)
6. Include comprehensive unit tests in `tests/mcp/test_session_validator.py`

The validator should work with the response structure documented in `docs/claude_sdk_response_structure.md`. Focus on reliable detection of MCP usage and clear validation results.

Please verify your implementation by testing with sample Claude Code responses and ensure all validation logic is thoroughly tested.
```

## Implementation Notes
- **Response Structure**: Based on `docs/claude_sdk_response_structure.md` format
- **Robust Parsing**: Handle missing or malformed response fields gracefully
- **File Verification**: Direct filesystem checks to confirm operations occurred
- **Performance Tracking**: Extract cost and timing data for analysis
- **Error Reporting**: Clear, actionable error messages for debugging

## Success Criteria
- ✅ Correctly parses Claude Code API detailed response structure
- ✅ Extracts MCP server connection status and tools used
- ✅ Verifies file operations actually occurred on filesystem
- ✅ Calculates accurate performance and cost metrics
- ✅ Handles malformed or incomplete responses gracefully
- ✅ Unit tests cover all validation scenarios including edge cases
