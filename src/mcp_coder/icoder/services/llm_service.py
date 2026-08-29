"""LLM service protocol and implementations for iCoder."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Protocol, runtime_checkable

from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway
from mcp_coder.icoder.permissions.model import PermissionFrame
from mcp_coder.llm.interface import prompt_llm_stream
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
        *,
        frame: PermissionFrame | None = None,
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
        *,
        project_dir: str | Path,
        gateway: LangchainEnforcementGateway | None = None,
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
        self._gateway = gateway

    def stream(
        self,
        question: str,
        *,
        frame: PermissionFrame | None = None,
    ) -> Iterator[StreamEvent]:
        """Call prompt_llm_stream() with stored config. Updates session_id from 'done' events.

        When a ``gateway`` is present, the already-built per-turn ``frame`` is
        installed via ``gateway.begin_turn`` and the manager's tool list is
        filtered against the resolver (``never`` tools hidden). Enforcement is
        config-driven; the frame is constructed upstream by ``AppCore`` from the
        skill-frame snapshot, so this method no longer builds frames or surfaces
        per-token warnings. Filtering operates on a copy, never mutating the
        manager's shared cache.

        Args:
            question: The user input to send to the LLM.
            frame: The per-turn permission frame installed via
                ``gateway.begin_turn``, or ``None`` for a config-only turn.

        Yields:
            StreamEvent dicts from the underlying LLM provider.
        """
        tools = None
        if self._mcp_manager is not None:
            tools = self._mcp_manager.tools()
            if self._gateway is not None:
                self._gateway.begin_turn(frame)
                tools = self._gateway.filter_tools(
                    tools, self._mcp_manager.canonical_name
                )
        for event in prompt_llm_stream(
            question,
            provider=self._provider,
            session_id=self._session_id,
            timeout=self._timeout,
            mcp_config=self._mcp_config,
            settings_file=self._settings_file,
            env_vars=self._env_vars,
            tools=tools,
            project_dir=self._project_dir,
            inject_prompts=True,
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
    ) -> None:
        """Initialize with optional canned response sequences.

        Each call to stream() pops the next response from the list.
        Default: single response with one text_delta + done event.
        """
        self._responses: list[list[StreamEvent]] = list(responses) if responses else []
        self._provider = provider
        self._session_id: str | None = None
        self.last_frame: PermissionFrame | None = None

    def stream(
        self,
        question: str,
        *,
        frame: PermissionFrame | None = None,
    ) -> Iterator[StreamEvent]:
        """Yield next canned response sequence, recording ``frame``."""
        self.last_frame = frame
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
