# Step 2: Explore Response Analysis and MCP Detection

## Objective
Understand how to reliably detect MCP usage in Claude Code API responses. Build simple parsing functions that can identify when MCP tools were used and which specific tools were called.

## WHERE
- **Implementation File**: `src/mcp_coder/mcp/response_parser.py` (simple functions, not a class yet)
- **Test File**: `tests/mcp/test_response_parser.py`
- **Data Collection**: Save real API responses from Step 1 as test fixtures

## WHAT
### Core Functions to Build
```python
def detect_mcp_usage(response: dict) -> bool:
    """Return True if response shows MCP tools were used"""

def extract_mcp_tools_used(response: dict) -> list[str]:
    """Return list of MCP tool names that were used"""

def extract_response_content(response: dict) -> str:
    """Get the main response text for verification"""

def save_response_example(response: dict, operation_name: str) -> None:
    """Save response as example for future testing"""
```

### Key Questions to Answer
- Where in the response structure does MCP tool usage appear?
- How can we reliably distinguish MCP usage from regular responses?
- What response fields contain the information we need?
- Are there different response formats to handle?

## HOW
### Integration Points
- **Use Step 1 Results**: Analyze actual responses collected in previous step
- **Simple Implementation**: Focus on working functions, not complex frameworks
- **Test-Driven**: Write tests using real response examples
- **Documentation**: Document response structure findings

### Analysis Strategy
- Collect various response examples from Step 1 tests
- Identify patterns in MCP vs non-MCP responses
- Build simple parsing logic based on observed patterns
- Test parsing functions against collected examples

## ALGORITHM
```
1. Load real API responses from Step 1 testing
2. Manually analyze response structure and MCP indicators
3. Implement simple detection functions based on patterns
4. Test functions against known MCP and non-MCP responses
5. Document findings about response structure
```

## DATA
### Response Collection Strategy
```python
# Collect these response types from Step 1
RESPONSE_EXAMPLES = [
    "file_read_with_mcp.json",      # Response when MCP read_file used
    "file_create_with_mcp.json",    # Response when MCP save_file used
    "file_list_with_mcp.json",      # Response when MCP list_directory used
    "no_mcp_response.json",         # Response with no MCP usage
    "mcp_error_response.json"       # Response when MCP operation fails
]
```

### Expected Response Patterns
Based on Claude SDK documentation, look for:
- MCP server information in session data
- Tool usage indicators
- Response metadata showing MCP calls
- Error patterns when MCP operations fail

## LLM Prompt
```
Please review the exploratory implementation plan in PR_Info, especially step_2.md.

I need you to analyze Claude Code API responses to understand how to detect MCP usage.

Key requirements:
1. Use the actual API responses collected in Step 1 as your data source
2. Create simple functions in `src/mcp_coder/mcp/response_parser.py` to detect MCP usage
3. Focus on working detection, not sophisticated analysis
4. Save example responses as test fixtures in `tests/fixtures/mcp_responses/`
5. Write tests that verify your parsing functions work on real examples

This is exploration focused - we want to understand the response structure before building complex validation logic.

Please document what you discover about where MCP information appears in responses.
```

## Implementation Notes
- **Use Real Data**: Base parsing logic on actual responses from Step 1
- **Keep It Simple**: Boolean detection is more important than detailed analysis
- **Save Examples**: Create test fixtures for future use
- **Handle Variability**: Responses might vary - build robust detection
- **Document Structure**: Record what we learn about response format

## Success Criteria
- ✅ Can reliably detect when MCP tools were used in a response
- ✅ Can identify which specific MCP tools were called
- ✅ Parsing functions work on real response examples
- ✅ Have documented the response structure patterns
- ✅ Created reusable test fixtures for future development

## Expected Learnings
- Response structure and where MCP information appears
- How to distinguish MCP vs non-MCP API calls
- Reliable patterns for detecting different MCP operations
- Edge cases in response format or structure
- Foundation for more sophisticated response analysis

This step provides the parsing foundation needed for automated validation in later steps.
