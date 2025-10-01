# LLM Session Management Implementation Plan - Index

## Quick Links

- **[Summary](summary.md)** - Architectural overview, design decisions, and file structure
- **[Step 1](step_1.md)** - Define LLM Response Types and Constants
- **[Step 2](step_2.md)** - Implement Serialization Functions
- **[Step 3](step_3.md)** - Enhance CLI Method with JSON Parsing and Session Support
- **[Step 4](step_4.md)** - Add Session Support to API Method
- **[Step 5](step_5.md)** - Update Interface Router for TypedDict Returns
- **[Step 6](step_6.md)** - Update Top-Level ask_llm() Interface
- **[Step 7](step_7.md)** - Implement prompt_llm() for Full Session Management
- **[Step 8](step_8.md)** - Update Module Exports and Documentation
- **[Step 9](step_9.md)** - Integration Testing and Validation

## Implementation Order

Follow steps sequentially as each builds on previous work:

### Phase 1: Foundation (Steps 1-2)
1. Type definitions and constants
2. Serialization utilities

### Phase 2: CLI Enhancement (Steps 3)
3. CLI method with JSON parsing and sessions

### Phase 3: API Enhancement (Step 4)
4. API method with session support

### Phase 4: Integration Layer (Steps 5-6)
5. Interface router updates
6. Top-level ask_llm() updates

### Phase 5: User Interface (Steps 7-8)
7. New prompt_llm() function
8. Module exports and documentation

### Phase 6: Validation (Step 9)
9. Comprehensive integration tests

## Key Features

✅ **Session Continuity** - Multi-turn conversations with context
✅ **Parallel Safety** - Multiple sessions don't interfere
✅ **Comprehensive Logging** - Full metadata for analysis
✅ **Backward Compatible** - Existing code unchanged
✅ **Versioned Serialization** - Future-proof data format

## Quick Start for LLM

To implement any step:

```
Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_N.md for the specific step requirements

Implement step N following TDD principles with all tests passing.
```

## Files Created

### New Files
- `src/mcp_coder/llm_types.py` - TypedDict definitions
- `src/mcp_coder/llm_serialization.py` - Serialization functions
- `tests/test_llm_types.py` - Type tests
- `tests/test_llm_serialization.py` - Serialization tests
- `tests/test_module_exports.py` - Export tests
- `tests/integration/test_llm_sessions.py` - Integration tests

### Modified Files
- `src/mcp_coder/llm_interface.py` - Add prompt_llm()
- `src/mcp_coder/llm_providers/claude/claude_code_cli.py` - Sessions + TypedDict
- `src/mcp_coder/llm_providers/claude/claude_code_api.py` - Sessions + TypedDict
- `src/mcp_coder/llm_providers/claude/claude_code_interface.py` - Routing updates
- `src/mcp_coder/__init__.py` - Export new functions

## Estimated Timeline

- **Phase 1**: 2-3 hours
- **Phase 2**: 2-3 hours (reduced via pure functions)
- **Phase 3**: 1-2 hours (simplified by using existing code)
- **Phase 4**: 2-3 hours
- **Phase 5**: 2-3 hours
- **Phase 6**: 2-3 hours
- **Total**: 9-14 hours (approximately 1.5-2 full working days)
- **Savings**: Pure function architecture reduces test count by ~40%, saving 2-3 hours

## Success Metrics

1. All tests pass (unit + integration)
2. Code coverage ≥ 90% for new modules
3. Zero breaking changes to existing API
4. Session continuity works for CLI and API
5. Serialization round-trips without data loss
6. Manual validation confirms real-world usage
