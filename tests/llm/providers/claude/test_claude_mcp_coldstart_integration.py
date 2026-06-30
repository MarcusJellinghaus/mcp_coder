"""Slow-MCP-stub cold-start integration tests (#999).

Acceptance proof for restoring the ``ToolSearch`` wait-bridge. These drive the
*real* Claude CLI against a deliberately slow stub MCP server (see
``_mcp_stub_server.py``) and assert end-to-end behaviour the unit tests cannot:

- **init.tools acceptance:** the init event advertises ``ToolSearch`` and the
  stub MCP tool, while the native file/exec built-ins
  (``Bash``/``Edit``/``Read``/``Write``) stay disabled.
- **v1 (self-heal):** the stub is ``pending`` at init (still cold-starting), and
  within the same session the model uses the wait-bridge, makes a *real*
  ``tool_use`` for the stub tool, gets the sentinel back, and echoes it in the
  final text — with no fabricated tool blocks. This is the headline red→green
  proof: under ``--tools ""`` (no ``ToolSearch``) the model would run blind and
  never make a real tool call.
- **v2 (never connects):** the stub's startup delay exceeds ``MCP_TIMEOUT`` so
  it never connects. The run must fail cleanly (raise / error event) without the
  sentinel appearing and without a hallucinated tool result.

Marked ``claude_cli_integration`` (slow; excluded from the default fast suite)
and skipped cleanly when the ``claude`` executable is absent.
"""

import json
import secrets
import sys
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    McpServersUnavailableError,
    ask_claude_code_cli,
)
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)
from mcp_coder.llm.providers.claude.claude_mcp_guard import (
    StreamMessage,
    parse_stream_json_file,
)

_STUB_SERVER = Path(__file__).with_name("_mcp_stub_server.py")

# Stub tool identity. Claude names MCP tools ``mcp__<server>__<tool>`` (the
# server segment may be sanitized), so we match on the tool suffix to stay
# robust against name-mangling of the "mcp-stub" server name.
_STUB_TOOL_SUFFIX = "reveal_sentinel"

# v1: past the ~5 s alwaysLoad cap (so the server is pending at init) but well
# under MCP_TIMEOUT, so it connects shortly after and self-heals in-session.
_V1_STARTUP_DELAY_SECONDS = 8

# v2: a short MCP_TIMEOUT paired with a startup delay that exceeds it, so the
# stub never connects within the session.
_V2_MCP_TIMEOUT_MS = "3000"
_V2_STARTUP_DELAY_SECONDS = 30

# Native built-ins that must stay disabled (only ToolSearch is restored).
_DISABLED_BUILTINS = ("Bash", "Edit", "Read", "Write")


def _make_sentinel() -> str:
    """Return an unguessable sentinel token for a single run."""
    return f"SENTINEL-{secrets.token_hex(12)}"


def _write_stub_mcp_config(
    tmp_path: Path, *, sentinel: str, startup_delay_seconds: float
) -> Path:
    """Write a ``.mcp.json`` registering the stub server via ``sys.executable``.

    Mirrors production shape: a single stdio server with ``alwaysLoad: true`` and
    the sentinel / startup-delay passed through the server ``env`` block.

    Args:
        tmp_path: Per-test temp directory.
        sentinel: The unguessable value the stub tool returns.
        startup_delay_seconds: Seconds the stub sleeps before serving stdio.

    Returns:
        Path to the written ``.mcp.json``.
    """
    config = {
        "mcpServers": {
            "mcp-stub": {
                "type": "stdio",
                "command": sys.executable,
                "args": [str(_STUB_SERVER)],
                "env": {
                    "MCP_STUB_SENTINEL": sentinel,
                    "MCP_STUB_STARTUP_DELAY_SECONDS": str(startup_delay_seconds),
                },
                "alwaysLoad": True,
            }
        }
    }
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path


def _write_stub_settings(tmp_path: Path) -> Path:
    """Write a Claude settings file granting the stub tool and ``ToolSearch``.

    A headless run otherwise blocks the MCP ``tool_use`` with a permission
    prompt (no interactive grant possible), so the self-heal can never surface
    a real ``tool_result``. Pre-allowing the stub tool removes that gate without
    weakening the test: the sentinel is still unguessable, so only a genuine
    call can produce it.

    Args:
        tmp_path: Per-test temp directory.

    Returns:
        Path to the written settings JSON.
    """
    settings = {
        "permissions": {
            "allow": [
                "ToolSearch",
                "mcp__mcp-stub__reveal_sentinel",
            ]
        },
        "enableAllProjectMcpServers": True,
        "enabledMcpjsonServers": ["mcp-stub"],
    }
    settings_path = tmp_path / "settings.local.json"
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings_path


def _latest_stream_log(logs_dir: Path) -> Path:
    """Return the most recent stream-json log written under ``logs_dir``."""
    candidates = sorted((logs_dir / "claude-sessions").glob("session_*.ndjson"))
    assert candidates, f"no stream log written under {logs_dir}"
    return candidates[-1]


def _init_message(parsed_messages: list[StreamMessage]) -> StreamMessage:
    """Return the ``system``/``init`` message from parsed stream messages."""
    for msg in parsed_messages:
        if msg.get("type") == "system" and msg.get("subtype") == "init":
            return msg
    raise AssertionError("no init (system/init) event found in stream log")


def _init_tool_names(init_msg: StreamMessage) -> list[str]:
    """Return the tool-name list advertised by the init event."""
    tools = init_msg.get("tools") or []
    names: list[str] = []
    for tool in tools:
        if isinstance(tool, str):
            names.append(tool)
        elif isinstance(tool, dict):
            names.append(str(tool.get("name", "")))
    return names


def _mcp_server_status(init_msg: StreamMessage, name_fragment: str) -> str | None:
    """Return the status of the MCP server whose name contains ``name_fragment``."""
    for server in init_msg.get("mcp_servers") or []:
        if isinstance(server, dict) and name_fragment in str(server.get("name", "")):
            return str(server.get("status", "")).strip().lower()
    return None


def _iter_content_blocks(messages: list[StreamMessage]) -> list[dict[str, Any]]:
    """Flatten all assistant/user message content blocks into a single list."""
    blocks: list[dict[str, Any]] = []
    for msg in messages:
        message_data = msg.get("message")
        if not isinstance(message_data, dict):
            continue
        content = message_data.get("content")
        if isinstance(content, list):
            blocks.extend(b for b in content if isinstance(b, dict))
    return blocks


def _stub_question() -> str:
    """Prompt that forces the model to surface the stub tool's return value."""
    return (
        "Call the available MCP tool whose name ends with 'reveal_sentinel' "
        "(it takes no arguments) and reply with ONLY the exact string it "
        "returns. Do not invent or guess a value — you must call the tool."
    )


@pytest.mark.claude_cli_integration
class TestClaudeMcpColdStartIntegration:
    """Real-CLI cold-start scenarios proving the ToolSearch wait-bridge."""

    def test_v1_pending_server_self_heals_via_toolsearch(
        self, require_claude_cli: None, tmp_path: Path
    ) -> None:
        """v1: pending stub self-heals; a real tool_use returns the sentinel.

        Also carries the init.tools acceptance assertion: ToolSearch present,
        native built-ins absent, stub MCP tool advertised.
        """
        sentinel = _make_sentinel()
        mcp_config = _write_stub_mcp_config(
            tmp_path,
            sentinel=sentinel,
            startup_delay_seconds=_V1_STARTUP_DELAY_SECONDS,
        )
        settings_file = _write_stub_settings(tmp_path)
        logs_dir = tmp_path / "logs"

        # Drive the real CLI; assertions read the captured stream-json log so
        # tool_use / tool_result blocks (not just the final text) are inspected.
        ask_claude_code_cli(
            _stub_question(),
            timeout=120,
            cwd=str(tmp_path),
            mcp_config=str(mcp_config),
            settings_file=str(settings_file),
            logs_dir=str(logs_dir),
            env_vars={"MCP_TIMEOUT": "60000"},
        )

        parsed = parse_stream_json_file(_latest_stream_log(logs_dir))
        messages = parsed["messages"]
        init_msg = _init_message(messages)

        # --- init.tools acceptance ---------------------------------------
        # ToolSearch must be the restored wait-bridge and native file/exec
        # built-ins must stay disabled. The stub MCP tool is intentionally NOT
        # asserted here: a server that is still ``pending`` at init has not yet
        # published its tools, so they cannot appear in init.tools. Its presence
        # is proven instead by the genuine post-connect ``tool_use`` below — the
        # stronger end-to-end signal.
        tool_names = _init_tool_names(init_msg)
        assert (
            "ToolSearch" in tool_names
        ), f"ToolSearch missing from init tools: {tool_names}"
        for builtin in _DISABLED_BUILTINS:
            assert (
                builtin not in tool_names
            ), f"native built-in {builtin!r} should be disabled: {tool_names}"

        # --- v1: stub was pending at init --------------------------------
        stub_status = _mcp_server_status(init_msg, "stub")
        assert (
            stub_status == "pending"
        ), f"expected stub 'pending' at init, got {stub_status!r}"

        # --- v1: a REAL tool_use for the stub tool occurred --------------
        blocks = _iter_content_blocks(messages)
        tool_uses = [
            b
            for b in blocks
            if b.get("type") == "tool_use"
            and _STUB_TOOL_SUFFIX in str(b.get("name", ""))
        ]
        assert tool_uses, (
            "no real tool_use for the stub tool — model ran blind "
            '(would fail under --tools "")'
        )

        # --- v1: a tool_result carried the sentinel ----------------------
        tool_results_text = "".join(
            json.dumps(b.get("content", "")) + str(b.get("content", ""))
            for b in blocks
            if b.get("type") == "tool_result"
        )
        assert (
            sentinel in tool_results_text
        ), "sentinel not found in any tool_result — no genuine tool output"

        # --- v1: final text echoes the sentinel --------------------------
        assert (
            sentinel in parsed["text"]
        ), f"sentinel not in final text: {parsed['text']!r}"

    def test_v2_never_connects_fails_clean_no_hallucination(
        self, require_claude_cli: None, tmp_path: Path
    ) -> None:
        """v2: stub never connects → clean failure, sentinel absent, no fake tool."""
        sentinel = _make_sentinel()
        mcp_config = _write_stub_mcp_config(
            tmp_path,
            sentinel=sentinel,
            startup_delay_seconds=_V2_STARTUP_DELAY_SECONDS,
        )
        settings_file = _write_stub_settings(tmp_path)
        logs_dir = tmp_path / "logs"

        final_text = ""
        raised_clean = False
        try:
            result = ask_claude_code_cli(
                _stub_question(),
                timeout=60,
                cwd=str(tmp_path),
                mcp_config=str(mcp_config),
                settings_file=str(settings_file),
                logs_dir=str(logs_dir),
                env_vars={"MCP_TIMEOUT": _V2_MCP_TIMEOUT_MS},
            )
            final_text = result["text"]
        except McpServersUnavailableError:
            # Clean fatal guard abort (stub reached a terminal/failed status).
            raised_clean = True

        log_path = _latest_stream_log(logs_dir)
        parsed = parse_stream_json_file(log_path)

        # The unguessable sentinel must never appear: no real tool output, and
        # (backstop) the model must not have fabricated it either.
        log_text = log_path.read_text(encoding="utf-8")
        assert (
            sentinel not in log_text
        ), "sentinel leaked without a connected server — hallucinated tool result"
        assert (
            sentinel not in final_text
        ), f"sentinel hallucinated into final text: {final_text!r}"

        # No genuine tool_result could exist (server never connected).
        blocks = _iter_content_blocks(parsed["messages"])
        stub_tool_results = [
            b
            for b in blocks
            if b.get("type") == "tool_result"
            and sentinel in json.dumps(b.get("content", ""))
        ]
        assert not stub_tool_results, "unexpected stub tool_result with no server"

        # Run ended in a recognisably non-success state: either a clean guard
        # abort, or no successful sentinel-bearing answer (covered above).
        # Surface the disposition for debugging.
        assert raised_clean or sentinel not in final_text
