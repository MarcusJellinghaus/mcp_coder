# Implementation Decisions

## Overview
Decisions made during project plan review and discussion for the --continue-from-last parameter feature.

## Key Decisions

### 1. Test Complexity Reduction
**Decision**: Reduce test methods from 5 to 3 focused tests
- Combine edge cases (no directory + no files) into single test
- Keep: success case, edge cases, sorting/mixed files
- **Rationale**: Avoid over-testing while maintaining full coverage

### 2. CLI Integration Testing Approach  
**Decision**: Only test CLI integration in `test_prompt.py`
- Skip separate argument parsing tests in `test_main.py`
- **Rationale**: Argparse handles mutual exclusivity automatically, focus on functionality

### 3. Documentation Strategy
**Decision**: Update README.md + CLI argument help + simplified help.py
- Remove examples from help text (keep only in README.md)
- Use `get_help_text()` instead of `handle_no_command()`
- **Rationale**: Simplified help system, avoid duplication

### 4. Error Handling
**Decision**: Show info message "No previous response files found"
- Treat missing directory same as no files
- **Rationale**: Simple, clear user feedback

### 5. File Pattern Validation
**Decision**: Strict validation - only files with proper ISO timestamp patterns
- Validate exact timestamp format in filenames
- **Rationale**: Ensure reliable sorting and avoid confusion

### 6. User Feedback
**Decision**: Show which file was selected when using `--continue-from-last`
- Display selected filename to user
- **Rationale**: Helpful for user awareness and debugging

### 7. Help System Refactoring
**Decision**: Add help system refactoring as Step 1
- Replace `handle_no_command()` with `get_help_text()`
- Remove examples from help functions
- **Rationale**: Prerequisite for clean documentation updates

### 8. Step Structure
**Decision**: Keep 6 implementation steps, add help refactoring as new Step 1
- Total: 7 steps (including help system refactoring)
- **Rationale**: Maintain granular approach while addressing help system first

## Updated Decisions from Final Review

### 9. Parameter Name Change
**Decision**: Change parameter name from `--continue-from-last` to `--continue`
- **Rationale**: Shorter, cleaner, easier to type while maintaining clarity

### 10. Error Handling for No Files
**Decision**: Continue execution with empty context instead of exit code 1
- Show info message: "No previous response files found, starting new conversation"
- **Rationale**: More user-friendly, allows seamless workflow continuation

### 11. User Feedback Detail Level
**Decision**: Keep both count and filename display
- Format: "Found X previous sessions, continuing from: filename"
- **Rationale**: Provides full transparency and context to users

### 12. File Pattern Validation
**Decision**: Maintain strict ISO timestamp validation
- Only accept files matching: `response_YYYY-MM-DDTHH-MM-SS.json`
- **Rationale**: Ensures predictable sorting and reliable behavior

### 13. Directory Configuration
**Decision**: Keep hardcoded `.mcp-coder/responses/` directory
- No environment variables or command line configuration
- **Rationale**: Simplicity for initial implementation

### 14. Implementation Approach
**Decision**: Design only for current `--continue` feature
- No over-engineering for future session management features
- **Rationale**: Implement what's needed now, refactor later if required

### 15. Step Order and Structure
**Decision**: Keep current 7-step implementation order exactly as planned
- Maintain granular approach with separate testing and implementation steps
- **Rationale**: Proven structure, clear separation of concerns
