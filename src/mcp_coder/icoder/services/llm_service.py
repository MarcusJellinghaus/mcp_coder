"""LLM service protocol and implementations for iCoder."""

from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable

from mcp_coder.llm.interface import prompt_llm_stream
from mcp_coder.llm.types import StreamEvent


@runtime_checkable
class LLMService(Protocol):
    """Protocol for LLM interaction. Enables DI for testing."""

    def stream(self, question: str) -> Iterator[StreamEvent]:
        """Stream LLM response events for the given input."""

    @property
    def session_id(self) -> str | None:
        """Current session ID (updated after each stream completes)."""


class RealLLMService:
    """Production LLM service wrapping prompt_llm_stream()."""

    def __init__(
        self,
        provider: str = "claude",
        session_id: str | None = None,
        execution_dir: str | None = None,
        mcp_config: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None:
        self._provider = provider
        self._session_id = session_id
        self._execution_dir = execution_dir
        self._mcp_config = mcp_config
        self._env_vars = env_vars

    def stream(self, question: str) -> Iterator[StreamEvent]:
        """Call prompt_llm_stream() with stored config. Updates session_id from 'done' events.

        Yields:
            StreamEvent dicts from the underlying LLM provider.
        """
        for event in prompt_llm_stream(
            question,
            provider=self._provider,
            session_id=self._session_id,
            execution_dir=self._execution_dir,
            mcp_config=self._mcp_config,
            env_vars=self._env_vars,
        ):
            if event.get("type") == "done":
                sid = event.get("session_id")
                if isinstance(sid, str):
                    self._session_id = sid
            yield event

    @property
    def session_id(self) -> str | None:
        """Current session ID (updated after each stream completes)."""
        return self._session_id


class FakeLLMService:
    """Fake LLM for testing. Returns canned streaming responses."""

    def __init__(self, responses: list[list[StreamEvent]] | None = None) -> None:
        """Initialize with optional canned response sequences.

        Each call to stream() pops the next response from the list.
        Default: single response with one text_delta + done event.
        """
        self._responses: list[list[StreamEvent]] = list(responses) if responses else []
        self._session_id: str | None = None

    def stream(self, question: str) -> Iterator[StreamEvent]:
        """Yield next canned response sequence."""
        if self._responses:
            events = self._responses.pop(0)
        else:
            events = [
                {"type": "text_delta", "text": "fake response"},
                {"type": "done"},
            ]
        for event in events:
            if event.get("type") == "done":
                sid = event.get("session_id")
                if isinstance(sid, str):
                    self._session_id = sid
            yield event

    @property
    def session_id(self) -> str | None:
        """Current session ID (updated after each stream completes)."""
        return self._session_id
