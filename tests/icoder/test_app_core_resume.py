"""Tests for AppCore.prepare_for_resume and post-resume/clear log rotation.

Split out of ``test_app_core.py`` to keep each module under the file-size
limit. Fixtures (``fake_llm``, ``event_log``, ``app_core``) come from the
package ``conftest.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.services.llm_service import FakeLLMService


def _write_log(path: Path, events: list[dict[str, object]]) -> None:
    """Write a JSONL log file containing the given event dicts."""
    lines = [json.dumps(ev) for ev in events]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def test_prepare_for_resume_reads_session_id_from_session_start(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """session_start.session_id is read and set on the LLM service."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "session_id": "abc"},
            {"t": 0.1, "event": "input_received", "text": "hello"},
        ],
    )
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        initial_path = live_log.current_path
        result = core.prepare_for_resume(log_path)
        assert result == "abc"
        assert fake_llm.session_id == "abc"
        # Event log was rotated → new current_path
        assert live_log.current_path != initial_path


def test_prepare_for_resume_falls_back_to_done_event(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """Without session_start.session_id, last stream_event{type=done} is used."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hi"},
            {
                "t": 0.2,
                "event": "stream_event",
                "type": "done",
                "session_id": "xyz",
            },
        ],
    )
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        result = core.prepare_for_resume(log_path)
        assert result == "xyz"
        assert fake_llm.session_id == "xyz"


def test_prepare_for_resume_uses_last_done_session_id(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """Multiple done events → most recent session_id wins."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "stream_event", "type": "done", "session_id": "old"},
            {"t": 0.2, "event": "stream_event", "type": "done", "session_id": "new"},
        ],
    )
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        result = core.prepare_for_resume(log_path)
        assert result == "new"
        assert fake_llm.session_id == "new"


def test_prepare_for_resume_returns_none_when_no_session_id(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """No session_start.session_id and no done.session_id → None."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hi"},
        ],
    )
    fake_llm.set_session_id("preexisting")
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        result = core.prepare_for_resume(log_path)
        assert result is None
        assert fake_llm.session_id is None


def test_prepare_for_resume_rotates_event_log(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """The event log is rotated regardless of session_id presence."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [{"t": 0.0, "event": "session_start", "provider": "claude"}],
    )
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        initial_path = live_log.current_path
        core.prepare_for_resume(log_path)
        assert live_log.current_path != initial_path


def test_provider_property(app_core: AppCore) -> None:
    """AppCore.provider exposes the underlying LLM service provider."""
    assert app_core.provider == "claude"


# --- self-contained-rotated-log tests (Decisions #4 + #29) ---


def test_prepare_for_resume_emits_session_start_in_new_log(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """The post-resume rotated log starts with session_start{provider}."""
    src_log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        src_log_path,
        [{"t": 0.0, "event": "session_start", "provider": "claude"}],
    )
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        core.prepare_for_resume(src_log_path)
        rotated_path = live_log.current_path

    from mcp_coder.icoder.core.event_log import iter_events

    events = list(iter_events(rotated_path))
    assert len(events) >= 1
    assert events[0]["event"] == "session_start"
    assert events[0]["provider"] == "claude"


def test_prepare_for_resume_log_visible_to_picker(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """list_icoder_logs (provider-filtered) includes the post-resume log."""
    src_log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        src_log_path,
        [{"t": 0.0, "event": "session_start", "provider": "claude"}],
    )
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        core.prepare_for_resume(src_log_path)
        rotated_path = live_log.current_path

    from mcp_coder.icoder.core.log_inventory import list_icoder_logs

    summaries = list_icoder_logs(tmp_path, provider="claude")
    paths = [s.path for s in summaries]
    assert rotated_path in paths


def test_clear_emits_session_start_in_new_log(
    fake_llm: FakeLLMService, tmp_path: Path
) -> None:
    """After /clear, the rotated log starts with session_start{provider}."""
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        core.handle_input("/clear")
        rotated_path = live_log.current_path

    from mcp_coder.icoder.core.event_log import iter_events

    events = list(iter_events(rotated_path))
    assert events[0]["event"] == "session_start"
    assert events[0]["provider"] == "claude"


def test_clear_log_visible_to_picker(fake_llm: FakeLLMService, tmp_path: Path) -> None:
    """list_icoder_logs (provider-filtered) includes the post-/clear log."""
    with EventLog(logs_dir=tmp_path) as live_log:
        core = AppCore(llm_service=fake_llm, event_log=live_log)
        core.handle_input("/clear")
        rotated_path = live_log.current_path

    from mcp_coder.icoder.core.log_inventory import list_icoder_logs

    summaries = list_icoder_logs(tmp_path, provider="claude")
    paths = [s.path for s in summaries]
    assert rotated_path in paths
