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

## Refined Decisions from Plan Review (September 2025)

### 16. Verbosity Implementation - SINGLE FLAG WITH VALUES
**Decision**: Use single `--verbosity` flag instead of separate boolean flags
- Command: `--verbosity={just-text|verbose|raw}`
- Default: `just-text` when no flag specified
- Examples: `mcp-coder prompt "question" --verbosity=verbose`
**Rationale**: Cleaner CLI interface, more intuitive than multiple boolean flags

### 17. Implementation Steps - KEEP 12 GRANULAR STEPS
**Decision**: Maintain the detailed 12-step TDD approach
**Rationale**: Provides better safety and easier debugging, chosen over consolidation for quality

### 18. Test Coverage - KEEP 5 COMPREHENSIVE TESTS
**Decision**: Maintain all 5 essential tests without consolidation
- `test_basic_prompt_success()`
- `test_prompt_api_error()`
- `test_verbosity_levels()`
- `test_store_response()`
- `test_continue_from()`
**Rationale**: Aligns with granular approach, ensures thorough testing coverage

### 19. CLI Integration - TOP-LEVEL COMMAND
**Decision**: Add `prompt` as top-level command alongside `help`, `verify`, `commit`
**Implementation**: Extend `create_parser()` in `main.py` with prompt subparser
**Rationale**: Follows established CLI pattern, easily accessible

### 20. Error Handling - MAINTAIN "LET IT CRASH"
**Decision**: Keep current "let it crash" approach for initial implementation
**Future**: Fine-tune error handling based on actual usage patterns
**Rationale**: Maintains KISS principles, allows for raw debugging experience

### 21. Storage Location - PROJECT-SPECIFIC
**Decision**: Keep `.mcp-coder/responses/` in current working directory
**Rationale**: Makes sessions project-specific, logical for development workflows

### 22. Session Management - IMPLEMENT BASIC FIRST
**Decision**: No session file management (size limits, cleanup) in initial implementation
**Future**: Add if needed based on usage patterns
**Rationale**: Focus on core functionality first

### 23. Session File Naming - ISO FORMAT
**Decision**: Use ISO timestamp format for session files
- Format: `response_2025-09-18T14-30-22.json`
- Change from: `response_20250918_143022.json`
**Rationale**: More standardized and readable format
