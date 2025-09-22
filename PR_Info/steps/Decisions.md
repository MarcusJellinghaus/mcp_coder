# Implementation Decisions

## Overview
Decisions made during project plan review and discussion for the --continue parameter feature.

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
**Decision**: Update README.md + CLI argument help + parameterized help.py
- Remove examples from short help, keep in detailed help command
- Use `get_help_text(include_examples=bool)` for both scenarios
- **Rationale**: Single function approach, examples where users expect them

### 4. Error Handling
**Decision**: Show info message "No previous response files found"
- Treat missing directory same as no files
- **Rationale**: Simple, clear user feedback

### 5. File Pattern Validation
**Decision**: Strict validation - only files with proper ISO timestamp patterns
- Validate exact timestamp format in filenames
- **Rationale**: Ensure reliable sorting and avoid confusion

### 6. User Feedback
**Decision**: Show which file was selected when using `--continue`
- Display selected filename to user
- **Rationale**: Helpful for user awareness and debugging

### 7. Help System Refactoring
**Decision**: Add help system refactoring as Step 1
- Add `include_examples` parameter to `get_help_text()`
- Preserve examples in help command, remove from no-command scenario
- **Rationale**: Prerequisite for clean documentation updates

### 8. Step Structure
**Decision**: Keep 6 implementation steps, add help refactoring as new Step 1
- Total: 7 steps (including help system refactoring)
- **Rationale**: Maintain granular approach while addressing help system first

## Updated Decisions from Final Review

### 9. Parameter Name Change
**Decision**: Use parameter name `--continue` consistently
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

## Help System Refactoring Decisions (Step 1 Review)

### 16. Help Function Structure
**Decision**: Use single `get_help_text(include_examples: bool = False)` function
- Replace multiple help functions with one parameterized function
- Default to no examples (safe for short help)
- **Rationale**: DRY principle, single source of truth, easier maintenance

### 17. Examples Placement Strategy
**Decision**: Keep examples in help command, remove from no-command scenario
- `mcp-coder help` → `get_help_text(include_examples=True)` (with examples)
- `mcp-coder` (no command) → `get_help_text(include_examples=False)` (without examples)
- **Rationale**: Users expect examples when explicitly asking for help, but not in error scenarios

### 18. Function Removal Strategy
**Decision**: Remove `handle_no_command()` and `get_usage_examples()` dependencies
- Keep `get_usage_examples()` function but only call it when needed
- Update `handle_no_command()` to use new parameterized function
- **Rationale**: Cleaner architecture while preserving existing functionality
