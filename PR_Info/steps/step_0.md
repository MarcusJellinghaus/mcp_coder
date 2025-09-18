# Step 0: Basic MCP Connectivity Proof-of-Concept

## Objective
Verify Claude Code API can connect to and use MCP servers at all. This is our foundational validation step - if this doesn't work, we need to investigate before proceeding.

## WHERE
- **Test File**: `tests/integration/test_mcp_basic_connectivity.py`
- **API Setup**: Claude Code API configuration with MCP server
- **Test Directory**: Create temporary directory with known test files

## WHAT
### Manual Tasks
1. **Setup mcp-server-filesystem** (already available as dev dependency)
2. **Claude Code API Configuration**
   - Configure MCP server programmatically through API
   - Point mcp-server-filesystem to test directory
   - Verify MCP server connection through API

3. **Create Test Environment**
   - Create temporary directory with known files (README.md, test.py, data.json)
   - Point MCP server to this directory

4. **Basic Connectivity Test**
```python
def test_mcp_basic_connectivity():
    """Test if Claude Code API can connect to MCP server at all"""
    prompt = "List the files in the current directory"
    response = ask_claude_code_api_detailed_sync(prompt)
    
    # Basic checks
    assert response is not None
    assert "README.md" in str(response)  # Our known test file
    
    # Document findings in comments
    print("Response structure:", type(response))
    print("Response keys:", response.keys() if isinstance(response, dict) else "Not a dict")
```

## HOW
### Integration Points
- **Claude Code API**: Use existing `ask_claude_code_api_detailed_sync()` function
- **Manual Configuration**: Document exact steps for Claude Desktop setup
- **Simple Assertions**: Just verify basic functionality works

### API Setup Process
1. Create test directory: `%TEMP%/mcp_test_project/` (Windows temp directory)
2. Add test files with known content
3. Configure MCP server through Claude Code API
4. Verify MCP server connection through API response

## ALGORITHM
```
1. Create test directory with known files
2. Manually configure MCP server in Claude Desktop
3. Write minimal test that calls Claude Code API
4. Check if response mentions our test files
5. Document everything we observe
```

## DATA
### Test Files to Create
```python
TEST_FILES = {
    "README.md": "# MCP Test Project\nThis is a test project for MCP integration.",
    "test.py": "print('Hello from MCP test!')",
    "data.json": '{"test": true, "mcp": "integration"}'
}
```

### Expected Outcomes
- **Success**: Response contains evidence of file listing through MCP
- **Partial Success**: MCP connects but operations don't work as expected
- **Failure**: No MCP connection or tools visible

## LLM Prompt
```
Please review the exploratory implementation plan in PR_Info, especially step_0.md.

I need you to create a basic proof-of-concept test to verify Claude Code can connect to MCP servers.

Key requirements:
1. Create `tests/integration/test_mcp_basic_connectivity.py` with one simple test
2. The test should call Claude Code API with a file listing prompt
3. Document what you observe in the response structure
4. Don't worry about automation or cleanup yet - this is pure exploration
5. Include clear documentation of manual setup steps needed

This is Step 0 - we just want to know if MCP + Claude Code integration works at all before building anything complex.

Please document your findings clearly, including what works, what doesn't, and what the response structure looks like.
```

## Implementation Notes
- **API Setup**: Use Claude Code API for MCP server configuration
- **Simple Test**: One function, basic assertions, lots of logging/documentation
- **Failure-Friendly**: If it doesn't work, that's valuable information too
- **Documentation**: Write down everything you observe about the process

## Success Criteria
- ✅ MCP server connects through Claude Code API
- ✅ Claude Code API call completes without errors
- ✅ Response shows evidence that MCP tools were used (files listed)
- ✅ API setup process is documented for repeatability

## If This Step Fails
- **Stop here** and investigate why MCP integration doesn't work
- **Document the failure** - what error messages, what doesn't connect
- **Research alternatives** - different MCP server, different configuration approach
- **Don't proceed to Step 1** until basic connectivity works

This step is our foundation - everything else depends on this working.
