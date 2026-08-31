"""AppCore — central input router for iCoder. No Textual dependency.

Security boundary (issue #1040, design #1037 §3): this module holds the
ONLY production ``registry.dispatch`` call site (in ``handle_input``). Model
output flows through a separate, one-directional render path
(``stream_llm`` -> ``ICoderApp._handle_stream_event`` -> ``OutputLog``) that
never re-parses text as a command, so a model-emitted ``/skill`` can never
route into a skill's tool context. Any future model-driven command feature
must consciously preserve this gate. Full threat model: I5.6 / #1056.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Literal

from mcp_coder.icoder.core.colors import DEFAULT_PROMPT_COLOR, validate_color
from mcp_coder.icoder.core.command_history import CommandHistory
from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.event_log import (
    EventLog,
    emit_session_start,
    read_session_id_from_log,
)
from mcp_coder.icoder.core.types import (
    Action,
    OutputText,
    ResetSession,
    Response,
    SendToLLM,
    TokenUsage,
)
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.permissions.model import Rule
from mcp_coder.icoder.permissions.skill_frame import SkillFrame
from mcp_coder.icoder.services.llm_service import LLMService
from mcp_coder.llm.storage import store_session
from mcp_coder.llm.types import (
    TRANSIENT_EVENT_TYPES,
    ResponseAssembler,
    StreamEvent,
)

if TYPE_CHECKING:
    # Typing-only on purpose, matching ``services/llm_service.py`` and
    # ``llm/interface.py``: the gateway imports the langchain provider's
    # ``permission_bridge``, so a runtime import here would put that submodule
    # on the runtime path of every importer of ``AppCore`` — the widest import
    # reach of the three. ``llm_service`` guards its own copy for the same
    # reason; both are needed, since ``AppCore`` imports that module eagerly.
    from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway


class AppCore:
    """Central input router. No Textual dependency."""

    def __init__(
        self,
        llm_service: LLMService,
        event_log: EventLog,
        registry: CommandRegistry | None = None,
        runtime_info: RuntimeInfo | None = None,
        tool_display: Literal["oneline", "compressed"] = "compressed",
        skill_frames: Mapping[str, SkillFrame] | None = None,
        permission_degraded: bool = False,
        approval_engine: ApprovalEngine | None = None,
        permission_gateway: LangchainEnforcementGateway | None = None,
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            llm_service: LLM service for non-command input
            event_log: Structured event log
            registry: Command registry (default: create_default_registry())
            runtime_info: Optional runtime environment info from env_setup
            tool_display: Initial global tool-display tier (default
                ``"compressed"``). Set by the ``--tool-display`` CLI flag.
            skill_frames: Startup snapshot mapping each skill name to its
                pre-built :class:`SkillFrame`, looked up per turn by
                ``stream_llm`` (design §8.1). Empty/``None`` means no skills.
            permission_degraded: Whether the loaded permission config is
                degraded (fail-closed — every MCP call is denied). Surfaced as a
                loud startup line by the UI (#1061). Defaults to ``False``.
            approval_engine: The runtime approval engine shared with the
                gateway and the LLM service (langchain only), or ``None``.
                Reached by the UI only through the three delegating methods
                below, so the Textual layer never holds the engine itself.
            permission_gateway: The enforcement gateway owning the runtime rule
                layer (langchain only), or ``None``.
        """
        self._llm_service = llm_service
        self._event_log = event_log
        self._registry = registry if registry is not None else create_default_registry()
        self._runtime_info = runtime_info
        self._token_usage = TokenUsage()
        self._command_history = CommandHistory()
        self._prompt_color: str = DEFAULT_PROMPT_COLOR
        self._tool_display: Literal["oneline", "compressed"] = tool_display
        self._skill_frames: dict[str, SkillFrame] = dict(skill_frames or {})
        self._permission_degraded = permission_degraded
        self._approval_engine = approval_engine
        self._permission_gateway = permission_gateway

    # -- approval delegators (the UI's only route to engine and gateway) -----

    def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None:
        """Answer one pending approval. No-op without an engine.

        Args:
            approval_id: The id carried by the ``approval_request`` event.
            decision: The answer to apply.
        """
        if self._approval_engine is not None:
            self._approval_engine.resolve_pending(approval_id, decision)

    def cancel_pending_approvals(self) -> None:
        """Abort every pending approval. No-op without an engine.

        The direct UI -> engine cancel channel: an interceptor parked on an
        approval emits no event, so the generic cancel paths cannot reach it.
        """
        if self._approval_engine is not None:
            self._approval_engine.cancel_all()

    def add_runtime_rule(self, rule: Rule) -> None:
        """Append a rule to the gateway's runtime layer. No-op without a gateway.

        Called on the UI thread by the approval modal (I3.3) when a user grants
        a durable scope; the engine never writes the layer itself.

        Args:
            rule: The runtime-layer rule to append.
        """
        if self._permission_gateway is not None:
            self._permission_gateway.add_runtime_rule(rule)

    def handle_input(self, text: str) -> Response:
        """Route user input to commands or typed actions for the UI.

        - Slash commands: dispatch via registry, perform state-mutating
          side effects (output_emitted events, session reset), and return
          the command's typed-action Response.
        - Empty input: ignore (return empty ``Response()``).
        - Other text: return ``Response(actions=(SendToLLM(text=text),))``
          so the UI can start streaming.

        All state-mutation side effects (event-log rotation, session reset,
        output_emitted emission) happen here, BEFORE returning; the UI then
        iterates ``response.actions`` in tuple order. ``SendToLLM`` actions
        are resolved here so an empty ``text`` (skill passthrough) becomes
        the original user input.

        Always emits "input_received" event for non-empty input.

        Returns:
            Response whose ``actions`` the UI dispatches in order.
        """
        text = text.strip()
        if not text:
            return Response()

        self._event_log.emit("input_received", text=text)

        # Blocked-skill refusal (#1061): a command whose declaration is broken
        # is registered + visible but must refuse to run rather than burn an
        # LLM turn. Guard BEFORE dispatch — no handler, no SendToLLM. Emit
        # command_matched too so its event log matches every other command's.
        lead = text.split()[0].lower()
        blocked = self._registry.get(lead)
        if blocked is not None and blocked.disabled_reason:
            self._event_log.emit("command_matched", command=lead)
            self._event_log.emit("output_emitted", text=blocked.disabled_reason)
            return Response(actions=(OutputText(blocked.disabled_reason),))

        # SECURITY BOUNDARY (#1040): the ONLY production dispatch call site.
        # Reached only via on_input_area_input_submitted (human Enter keypress).
        # Model/stream output must never be routed here. A second call site
        # breaks tests/icoder/test_self_invocation_guard.py by design.
        response = self._registry.dispatch(text)
        if response is not None:
            self._event_log.emit("command_matched", command=text.split()[0].lower())
            resolved: list[Action] = []
            for action in response.actions:
                if isinstance(action, OutputText):
                    self._event_log.emit("output_emitted", text=action.text)
                    resolved.append(action)
                elif isinstance(action, ResetSession):
                    self._reset_session()
                    resolved.append(action)
                elif isinstance(action, SendToLLM):
                    resolved.append(replace(action, text=action.text or text))
                else:
                    resolved.append(action)
            return Response(actions=tuple(resolved))

        # Not a command → send to LLM
        return Response(actions=(SendToLLM(text=text),))

    def _reset_session(self) -> None:
        """Reset the LLM session and rotate the event log.

        The rotated log starts empty — emit a fresh session_start so the
        post-/clear file remains self-contained and visible to the startup
        picker (which filters on provider).
        """
        self._llm_service.reset_session()
        self._event_log.rotate()
        emit_session_start(
            self._event_log,
            provider=self._llm_service.provider,
            runtime_info=self._runtime_info,
            session_id=self._llm_service.session_id,
        )

    def stream_llm(
        self, text: str, skill_name: str | None = None
    ) -> Iterator[StreamEvent]:
        """Stream LLM response and auto-store for session continuation.

        Called by the UI layer when dispatching a ``SendToLLM`` action.
        Emits events for each stream phase. After streaming completes,
        stores the response so ``--continue-session`` can find it.

        Looks up the pre-built :class:`SkillFrame` for ``skill_name`` in the
        startup snapshot (``None`` for a plain message or an unknown skill),
        prepends its ``warnings`` as ``permission_warning`` events in front of
        the service stream, and forwards ``sf.frame`` to the service. Frames
        are single-turn: the next message runs frameless.

        Args:
            text: User input to send to the LLM.
            skill_name: Provenance of a skill-initiated turn (from
                ``SendToLLM.skill_name``), used to look up the per-turn frame,
                or ``None`` for a plain message.

        Yields:
            StreamEvent dicts for UI to render.
        """
        assembler = ResponseAssembler(self._llm_service.provider)
        sf = self._skill_frames.get(skill_name) if skill_name is not None else None
        self._event_log.emit("llm_request_start", text=text)

        def _events() -> Iterator[StreamEvent]:
            # Route warnings through the SAME assembler + event-log path as
            # service events so they are logged/replayed like any other event.
            for warning in sf.warnings if sf else ():
                yield {"type": "permission_warning", "message": warning}
            yield from self._llm_service.stream(text, frame=sf.frame if sf else None)

        for event in _events():
            assembler.add(event)
            if event.get("type") not in TRANSIENT_EVENT_TYPES:
                self._event_log.emit("stream_event", **event)
            if event.get("type") == "done":
                usage = event.get("usage", {})
                if isinstance(usage, dict):
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    if (
                        isinstance(input_tokens, int)
                        and isinstance(output_tokens, int)
                        and isinstance(cache_read, int)
                    ):
                        self._token_usage.update(
                            input_tokens, output_tokens, cache_read
                        )
            yield event

        # R16 — a hard cancel unwinds the provider generator without a ``done``
        # event, so this tail still runs and would record the aborted turn.
        # BOTH statements are skipped, not just the store: ``ui/replay.py``
        # clears ``in_flight`` on ``llm_request_end`` and appends the
        # "— Cancelled —" marker only while ``in_flight`` is still true at EOF,
        # so gating the store alone would make this the one cancel that replays
        # without a marker.
        #
        # The gate is ``turn_aborted``, NOT ``cancelled``: the latter is raised
        # by every ``cancel_all()``, including the one ``on_unmount`` fires on
        # app shutdown. A turn that finishes normally while the user is quitting
        # was never unwound and must still be recorded. ``turn_aborted`` is
        # reset by the next ``attach()`` — never by ``detach()``, which already
        # ran inside the provider's ``finally`` before this line is reached.
        if self._approval_engine is not None and self._approval_engine.turn_aborted:
            return

        self._event_log.emit("llm_request_end")

        # Auto-store response for --continue-session
        response_data = assembler.result()
        store_session(
            response_data, text, log_file_path=str(self._event_log.current_path)
        )

    @property
    def command_history(self) -> CommandHistory:
        """Command history for Up/Down recall. Survives /clear."""
        return self._command_history

    @property
    def registry(self) -> CommandRegistry:
        """Public read-only access to the command registry."""
        return self._registry

    @property
    def event_log(self) -> EventLog:
        """Public read-only access to the event log."""
        return self._event_log

    @property
    def runtime_info(self) -> RuntimeInfo | None:
        """Runtime environment info, if provided."""
        return self._runtime_info

    @property
    def broken_skills(self) -> dict[str, str]:
        """Skills that refuse to run, as ``{name: blocked_reason}`` (#1061).

        Derived from the startup :class:`SkillFrame` snapshot: a frame with a
        non-``None`` ``blocked_reason`` is a skill the user can see but cannot
        run. Rendered at startup and matching the invocation-refusal reason.

        Returns:
            A ``{skill_name: reason}`` map, empty when every skill is runnable.
        """
        return {
            name: sf.blocked_reason
            for name, sf in self._skill_frames.items()
            if sf.blocked_reason
        }

    @property
    def permission_degraded(self) -> bool:
        """Whether the loaded permission config is degraded (fail-closed)."""
        return self._permission_degraded

    @property
    def token_usage(self) -> TokenUsage:
        """Cumulative token usage for this session."""
        return self._token_usage

    @property
    def prompt_color(self) -> str:
        """Current prompt border color as hex string. Always concrete, never None."""
        return self._prompt_color

    def set_prompt_color(self, value: str) -> str | None:
        """Validate and set prompt border color. Delegates to validate_color().

        Returns:
            Error message string on failure, None on success.
        """
        hex_color, error = validate_color(value)
        if error:
            return error
        self._prompt_color = hex_color  # type: ignore[assignment]
        return None

    @property
    def tool_display(self) -> str:
        """Current global tool-display tier ("oneline" or "compressed")."""
        return self._tool_display

    def set_tool_display(self, value: Literal["oneline", "compressed"]) -> None:
        """Set the global tool-display tier and emit a change event.

        Args:
            value: The new global tier ("oneline" or "compressed").
        """
        self._tool_display = value
        self._event_log.emit("display_mode_changed", to=value)

    @property
    def session_id(self) -> str | None:
        """Current session ID from LLM service."""
        return self._llm_service.session_id

    @property
    def provider(self) -> str:
        """Current LLM provider name from the LLM service."""
        return self._llm_service.provider

    def prepare_for_resume(self, log_path: Path) -> str | None:
        """Resolve a session_id from a prior log and rotate the event log.

        Delegates id resolution to ``read_session_id_from_log``; the
        resolved id (or ``None``) is set on the LLM service. The event
        log is rotated so the new conversation gets its own JSONL file,
        and a fresh ``session_start`` (with the current provider /
        runtime_info / session_id) is emitted so the resumed-from log
        is self-contained and visible to future pickers.

        Returns:
            The resolved session_id string, or ``None`` if no candidate
            was found in the log.
        """
        session_id = read_session_id_from_log(log_path)
        self._llm_service.set_session_id(session_id)
        self._event_log.rotate()
        emit_session_start(
            self._event_log,
            provider=self._llm_service.provider,
            runtime_info=self._runtime_info,
            session_id=self._llm_service.session_id,
        )
        return session_id
