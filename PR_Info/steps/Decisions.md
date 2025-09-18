# Project Decisions Log

## Implementation Decisions Made (Updated with Enhanced Scope)

### 1. Test Scope - MINIMAL
**Decision**: Keep only 2 essential tests
- `test_execute_prompt_success()` - Mock successful API call
- `test_execute_prompt_api_error()` - Handle API failures

**Rationale**: Avoid over-testing, keep implementation simple

### 2. Input Validation - NONE
**Decision**: No input validation at all
**Rationale**: Let Claude API handle any input issues naturally, simpler implementation

### 3. Error Handling - NONE  
**Decision**: No error handling, let it crash
**Rationale**: This is a test/debug feature, crashing shows exactly what's wrong

### 4. Task Tracker Integration - SKIP
**Decision**: Skip task tracker, work directly from step files
**Rationale**: Simpler workflow for this feature

### 5. Output Format - RAW
**Decision**: Print Claude's response directly to stdout
**Rationale**: Simple, no formatting overhead

### 6. API Function Choice - DETAILED
**Decision**: Use `ask_claude_code_api_detailed_sync()` instead of `ask_claude_code_cli()`
**Rationale**: 
- Rich debug information available
- Shows MCP server interactions
- Better reliability (no subprocess)
- Built-in error handling

### 7. Debug Output Level - FULL
**Decision**: Show comprehensive debug information including:
- Session info (ID, model, working directory, API key source)
- MCP servers status and available tools
- Performance metrics (duration, cost, tokens)
- Tool interactions with detailed parameters
- Full raw message content
- Complete Claude response

### 8. MCP Tool Interaction Display - DETAILED
**Decision**: Show tool calls with parameters (Option B format):
```
Tool Interactions:
1. fs on p MCP Coder:read_file
   Parameters: {"file_path": "README.md"}
2. web_search  
   Parameters: {"query": "something"}
```

**Rationale**: Provides insight into MCP server interactions without being overwhelming

### 9. Raw Message Content - FULL
**Decision**: Display complete raw message JSON structures
**Rationale**: Maximum debugging capability for understanding Claude API responses

### 10. Verbosity Levels - THREE LEVELS
**Decision**: Implement three verbosity levels:
- `--just-text` (default): Claude response + tool interactions summary
- `--verbose`: Claude response + tool interactions details + metrics
- `--raw`: Everything + full JSON structures
**Rationale**: Provides flexibility for different debugging needs while keeping default output clean

### 11. Response Storage - ENHANCED
**Decision**: Add `--store-response` parameter to save complete sessions
- **Location**: `.mcp-coder/responses/` directory
- **Content**: Complete session log (prompt + all responses + metadata)
- **Purpose**: Enable follow-up questions and full debugging
**Rationale**: Essential for debugging complex multi-step interactions and conversation continuity

### 12. Continuation Capability - IMMEDIATE
**Decision**: Add `--continue-from <response-file>` parameter
- **Implementation**: Load previous session context for follow-up questions
- **Integration**: Works with current prompt command
**Rationale**: Enables iterative debugging and conversation flow

### 13. Implementation Steps - 12 TDD STEPS
**Decision**: Expand from 4 to 12 small TDD steps
- Each step follows test-first development
- Small, focused implementations
- Clear separation of concerns
**Rationale**: Maintains KISS principles while handling expanded scope

### 14. Test Strategy - 5 ESSENTIAL TESTS
**Decision**: Implement 5 key tests covering core functionality
- `test_basic_prompt_success()`
- `test_prompt_api_error()`
- `test_verbosity_levels()`
- `test_store_response()`
- `test_continue_from()`
**Rationale**: Balanced testing approach - sufficient coverage without over-testing

### 15. Function Structure - 6 SMALL FUNCTIONS
**Decision**: Split formatting into separate functions per verbosity level
- `execute_prompt()` - main entry point
- `_format_just_text()` - default output
- `_format_verbose()` - detailed output
- `_format_raw()` - everything including JSON
- `_store_response()` - session storage
- `_load_previous_chat()` - continuation loading
**Rationale**: Follows single responsibility principle and KISS approach
