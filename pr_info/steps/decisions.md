# Project Decisions

## Discussed and Decided During Planning Review

### 1. Test Complexity Reduction (Human's Response: \"Much less\")
**Question**: How many test classes should we have for the refactoring?
**Decision**: Minimal approach - Add only 4 test methods instead of 20+ 
- 2 tests for parameter mapping (CLI wrapper functionality)
- 2 tests for save functions (only new functionality)  
- Keep all existing comprehensive tests unchanged
- **Reasoning**: \"This is just refactoring\" - existing tests provide regression coverage

### 2. File Path Handling (Human's Choice: \"A\")
**Question**: How should the save functions handle file paths?
**Options Presented**: 
- A: Accept full paths only 
- B: Accept relative paths and resolve them
- C: Auto-create timestamped filenames if user only provides directory
**Decision**: Accept full paths only (Option A)
- Users must specify complete path like `/path/to/conversation.md`
- No automatic filename generation
- User responsibility for complete path+filename

### 3. Error Handling Strategy (Human's Choice: \"C\")  
**Question**: What should happen if save operations fail?
**Options Presented**:
- A: If markdown save fails but JSON succeeds, continue and log warning
- B: If any save fails, return error code 1 (treat as overall failure)
- C: Best effort - try both saves, log any failures, but don't fail the command
**Decision**: Best effort approach (Option C)
- Try both save operations independently
- Log any failures but don't fail the overall command
- Claude API success + response display is primary goal

### 4. JSON Data Structure (Human's Choice: \"C - start with the current full JSON structure, do not modify it, just store it\")
**Question**: Do we need the full JSON structure shown in the plan?
**Options Presented**:
- A: Keep it simple - just flatten everything into one level
- B: Use the planned structure but without format_version field
- C: Start with minimal structure, enhance later if needed
**Decision**: Store current full JSON structure as-is (Modified Option C)
- Use the complete `response_data` from `ask_claude_code_api_detailed_sync`
- Don't modify or restructure the existing data
- Use same structure as existing `_store_response` function
- Simple approach: just store what we already have

## Implementation Notes Based on Decisions
- Save functions use best-effort error handling with logging
- File paths are user responsibility (full paths required)
- JSON structure preservation maintains existing compatibility
- Minimal test additions leverage existing comprehensive coverage
