"""Tests for AppCore — blocked skills, skill frames, and permission wiring."""

from __future__ import annotations

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.core.types import OutputText, SendToLLM
from mcp_coder.icoder.permissions.model import Matcher, PermissionFrame
from mcp_coder.icoder.permissions.skill_frame import SkillFrame
from mcp_coder.icoder.services.llm_service import FakeLLMService


def test_handle_input_blocked_command_returns_reason(app_core: AppCore) -> None:
    """Invoking a blocked command returns a single OutputText(reason)."""
    from mcp_coder.icoder.core.types import Command, Response

    app_core.registry.add_command(
        Command(
            name="/broken",
            description="broken skill",
            handler=lambda args: Response(actions=(SendToLLM(text="should not run"),)),
            disabled_reason="tools: block is malformed",
        )
    )
    response = app_core.handle_input("/broken do it")
    assert response.actions == (OutputText(text="tools: block is malformed"),)


def test_handle_input_blocked_command_no_send_to_llm(app_core: AppCore) -> None:
    """A blocked command dispatches no SendToLLM (never queries the LLM)."""
    from mcp_coder.icoder.core.types import Command, Response

    app_core.registry.add_command(
        Command(
            name="/broken",
            description="broken skill",
            handler=lambda args: Response(actions=(SendToLLM(text="should not run"),)),
            disabled_reason="broken",
        )
    )
    response = app_core.handle_input("/broken")
    assert not any(isinstance(a, SendToLLM) for a in response.actions)


def test_handle_input_blocked_command_emits_events(
    app_core: AppCore, event_log: EventLog
) -> None:
    """A blocked command logs command_matched AND output_emitted events."""
    from mcp_coder.icoder.core.types import Command, Response

    app_core.registry.add_command(
        Command(
            name="/broken",
            description="broken skill",
            handler=lambda args: Response(),
            disabled_reason="broken reason",
        )
    )
    app_core.handle_input("/broken now")
    events = event_log.entries
    assert any(e.event == "input_received" for e in events)
    matched = [e for e in events if e.event == "command_matched"]
    assert matched and matched[0].data.get("command") == "/broken"
    emitted = [e for e in events if e.event == "output_emitted"]
    assert emitted and emitted[0].data.get("text") == "broken reason"


def test_handle_input_non_blocked_command_unaffected(app_core: AppCore) -> None:
    """A command with disabled_reason=None dispatches normally."""
    from mcp_coder.icoder.core.types import Command, Response

    app_core.registry.add_command(
        Command(
            name="/ok",
            description="ok skill",
            handler=lambda args: Response(actions=(SendToLLM(text="run me"),)),
        )
    )
    response = app_core.handle_input("/ok")
    assert response.actions == (SendToLLM(text="run me"),)


def test_broken_skills_reflects_only_frames_with_blocked_reason(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """broken_skills lists only frames carrying a blocked_reason (#1061)."""
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={
            "ok": SkillFrame(frame=PermissionFrame(base="inherit")),
            "broken": SkillFrame(
                frame=PermissionFrame(base="none"), blocked_reason="bad tools block"
            ),
        },
    )
    assert core.broken_skills == {"broken": "bad tools block"}


def test_broken_skills_empty_when_all_runnable(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """broken_skills is empty when no frame carries a blocked_reason."""
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={"ok": SkillFrame(frame=PermissionFrame(base="inherit"))},
    )
    assert core.broken_skills == {}


def test_permission_degraded_echoes_constructor_flag(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """permission_degraded echoes the constructor flag (True and default False)."""
    degraded = AppCore(
        llm_service=fake_llm, event_log=event_log, permission_degraded=True
    )
    assert degraded.permission_degraded is True
    default = AppCore(llm_service=fake_llm, event_log=event_log)
    assert default.permission_degraded is False


def test_stream_llm_forwards_skill_frame_to_service(event_log: EventLog) -> None:
    """stream_llm looks up the skill frame and forwards it to the LLM service."""
    fake_llm = FakeLLMService()
    frame = PermissionFrame(base="inherit", allow=(Matcher("srv", "a"),))
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={"tooled": SkillFrame(frame=frame)},
    )
    list(core.stream_llm("hello", "tooled"))
    assert fake_llm.last_frame is frame


def test_stream_llm_default_skill_name_forwards_no_frame(event_log: EventLog) -> None:
    """stream_llm without a skill_name forwards frame=None to the service."""
    fake_llm = FakeLLMService()
    core = AppCore(llm_service=fake_llm, event_log=event_log)
    list(core.stream_llm("hello"))
    assert fake_llm.last_frame is None


def test_stream_llm_unknown_skill_forwards_no_frame(event_log: EventLog) -> None:
    """An unknown skill_name (not in the snapshot) forwards frame=None."""
    fake_llm = FakeLLMService()
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={"known": SkillFrame(frame=PermissionFrame(base="none"))},
    )
    list(core.stream_llm("hello", "unknown"))
    assert fake_llm.last_frame is None


def test_stream_llm_emits_skill_warnings_before_stream(event_log: EventLog) -> None:
    """sf.warnings are emitted as permission_warning events before the stream."""
    fake_llm = FakeLLMService(
        responses=[[{"type": "text_delta", "text": "hi"}, {"type": "done"}]]
    )
    frame = PermissionFrame(base="none")
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={
            "tooled": SkillFrame(frame=frame, warnings=("dropped mcp__srv__x",))
        },
    )
    events = list(core.stream_llm("hello", "tooled"))
    types = [e.get("type") for e in events]
    # Warning precedes the service stream.
    assert types[0] == "permission_warning"
    assert events[0]["message"] == "dropped mcp__srv__x"
    assert types.index("permission_warning") < types.index("text_delta")


def test_stream_llm_skill_frame_does_not_leak_into_next_turn(
    event_log: EventLog,
) -> None:
    """A skill frame is single-turn: the following plain turn runs frameless."""
    fake_llm = FakeLLMService(responses=[[{"type": "done"}], [{"type": "done"}]])
    frame = PermissionFrame(base="inherit", allow=(Matcher("srv", "a"),))
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={"tooled": SkillFrame(frame=frame)},
    )
    list(core.stream_llm("first", "tooled"))
    assert fake_llm.last_frame is frame
    list(core.stream_llm("second"))
    assert fake_llm.last_frame is None


def test_stream_llm_passes_permission_warning_through(event_log: EventLog) -> None:
    """A synthetic permission_warning event passes cleanly and is logged.

    The unknown event type is tolerated by ResponseAssembler.add (no error)
    and is forwarded to the event log as a stream_event.
    """
    fake_llm = FakeLLMService(
        responses=[
            [
                {"type": "permission_warning", "message": "dropped mcp__srv__*"},
                {"type": "text_delta", "text": "hi"},
                {"type": "done"},
            ]
        ]
    )
    core = AppCore(llm_service=fake_llm, event_log=event_log)
    events = list(core.stream_llm("hello"))

    # Event survived the stream unchanged.
    assert {"type": "permission_warning", "message": "dropped mcp__srv__*"} in events

    # And it reached the event log as a stream_event.
    stream_entries = [e for e in event_log.entries if e.event == "stream_event"]
    logged_types = [e.data.get("type") for e in stream_entries]
    assert "permission_warning" in logged_types
