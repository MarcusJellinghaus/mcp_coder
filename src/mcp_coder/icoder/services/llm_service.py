"""LLM service protocol and implementations for iCoder."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Protocol, runtime_checkable

from mcp_coder.llm.interface import prompt_llm_stream
from mcp_coder.llm.providers.langchain.mcp_manager import (
    filter_tools_by_declaration,
)
from mcp_coder.llm.types import StreamEvent

if TYPE_CHECKING:
    from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager

ICODER_LLM_TIMEOUT_SECONDS = 300  # 5-minute inactivity timeout for interactive use


@runtime_checkable
class LLMService(Protocol):
    """Protocol for LLM interaction. Enables DI for testing."""

    def stream(
        self,
        question: str,
        allowed_tools: tuple[str, ...] | None = None,
    ) -> Iterator[StreamEvent]:
        """Stream LLM response events for the given input."""

    def reset_session(self) -> None:
        """Reset session state to start a new conversation."""

    def set_session_id(self, session_id: str | None) -> None:
        """Replace the current session_id. None = fresh conversation."""

    @property
    def provider(self) -> str:
        """LLM provider name (e.g. 'claude', 'langchain')."""

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
        settings_file: str | None = None,
        env_vars: dict[str, str] | None = None,
        timeout: int = ICODER_LLM_TIMEOUT_SECONDS,
        mcp_manager: MCPManager | None = None,
        project_dir: str | None = None,
        enforce_skill_tools: bool = False,
    ) -> None:
        self._provider = provider
        self._session_id = session_id
        self._execution_dir = execution_dir
        self._mcp_config = mcp_config
        self._settings_file = settings_file
        self._env_vars = env_vars
        self._timeout = timeout
        self._mcp_manager = mcp_manager
        self._project_dir = project_dir
        self._enforce_skill_tools = enforce_skill_tools

    def stream(
        self,
        question: str,
        allowed_tools: tuple[str, ...] | None = None,
    ) -> Iterator[StreamEvent]:
        """Call prompt_llm_stream() with stored config. Updates session_id from 'done' events.

        When ``enforce_skill_tools`` is set and ``allowed_tools`` is present,
        the tool list is narrowed host-side to the declared MCP tokens before
        reaching the injection seam. Filtering operates on a copy, never
        mutating the manager's shared cache.

        Args:
            question: The user input to send to the LLM.
            allowed_tools: Declared MCP tool tokens for this turn, or None.

        Yields:
            StreamEvent dicts from the underlying LLM provider. When
            enforcement drops un-parseable tokens, a synthetic
            ``permission_warning`` event is yielded before the agent stream.
        """
        tools = None
        if self._mcp_manager is not None:
            tools = self._mcp_manager.tools()
            if self._enforce_skill_tools and allowed_tools:
                filtered, warnings = filter_tools_by_declaration(
                    list(tools),
                    self._mcp_manager.canonical_name,
                    allowed_tools,
                )
                tools = filtered
                for warning in warnings:
                    yield {"type": "permission_warning", "message": warning}
        for event in prompt_llm_stream(
            question,
            provider=self._provider,
            session_id=self._session_id,
            timeout=self._timeout,
            execution_dir=self._execution_dir,
            mcp_config=self._mcp_config,
            settings_file=self._settings_file,
            env_vars=self._env_vars,
            tools=tools,
            project_dir=self._project_dir,
        ):
            if event.get("type") == "done":
                sid = event.get("session_id")
                if isinstance(sid, str):
                    self._session_id = sid
            yield event

    def reset_session(self) -> None:
        """Reset session state to start a new conversation."""
        self._session_id = None

    def set_session_id(self, session_id: str | None) -> None:
        """Replace the current session_id. None = fresh conversation."""
        self._session_id = session_id

    @property
    def provider(self) -> str:
        """LLM provider name."""
        return self._provider

    @property
    def session_id(self) -> str | None:
        """Current session ID (updated after each stream completes)."""
        return self._session_id


class FakeLLMService:
    """Fake LLM for testing. Returns canned streaming responses."""

    def __init__(
        self,
        responses: list[list[StreamEvent]] | None = None,
        provider: str = "claude",
        enforce_skill_tools: bool = False,
    ) -> None:
        """Initialize with optional canned response sequences.

        Each call to stream() pops the next response from the list.
        Default: single response with one text_delta + done event.

        ``enforce_skill_tools`` exists for signature parity with
        ``RealLLMService`` and is a no-op here.
        """
        self._responses: list[list[StreamEvent]] = list(responses) if responses else []
        self._provider = provider
        self._enforce_skill_tools = enforce_skill_tools
        self._session_id: str | None = None
        self.last_allowed_tools: tuple[str, ...] | None = None

    def stream(
        self,
        question: str,
        allowed_tools: tuple[str, ...] | None = None,
    ) -> Iterator[StreamEvent]:
        """Yield next canned response sequence, recording ``allowed_tools``."""
        self.last_allowed_tools = allowed_tools
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

    def reset_session(self) -> None:
        """Reset session state to start a new conversation."""
        self._session_id = None

    def set_session_id(self, session_id: str | None) -> None:
        """Replace the current session_id. None = fresh conversation."""
        self._session_id = session_id

    @property
    def provider(self) -> str:
        """LLM provider name."""
        return self._provider

    @property
    def session_id(self) -> str | None:
        """Current session ID (updated after each stream completes)."""
        return self._session_id
