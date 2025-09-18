# Step 1: Explore Individual MCP File Operations

## Objective
Test each mcp-server-filesystem operation individually to understand their behavior, timing, and reliability. Build knowledge about what prompts trigger which tools and what success looks like.

## WHERE
- **Test File**: `tests/integration/test_mcp_operations_exploration.py`
- **Documentation**: Create `docs/mcp_operation_findings.md` to record observations
- **Test Environment**: Use same manual setup from Step 0

## WHAT
### Operations to Explore
```python
class TestMCPOperationsExploration:
    def test_file_reading_operation(self)
    def test_file_creation_operation(self)
    def test_file_listing_operation(self)
    def test_directory_operations(self)
    def test_file_editing_operation(self)  # If available
```

### Key Questions to Answer
- What prompt reliably triggers each MCP tool?
- How long does each operation typically take?
- What does success vs failure look like in responses?
- Are there any unexpected behaviors or limitations?

## HOW
### Integration Points
- **Build on Step 0**: Use same manual MCP setup
- **Systematic Testing**: One operation per test function
- **Response Collection**: Save actual API responses for analysis
- **Documentation**: Record findings in markdown file

### Exploration Strategy
- Try multiple prompt variations for each operation
- Test with different file types and sizes
- Observe response timing and structure
- Note any error conditions encountered

## ALGORITHM
```
For each MCP operation:
1. Design prompt that should trigger the operation
2. Call Claude Code API with prompt
3. Analyze response for MCP tool usage
4. Verify expected file system changes occurred
5. Document findings and optimal prompts
```

## DATA
### Operation Test Matrix
```python
OPERATIONS_TO_TEST = [
    {
        "name": "file_read",
        "prompts": [
            "Read the contents of README.md",
            "Show me what's in the README file",
            "What does README.md contain?"
        ],
        "expected_tool": "read_file",
        "verify_method": "check_response_contains_file_content"
    },
    {
        "name": "file_create", 
        "prompts": [
            "Create a file called output.txt with content 'Hello MCP'",
            "Make a new file named test_output.txt containing 'Success'"
        ],
        "expected_tool": "save_file",
        "verify_method": "check_file_exists_on_filesystem"
    },
    {
        "name": "file_list",
        "prompts": [
            "List all files in this directory",
            "Show me the files in the current folder",
            "What files are here?"
        ],
        "expected_tool": "list_directory",
        "verify_method": "check_response_contains_known_files"
    }
]
```

### Findings Documentation Format
```markdown
## File Reading Operation
- **Best Prompt**: "Read the contents of [filename]"
- **Response Time**: ~2-3 seconds
- **Success Indicators**: File content appears in response, read_file tool mentioned
- **Failure Cases**: File not found, permission issues
- **Notes**: Works reliably with text files, unsure about binary files
```

## LLM Prompt
```
Please review the exploratory implementation plan in PR_Info, especially step_1.md.

I need you to systematically test individual MCP file operations to understand their behavior.

Key requirements:
1. Create `tests/integration/test_mcp_operations_exploration.py` with tests for each operation
2. Try multiple prompt variations to find what reliably triggers each MCP tool  
3. Create `docs/mcp_operation_findings.md` to document what you discover
4. Test file reading, creation, listing, and directory operations
5. Record response times, success patterns, and any unexpected behaviors

This is pure exploration - we want to understand how each MCP tool behaves before building automation around it.

Please be thorough in documenting your findings, including what doesn't work as expected.
```

## Implementation Notes
- **Systematic Approach**: Test each operation thoroughly before moving to the next
- **Multiple Prompts**: Try different ways to trigger the same operation
- **Real Verification**: Check filesystem for actual changes, not just response content
- **Detailed Documentation**: Record everything for future reference
- **Timing Observations**: Note how long operations take

## Success Criteria
- ✅ Understand reliable prompts for each basic file operation
- ✅ Know what successful MCP tool usage looks like in responses
- ✅ Have documented timing and behavior patterns
- ✅ Identified any operations that don't work reliably
- ✅ Created reference documentation for future automation

## Expected Learnings
- Which prompts consistently trigger which MCP tools
- How to verify operations actually occurred
- What the response structure looks like for different operations
- Any limitations or edge cases in MCP server behavior
- Baseline performance expectations for each operation type

This step builds the knowledge foundation needed for automation in later steps.
