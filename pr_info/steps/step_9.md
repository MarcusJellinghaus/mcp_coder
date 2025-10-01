# Step 9: Integration Testing and Validation

## Context
Create comprehensive integration tests to validate end-to-end functionality of session management and serialization. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Validate that all components work together correctly, session continuity functions as expected, and parallel usage is safe.

## Changes Required

### WHERE: Test File Creation
**New File**: `tests/integration/test_llm_sessions.py`

### WHAT: Integration Test Scenarios

1. **Session Continuity**: Multi-turn conversations
2. **Serialization Round-trip**: Save and load responses
3. **Parallel Safety**: Multiple sessions don't interfere
4. **Cross-Method Compatibility**: CLI and API session behavior
5. **Error Handling**: Invalid session_ids, missing data
6. **Metadata Preservation**: Cost and usage tracking

### HOW: Integration Test Structure

```python
# Use mocked LLM calls that simulate real behavior
# Test complete workflows end-to-end
# Validate session_id propagation
# Verify data integrity through serialization
```

### ALGORITHM: Test Flow

```python
def test_session_continuity():
    # 1. Start conversation with prompt_llm()
    # 2. Extract session_id from result
    # 3. Make follow-up call with same session_id
    # 4. Verify context is maintained (same session_id returned)
    # 5. Validate response coherence
```

### DATA: Test Fixtures

```python
# Mock responses with consistent session_ids
# Sample conversation flows
# Expected metadata structures
```

## Implementation

### File: `tests/integration/test_llm_sessions.py`

```python
"""Integration tests for LLM session management and serialization.

These tests validate end-to-end functionality including:
- Session continuity across multiple turns
- Serialization and deserialization
- Parallel session safety
- Cross-method compatibility (CLI and API)
"""

import pytest
import tempfile
from pathlib import Path

from mcp_coder import (
    prompt_llm,
    serialize_llm_response,
    deserialize_llm_response,
    LLMResponseDict,
)


@pytest.mark.integration
class TestSessionContinuity:
    """Test session continuity across multiple turns."""

    def test_session_continuity_cli(self, mock_claude_cli):
        """Test multi-turn conversation with CLI method."""
        # First turn
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Your favorite color is blue.",
            "session_id": "session-123",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        
        result1 = prompt_llm("My favorite color is blue", method="cli")
        session_id = result1["session_id"]
        
        # Second turn with same session
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:31:00",
            "text": "You told me your favorite color is blue.",
            "session_id": "session-123",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        
        result2 = prompt_llm("What's my favorite color?", method="cli", session_id=session_id)
        
        # Validate session continuity
        assert result2["session_id"] == session_id
        assert mock_claude_cli.received_session_id == session_id
        assert "blue" in result2["text"].lower()

    def test_session_continuity_api(self, mock_claude_api):
        """Test multi-turn conversation with API method."""
        # First turn
        mock_claude_api.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Your favorite color is red.",
            "session_id": "api-session-456",
            "method": "api",
            "provider": "claude",
            "raw_response": {}
        })
        
        result1 = prompt_llm("My favorite color is red", method="api")
        session_id = result1["session_id"]
        
        # Second turn
        mock_claude_api.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:31:00",
            "text": "You said your favorite color is red.",
            "session_id": "api-session-456",
            "method": "api",
            "provider": "claude",
            "raw_response": {}
        })
        
        result2 = prompt_llm("What's my color?", method="api", session_id=session_id)
        
        assert result2["session_id"] == session_id
        assert mock_claude_api.received_session_id == session_id

    def test_multi_turn_conversation(self, mock_claude_cli):
        """Test conversation with 3+ turns."""
        session_id = "multi-turn-session"
        
        # Turn 1
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Got it, your name is Alice.",
            "session_id": session_id,
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result1 = prompt_llm("My name is Alice", method="cli")
        
        # Turn 2
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:31:00",
            "text": "Your favorite color is green.",
            "session_id": session_id,
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result2 = prompt_llm("My favorite color is green", method="cli", session_id=session_id)
        
        # Turn 3
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:32:00",
            "text": "Your name is Alice and your favorite color is green.",
            "session_id": session_id,
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result3 = prompt_llm("What's my name and color?", method="cli", session_id=session_id)
        
        # All should have same session_id
        assert result1["session_id"] == session_id
        assert result2["session_id"] == session_id
        assert result3["session_id"] == session_id


@pytest.mark.integration
class TestSerialization:
    """Test serialization and deserialization workflows."""

    def test_serialization_roundtrip(self, mock_claude_cli, tmp_path):
        """Test save and load preserves all data."""
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Test response",
            "session_id": "serialize-test",
            "method": "cli",
            "provider": "claude",
            "raw_response": {
                "duration_ms": 2801,
                "cost_usd": 0.058,
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }
        })
        
        result = prompt_llm("Test question", method="cli")
        
        # Save to file
        filepath = tmp_path / "conversation.json"
        serialize_llm_response(result, filepath)
        
        # Load from file
        loaded = deserialize_llm_response(filepath)
        
        # Verify all data preserved
        assert loaded["text"] == result["text"]
        assert loaded["session_id"] == result["session_id"]
        assert loaded["version"] == result["version"]
        assert loaded["raw_response"]["duration_ms"] == 2801
        assert loaded["raw_response"]["cost_usd"] == 0.058

    def test_session_from_saved_file(self, mock_claude_cli, tmp_path):
        """Test resuming session from saved file."""
        # First conversation
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Conversation started",
            "session_id": "saved-session",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result1 = prompt_llm("Start conversation", method="cli")
        
        # Save session
        filepath = tmp_path / f"{result1['session_id']}.json"
        serialize_llm_response(result1, filepath)
        
        # Later: Load session_id and continue
        loaded = deserialize_llm_response(filepath)
        session_id = loaded["session_id"]
        
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:35:00",
            "text": "Continuing from saved session",
            "session_id": session_id,
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result2 = prompt_llm("Continue", method="cli", session_id=session_id)
        
        assert result2["session_id"] == session_id


@pytest.mark.integration
class TestParallelSafety:
    """Test that parallel sessions don't interfere."""

    def test_parallel_sessions_cli(self, mock_claude_cli):
        """Test two independent sessions running in parallel."""
        # Session 1: Color is blue
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Your color is blue",
            "session_id": "session-1",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result1a = prompt_llm("My color is blue", method="cli")
        session1_id = result1a["session_id"]
        
        # Session 2: Color is red
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Your color is red",
            "session_id": "session-2",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result2a = prompt_llm("My color is red", method="cli")
        session2_id = result2a["session_id"]
        
        # Sessions should have different IDs
        assert session1_id != session2_id
        
        # Continue session 1
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:31:00",
            "text": "You said blue",
            "session_id": "session-1",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result1b = prompt_llm("What was my color?", method="cli", session_id=session1_id)
        
        # Continue session 2
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:31:00",
            "text": "You said red",
            "session_id": "session-2",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        result2b = prompt_llm("What was my color?", method="cli", session_id=session2_id)
        
        # Each session maintains its own context
        assert result1b["session_id"] == session1_id
        assert result2b["session_id"] == session2_id
        assert "blue" in result1b["text"].lower()
        assert "red" in result2b["text"].lower()

    def test_parallel_sessions_different_methods(self, mock_claude_cli, mock_claude_api):
        """Test CLI and API sessions can run independently."""
        # CLI session
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "CLI session",
            "session_id": "cli-session",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        })
        cli_result = prompt_llm("CLI test", method="cli")
        
        # API session
        mock_claude_api.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "API session",
            "session_id": "api-session",
            "method": "api",
            "provider": "claude",
            "raw_response": {}
        })
        api_result = prompt_llm("API test", method="api")
        
        # Different sessions
        assert cli_result["session_id"] != api_result["session_id"]
        assert cli_result["method"] == "cli"
        assert api_result["method"] == "api"


@pytest.mark.integration
class TestMetadataTracking:
    """Test metadata preservation and cost tracking."""

    def test_metadata_preserved_through_workflow(self, mock_claude_cli, tmp_path):
        """Test that metadata is preserved through complete workflow."""
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Response with metadata",
            "session_id": "meta-session",
            "method": "cli",
            "provider": "claude",
            "raw_response": {
                "duration_ms": 2801,
                "cost_usd": 0.058,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0
                }
            }
        })
        
        # Get response
        result = prompt_llm("Test with metadata", method="cli")
        
        # Verify metadata present
        assert result["raw_response"]["duration_ms"] == 2801
        assert result["raw_response"]["cost_usd"] == 0.058
        assert result["raw_response"]["usage"]["input_tokens"] == 100
        
        # Save and load
        filepath = tmp_path / "metadata_test.json"
        serialize_llm_response(result, filepath)
        loaded = deserialize_llm_response(filepath)
        
        # Metadata still present after serialization
        assert loaded["raw_response"]["duration_ms"] == 2801
        assert loaded["raw_response"]["cost_usd"] == 0.058

    def test_cost_tracking_across_sessions(self, mock_claude_cli):
        """Test accumulating costs across conversation turns."""
        session_id = "cost-tracking"
        total_cost = 0.0
        
        # Turn 1
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Turn 1",
            "session_id": session_id,
            "method": "cli",
            "provider": "claude",
            "raw_response": {"cost_usd": 0.025}
        })
        result1 = prompt_llm("Question 1", method="cli")
        total_cost += result1["raw_response"].get("cost_usd", 0)
        
        # Turn 2
        mock_claude_cli.set_response_dict({
            "version": "1.0",
            "timestamp": "2025-10-01T10:31:00",
            "text": "Turn 2",
            "session_id": session_id,
            "method": "cli",
            "provider": "claude",
            "raw_response": {"cost_usd": 0.033}
        })
        result2 = prompt_llm("Question 2", method="cli", session_id=session_id)
        total_cost += result2["raw_response"].get("cost_usd", 0)
        
        # Can track total cost
        assert total_cost == pytest.approx(0.058)


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_session_id_handled(self, mock_claude_cli):
        """Test behavior with invalid session_id."""
        # Mock should handle gracefully or raise appropriate error
        mock_claude_cli.set_error_on_invalid_session(True)
        
        # Attempting to use non-existent session
        # Behavior depends on CLI/API implementation
        # Should either create new session or raise clear error
        try:
            result = prompt_llm("Test", method="cli", session_id="nonexistent-session")
            # If succeeds, should have a session_id (possibly new one)
            assert "session_id" in result
        except Exception as e:
            # If fails, error should be clear
            assert "session" in str(e).lower()

    def test_missing_fields_in_serialized_data(self, tmp_path):
        """Test handling of incomplete serialized data."""
        # Create file with minimal data
        filepath = tmp_path / "minimal.json"
        import json
        minimal_data = {
            "version": "1.0",
            "text": "Minimal response",
            # Missing other fields
        }
        with open(filepath, 'w') as f:
            json.dump(minimal_data, f)
        
        # Should load with best effort
        loaded = deserialize_llm_response(filepath)
        assert loaded["version"] == "1.0"
        assert loaded["text"] == "Minimal response"


@pytest.mark.integration
class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_ask_llm_still_works(self, mock_claude_cli):
        """Test that ask_llm (simple interface) still works."""
        from mcp_coder import ask_llm
        
        mock_claude_cli.set_response("Simple response")
        
        response = ask_llm("Simple question")
        
        # Should return string as before
        assert isinstance(response, str)
        assert response == "Simple response"

    def test_ask_llm_without_session_id(self, mock_claude_cli):
        """Test ask_llm works without session_id parameter."""
        from mcp_coder import ask_llm
        
        mock_claude_cli.set_response("No session needed")
        
        # Old calling pattern should still work
        response = ask_llm("Question", provider="claude", method="cli", timeout=30)
        
        assert response == "No session needed"


# Test fixtures for integration tests
@pytest.fixture
def mock_claude_cli():
    """Mock for Claude CLI that simulates real behavior."""
    # Implementation depends on existing test infrastructure
    # This is a placeholder - actual implementation in test file
    pass


@pytest.fixture
def mock_claude_api():
    """Mock for Claude API that simulates real behavior."""
    # Implementation depends on existing test infrastructure
    # This is a placeholder - actual implementation in test file
    pass
```

## Validation Checklist

- [ ] Integration test file created in `tests/integration/`
- [ ] Session continuity tests for CLI and API
- [ ] Multi-turn conversation tests
- [ ] Serialization round-trip tests
- [ ] Parallel session safety tests
- [ ] Cross-method compatibility tests
- [ ] Metadata preservation tests
- [ ] Cost tracking tests
- [ ] Error handling tests
- [ ] Backward compatibility tests
- [ ] All integration tests pass
- [ ] Test coverage ≥ 90% for new modules

## LLM Prompt

```
I am implementing Step 9 (final step) of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for complete architectural context
- pr_info/steps/decisions.md for architecture decisions
- All previous steps (1-8) for implementation details

For Step 9, I need to create tests/integration/test_llm_sessions.py:

Requirements from pr_info/steps/step_9.md:
1. Create comprehensive integration tests that validate:
   - Session continuity across multiple turns (CLI and API)
   - Serialization and deserialization workflows
   - Parallel session safety (sessions don't interfere)
   - Cross-method compatibility
   - Metadata preservation through workflows
   - Cost tracking across conversation turns
   - Error handling scenarios
   - Backward compatibility with existing code

2. Test classes to implement:
   - TestSessionContinuity: Multi-turn conversations
   - TestSerialization: Save/load workflows
   - TestParallelSafety: Independent sessions
   - TestMetadataTracking: Cost and usage data
   - TestErrorHandling: Edge cases
   - TestBackwardCompatibility: Existing code still works

3. Use mocked LLM responses that simulate real behavior
4. Validate complete end-to-end workflows
5. Ensure all tests are marked with @pytest.mark.integration

This is the final validation step before the feature is complete.

Please implement comprehensive integration tests with all tests passing.
```

## Dependencies
- **Requires**: All steps 1-8 complete (entire implementation)
- **Validates**: Complete feature functionality

## Success Criteria
1. ✅ Integration test file created
2. ✅ All test classes implemented
3. ✅ Session continuity validated for both methods
4. ✅ Multi-turn conversations work correctly
5. ✅ Serialization preserves all data
6. ✅ Parallel sessions don't interfere
7. ✅ Metadata tracked correctly
8. ✅ Error cases handled gracefully
9. ✅ Backward compatibility maintained
10. ✅ All integration tests pass
11. ✅ Test coverage ≥ 90% for new code
12. ✅ Manual testing confirms real-world usage

## Final Validation

After all tests pass, perform manual validation:

1. **Manual CLI Test**:
```bash
# Start conversation
result=$(python -c "from mcp_coder import prompt_llm; import json; r=prompt_llm('My color is blue'); print(json.dumps(r))")
session_id=$(echo $result | jq -r '.session_id')

# Continue conversation
python -c "from mcp_coder import prompt_llm; r=prompt_llm('What is my color?', session_id='$session_id'); print(r['text'])"
```

2. **Manual API Test**: Same as above with `method="api"`

3. **Serialization Test**:
```python
from mcp_coder import prompt_llm, serialize_llm_response, deserialize_llm_response

result = prompt_llm("Test")
serialize_llm_response(result, "test.json")
loaded = deserialize_llm_response("test.json")
assert loaded == result
```

4. **Verify Existing Code**: Run existing test suite to ensure no regressions
