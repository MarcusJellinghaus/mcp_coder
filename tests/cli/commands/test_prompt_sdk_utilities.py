"""Tests for prompt command SDK utility functions.

These tests focus on our own utility functions that provide unified access to
both dictionary and SDK object message formats. They test our code's behavior
with controlled inputs rather than relying on external SDK behavior.
"""

from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.prompt import (
    _extract_tool_interactions,
    _get_message_role,
    _get_message_tool_calls,
    _is_sdk_message,
    _serialize_message_for_json,
)


class TestMessageRoleExtraction:
    """Test _get_message_role utility function."""

    def test_dictionary_role_extraction(self) -> None:
        """Test role extraction from dictionary messages."""
        user_message = {"role": "user", "content": "Hello"}
        assert _get_message_role(user_message) == "user"

        assistant_message = {"role": "assistant", "content": "Hi there"}
        assert _get_message_role(assistant_message) == "assistant"

        system_message = {"role": "system", "content": "You are helpful"}
        assert _get_message_role(system_message) == "system"

    def test_dictionary_missing_role(self) -> None:
        """Test handling of dictionaries without role key."""
        message_no_role = {"content": "No role specified"}
        assert _get_message_role(message_no_role) is None

    def test_dictionary_none_role(self) -> None:
        """Test handling of dictionaries with None role."""
        message_none_role = {"role": None, "content": "Role is None"}
        assert _get_message_role(message_none_role) is None

    def test_none_values(self) -> None:
        """Test that None values return None role."""
        assert _get_message_role(None) is None

    def test_empty_dictionary(self) -> None:
        """Test handling of empty dictionaries."""
        assert _get_message_role({}) is None

    def test_non_dictionary_object(self) -> None:
        """Test handling of non-dictionary objects without SDK type."""

        class MockObject:
            def __init__(self) -> None:
                self.role = "custom_role"

        mock_obj = MockObject()
        assert _get_message_role(mock_obj) is None

    def test_string_input(self) -> None:
        """Test handling of string input."""
        assert _get_message_role("not a message") is None


class TestToolCallExtraction:
    """Test _get_message_tool_calls utility function."""

    def test_dictionary_tool_calls(self) -> None:
        """Test tool call extraction from dictionary messages."""
        message_with_tools = {
            "role": "assistant",
            "tool_calls": [
                {"name": "file_reader", "parameters": {"path": "/test/file.py"}},
                {"name": "calculator", "parameters": {"expression": "2+2"}},
            ],
        }
        tool_calls = _get_message_tool_calls(message_with_tools)
        assert len(tool_calls) == 2
        assert tool_calls[0]["name"] == "file_reader"
        assert tool_calls[0]["parameters"]["path"] == "/test/file.py"
        assert tool_calls[1]["name"] == "calculator"

    def test_dictionary_no_tool_calls(self) -> None:
        """Test handling of dictionaries without tool_calls key."""
        message_no_tools = {"role": "assistant", "content": "No tools used"}
        assert _get_message_tool_calls(message_no_tools) == []

    def test_dictionary_empty_tool_calls(self) -> None:
        """Test handling of dictionaries with empty tool_calls."""
        message_empty_tools = {"role": "assistant", "tool_calls": []}
        assert _get_message_tool_calls(message_empty_tools) == []

    def test_dictionary_invalid_tool_calls(self) -> None:
        """Test handling of dictionaries with invalid tool_calls value."""
        message_invalid_tools = {"role": "assistant", "tool_calls": "not a list"}
        assert _get_message_tool_calls(message_invalid_tools) == []

    def test_none_values(self) -> None:
        """Test that None values return empty list."""
        assert _get_message_tool_calls(None) == []

    def test_non_dictionary_object(self) -> None:
        """Test handling of non-dictionary, non-SDK objects."""

        class MockObject:
            def __init__(self) -> None:
                self.tool_calls = [{"name": "test_tool"}]

        mock_obj = MockObject()
        assert _get_message_tool_calls(mock_obj) == []


class TestSDKMessageDetection:
    """Test _is_sdk_message utility function."""

    def test_sdk_message_detection_basic(self) -> None:
        """Test that isinstance() logic works with SDK objects using mock classes."""

        # Create mock classes that can be used with isinstance()
        class MockSystemMessage:
            pass

        class MockAssistantMessage:
            pass

        class MockResultMessage:
            pass

        # Mock the SDK classes in the prompt module
        with (
            patch("mcp_coder.cli.commands.prompt.SystemMessage", MockSystemMessage),
            patch(
                "mcp_coder.cli.commands.prompt.AssistantMessage", MockAssistantMessage
            ),
            patch("mcp_coder.cli.commands.prompt.ResultMessage", MockResultMessage),
        ):

            # Create instances of mock classes
            mock_system_instance = MockSystemMessage()
            mock_assistant_instance = MockAssistantMessage()
            mock_result_instance = MockResultMessage()

            # Test our core isinstance() logic with each type
            assert _is_sdk_message(mock_system_instance) is True
            assert _is_sdk_message(mock_assistant_instance) is True
            assert _is_sdk_message(mock_result_instance) is True

            # Test that non-SDK objects return False
            assert _is_sdk_message({"role": "user"}) is False
            assert _is_sdk_message(None) is False

    def test_none_values(self) -> None:
        """Test that None values are handled gracefully."""
        assert _is_sdk_message(None) is False

    def test_dictionary_detection(self) -> None:
        """Test that dictionaries are correctly identified as non-SDK."""
        test_dict = {"role": "user", "content": "test message"}
        assert _is_sdk_message(test_dict) is False

    def test_empty_dictionary_detection(self) -> None:
        """Test that empty dictionaries are correctly identified as non-SDK."""
        assert _is_sdk_message({}) is False

    def test_string_detection(self) -> None:
        """Test that strings are correctly identified as non-SDK."""
        assert _is_sdk_message("not a message object") is False

    def test_list_detection(self) -> None:
        """Test that lists are correctly identified as non-SDK."""
        assert _is_sdk_message([1, 2, 3]) is False

    def test_custom_object_detection(self) -> None:
        """Test that custom objects are correctly identified as non-SDK."""

        class CustomObject:
            def __init__(self) -> None:
                self.some_attr = "value"

        custom_obj = CustomObject()
        assert _is_sdk_message(custom_obj) is False

    @pytest.mark.claude_api_integration
    def test_real_sdk_objects_if_available(self) -> None:
        """Test with real SDK objects when SDK is available."""
        try:
            from mcp_coder.llm_providers.claude.claude_code_api import (
                SystemMessage,
                TextBlock,
            )

            # Test with real SDK objects
            system_msg = SystemMessage(subtype="test", data={})
            assert _is_sdk_message(system_msg) is True
            assert _get_message_role(system_msg) == "system"

            # Test graceful handling
            assert _get_message_tool_calls(system_msg) == []

            # Test TextBlock creation (basic SDK object validation)
            text_block = TextBlock(text="Hello, world!")
            assert hasattr(text_block, "text")
            assert text_block.text == "Hello, world!"

        except ImportError:
            pytest.skip("SDK not available for integration testing")


class TestJSONSerialization:
    """Test _serialize_message_for_json utility function."""

    def test_none_values(self) -> None:
        """Test that None values are preserved."""
        assert _serialize_message_for_json(None) is None

    def test_basic_json_serializable_objects(self) -> None:
        """Test that basic JSON-serializable objects are unchanged."""
        assert _serialize_message_for_json("string") == "string"
        assert _serialize_message_for_json(42) == 42
        assert _serialize_message_for_json([1, 2, 3]) == [1, 2, 3]
        assert _serialize_message_for_json({"key": "value"}) == {"key": "value"}

    def test_unknown_object_fallback(self) -> None:
        """Test fallback behavior for unknown object types."""

        class UnknownObject:
            def __init__(self) -> None:
                self.some_attr = "value"

        unknown_obj = UnknownObject()
        result = _serialize_message_for_json(unknown_obj)
        # Should return the object unchanged for json.dumps to handle
        assert result == unknown_obj


class TestToolInteractionExtraction:
    """Test _extract_tool_interactions utility function."""

    def test_empty_message_list(self) -> None:
        """Test that empty message lists return empty interactions."""
        assert _extract_tool_interactions([]) == []

    def test_dictionary_messages_with_tools(self) -> None:
        """Test extraction from dictionary messages with tools."""
        messages = [
            {"role": "user", "content": "Read a file"},
            {
                "role": "assistant",
                "content": "I'll read the file for you",
                "tool_calls": [
                    {"name": "file_reader", "parameters": {"path": "/test/file.py"}},
                    {"name": "calculator", "parameters": {"expression": "2+2"}},
                ],
            },
        ]
        result = _extract_tool_interactions(messages)
        assert len(result) == 2
        assert "file_reader: {'path': '/test/file.py'}" in result[0]
        assert "calculator: {'expression': '2+2'}" in result[1]

    def test_mixed_message_types(self) -> None:
        """Test extraction from mixed message types."""
        messages = [
            {"role": "user", "content": "Hello"},
            None,  # None message
            {"role": "assistant", "tool_calls": []},  # Empty tool calls
            {
                "role": "assistant",
                "tool_calls": [{"name": "test_tool", "parameters": {"arg": "value"}}],
            },
        ]
        result = _extract_tool_interactions(messages)
        assert len(result) == 1
        assert "test_tool: {'arg': 'value'}" in result[0]
