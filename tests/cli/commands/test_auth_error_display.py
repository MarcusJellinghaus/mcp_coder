"""Display of Claude auth failures in ``prompt`` and ``verify`` (issue #33).

Both boundaries show the CLI's own text, prefixed once by the login hint.
"""

import argparse
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt
from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)
from mcp_coder.llm.types import LLMAuthError, StreamEvent
from mcp_coder.utils.subprocess_runner import CalledProcessError, CommandResult
from tests.logged_out_capture import (
    AUTH_HINT,
    AUTH_MESSAGE,
    CLI_TEXT,
    LOGGED_OUT_RC,
    LOGGED_OUT_STDERR,
    load_logged_out_lines,
)

from .conftest import (
    _VERIFY,
    _claude_ok,
    _github_ok_default,
    _make_args,
    _mlflow_not_installed,
)

_PROMPT = "mcp_coder.cli.commands.prompt"
_STREAMING = "mcp_coder.llm.providers.claude.claude_code_cli_streaming"


def _logged_out_events(tmp_path: Path) -> list[StreamEvent]:
    """Run the real streaming core on the logged-out capture."""
    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(load_logged_out_lines())
    mock_stream.result = CommandResult(
        return_code=LOGGED_OUT_RC,
        stdout="",
        stderr=LOGGED_OUT_STDERR,
        timed_out=False,
    )
    with (
        patch(f"{_STREAMING}.stream_subprocess", return_value=mock_stream),
        patch(f"{_STREAMING}._find_claude_executable", return_value="claude"),
        patch(
            f"{_STREAMING}.get_stream_log_path",
            return_value=tmp_path / "stream.ndjson",
        ),
    ):
        return list(ask_claude_code_cli_stream("Reply with OK"))


def _prompt_args(**kwargs: Any) -> argparse.Namespace:
    defaults: dict[str, Any] = {
        "prompt": "Reply with OK",
        "llm_method": "claude",
        "mcp_config": None,
        "settings": None,
        "project_dir": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@patch(f"{_PROMPT}.resolve_mcp_config_path", return_value=None)
@patch(f"{_PROMPT}.resolve_llm_method", return_value=("claude", "cli argument"))
@patch(f"{_PROMPT}.prepare_llm_environment", return_value={})
class TestPromptAuthDisplay:
    """``mcp-coder prompt`` shows the hinted CLI text once."""

    def test_rendered_shows_cli_text_and_hint_once(
        self,
        _mock_env: MagicMock,
        _mock_llm: MagicMock,
        _mock_mcp: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The streaming path prints the error event message exactly once."""
        events = _logged_out_events(tmp_path)
        with patch(f"{_PROMPT}.prompt_llm_stream", return_value=iter(events)):
            result = execute_prompt(_prompt_args())

        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert result == 1
        assert output.count(CLI_TEXT) == 1
        assert output.count(AUTH_HINT) == 1

    def test_json_logs_summarized_auth_error(
        self,
        _mock_env: MagicMock,
        _mock_llm: MagicMock,
        _mock_mcp: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The exception boundary logs ``LLMAuthError: <hinted text>``."""
        with (
            patch(f"{_PROMPT}.prompt_llm", side_effect=LLMAuthError(AUTH_MESSAGE)),
            caplog.at_level(logging.ERROR),
        ):
            result = execute_prompt(_prompt_args(output_format="json"))

        assert result == 1
        errors = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert "LLMAuthError: " in errors[0]
        assert CLI_TEXT in errors[0]
        assert errors[0].count(AUTH_HINT) == 1

    def test_called_process_error_logs_stderr_cause(
        self,
        _mock_env: MagicMock,
        _mock_llm: MagicMock,
        _mock_mcp: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A non-auth CalledProcessError shows its stderr detail."""
        exc = CalledProcessError(
            1, ["claude", "-p"], stderr="real cause Stream file: x"
        )
        with (
            patch(f"{_PROMPT}.prompt_llm", side_effect=exc),
            caplog.at_level(logging.ERROR),
        ):
            result = execute_prompt(_prompt_args(output_format="json"))

        assert result == 1
        assert "real cause" in caplog.text


class TestVerifyAuthDisplay:
    """``mcp-coder verify`` shows the hinted CLI text on the Test prompt row."""

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_test_prompt_row_shows_hinted_cli_text(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """One Test prompt line carries the CLI text with the hint once."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = LLMAuthError(AUTH_MESSAGE)

        result = execute_verify(_make_args(project_dir=str(tmp_path)))
        output = capsys.readouterr().out

        assert result == 1
        rows = [line for line in output.splitlines() if "Test prompt" in line]
        assert len(rows) == 1
        assert CLI_TEXT in rows[0]
        assert rows[0].count(AUTH_HINT) == 1
        assert f"FAILED (LLMAuthError: {AUTH_MESSAGE})" in rows[0]
