"""Tests for tool output extraction in run_agent_stream()."""

from unittest.mock import MagicMock

from tests.llm.providers.langchain.test_langchain_agent_streaming import (
    _patch_run_agent_stream,
)


class TestRunAgentStreamToolOutput:
    """Tests for tool result output extraction in run_agent_stream()."""

    async def test_tool_result_from_on_tool_end(self) -> None:
        """on_tool_end events become tool_result StreamEvents."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-123"
        output_mock.content = "test result"
        # Remove artifact attr so cascade falls through to content string
        del output_mock.artifact
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "search_tool",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["name"] == "search_tool"
        assert tool_results[0]["tool_call_id"] == "tc-123"
        assert tool_results[0]["output"] == "test result"

    async def test_tool_result_structured_content(self) -> None:
        """artifact.structured_content is extracted as JSON string."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-1"
        output_mock.artifact = {"structured_content": {"result": True}}
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "save_file",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["output"] == '{"result": true}'

    async def test_tool_result_content_blocks(self) -> None:
        """Content list with text blocks is joined, non-text filtered out."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-2"
        output_mock.content = [
            {"type": "text", "text": "line1"},
            {"type": "image", "url": "http://example.com/img.png"},
            {"type": "text", "text": "line2"},
        ]
        del output_mock.artifact
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "read_file",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["output"] == "line1\nline2"

    async def test_tool_result_content_single_block(self) -> None:
        """Content list with single text block extracts correctly."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-3"
        output_mock.content = [{"type": "text", "text": "hello"}]
        del output_mock.artifact
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "search",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["output"] == "hello"

    async def test_tool_result_content_string(self) -> None:
        """Plain string content is used directly."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-4"
        output_mock.content = "plain text"
        del output_mock.artifact
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "tool",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["output"] == "plain text"

    async def test_tool_result_artifact_without_structured_content(self) -> None:
        """artifact without structured_content falls through to content."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-5"
        output_mock.artifact = {"other_key": "value"}
        output_mock.content = "fallback text"
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "tool",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["output"] == "fallback text"

    async def test_tool_result_fallback(self) -> None:
        """No artifact, no content — falls back to str(output)."""
        output_mock = MagicMock()
        output_mock.tool_call_id = "tc-6"
        del output_mock.artifact
        del output_mock.content
        events: list[dict[str, object]] = [
            {
                "event": "on_tool_end",
                "data": {"output": output_mock},
                "run_id": "run-1",
                "name": "tool",
            },
        ]
        with _patch_run_agent_stream(events):
            from mcp_coder.llm.providers.langchain.agent import run_agent_stream

            result = [
                e
                async for e in run_agent_stream(
                    question="Hi",
                    chat_model=MagicMock(),
                    messages=[],
                    mcp_config_path="/tmp/mcp.json",
                    session_id="s1",
                )
            ]
        tool_results = [e for e in result if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["output"] == str(output_mock)
