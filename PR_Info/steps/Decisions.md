# Project Plan Decisions

## Discussion Summary
This file documents the key decisions made during project plan review and revision.

## Decided Changes

### **Step Structure & Timing**
- **Decision**: Keep 5-step structure but modify Step 2 approach
- **Change**: Step 2 creates minimal working fix first (not just utilities in isolation)
- **Rationale**: Ensures each step provides working progress

### **Integration Test Distribution**
- **Decision**: Distribute integration tests across development steps instead of all at the end
- **Implementation**:
  - Step 2: `test_real_world_sdk_message_integration()` (basic integration test)
  - Step 3: `test_all_verbosity_levels_with_sdk_objects()` (after raw output fixed)
  - Step 4: `test_edge_cases_sdk_message_handling()` (comprehensive edge cases)
- **Rationale**: Follows true TDD - test functionality as it's developed, catch issues earlier

### **Utility Functions**
- **Decision**: Keep all 4 utility functions as planned
- **Functions**: `_is_sdk_message()`, `_get_message_role()`, `_get_message_tool_calls()`, `_extract_tool_interactions()`
- **Rationale**: Good modularity and reusability

### **JSON Serialization**
- **Decision**: Use custom serializer with official Anthropic SDK structure
- **SDK Structure Source**: Official Claude Code SDK Python documentation
- **Implementation**: Use exact dataclass attributes for each message type
- **Rationale**: Precise structure helps with data loading and debugging

### **Compatibility Requirements**
- **Decision**: No backward compatibility required beyond current formats
- **Scope**: Support only dictionary format (tests) + SDK objects (production)
- **Rationale**: Simplifies implementation, no legacy format support needed

### **Performance Requirements**
- **Decision**: Normal responsiveness is sufficient
- **Target**: No special optimization required
- **Rationale**: Prompt command performance is not critical path

## Official SDK Message Structure

From Anthropic Claude Code SDK Python documentation:

```python
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]

@dataclass  
class AssistantMessage:
    content: list[ContentBlock]
    model: str

@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
```

## Implementation Notes

- Use `isinstance()` for SDK object detection
- Implement graceful fallbacks for missing attributes
- Maintain existing test compatibility with dictionary format
- Focus on clarity and maintainability over micro-optimizations
