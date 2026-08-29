"""Guard tests for langchain session resumption via the default history path.

Deliberately placed in ``tests/llm/providers/`` rather than in
``tests/llm/providers/langchain/``: the ``skip_langchain_history_guard`` fixture
lives in that directory's conftest, and these tests must see the real guard.

They also exercise the production (``base_dir``-free) path, redirecting
``Path.home()`` into ``tmp_path`` so ``~/.mcp_coder/sessions/langchain/`` is a
temporary directory.
"""

import uuid
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain import (
    _resolve_session_id,
    ask_langchain,
    ask_langchain_stream,
)
from mcp_coder.llm.storage.session_storage import store_langchain_history

_CONFIG: dict[str, str | None] = {
    "backend": "openai",
    "model": "gpt-4o-mini",
    "api_key": "k",
    "base_url": None,
    "api_version": None,
    "default_provider": None,
}


@pytest.fixture
def home_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[Path, None, None]:
    """Redirect ~/.mcp_coder/sessions/langchain/ into tmp_path.

    Yields:
        The temporary home directory.
    """
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    yield tmp_path


@pytest.fixture
def configured_backend() -> Generator[None, None, None]:
    """Report a configured backend so the guard is what raises.

    Without this the pre-existing "backend not configured" ValueError fires
    first and the guard tests would pass for the wrong reason.
    """
    with patch(
        "mcp_coder.llm.providers.langchain._load_langchain_config",
        return_value=dict(_CONFIG),
    ):
        yield


class TestLangchainSessionGuard:
    """The resume guard on both langchain entry points."""

    def test_ask_langchain_raises_for_unknown_session_id(
        self, home_dir: Path, configured_backend: None
    ) -> None:
        """Resuming an id with no history file names the id and the path."""
        with pytest.raises(ValueError) as exc_info:
            ask_langchain("q", session_id="ghost-id")

        message = str(exc_info.value)
        assert "ghost-id" in message
        assert "ghost-id.json" in message
        assert str(home_dir) in message

    def test_ask_langchain_stream_raises_for_unknown_session_id(
        self, home_dir: Path, configured_backend: None
    ) -> None:
        """The streaming entry point is guarded too (lazily, on first next())."""
        with pytest.raises(ValueError) as exc_info:
            list(ask_langchain_stream("q", session_id="ghost-id"))

        message = str(exc_info.value)
        assert "ghost-id" in message
        assert "ghost-id.json" in message
        assert str(home_dir) in message

    def test_resolve_session_id_accepts_existing_history(self, home_dir: Path) -> None:
        """A successful resume stays silent and returns the requested id."""
        store_langchain_history("known-id", [])

        assert _resolve_session_id("known-id") == "known-id"

    def test_resolve_session_id_mints_uuid_when_none_given(
        self, home_dir: Path
    ) -> None:
        """A new session is unaffected: a fresh UUID, no filesystem touch."""
        sid = _resolve_session_id(None)

        uuid.UUID(sid)
        assert not list(home_dir.rglob("*.json"))
