"""Test VSCode launch functions for orchestrator."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.workflows.vscodeclaude.orchestrator import launch_vscode


class TestLaunch:
    """Test VSCode launch functions."""

    def test_launch_vscode_returns_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns PID from Popen."""
        mock_process = Mock()
        mock_process.pid = 12345

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.subprocess.Popen",
            lambda *args, **kwargs: mock_process,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()

        pid = launch_vscode(workspace)
        assert pid == 12345

    def test_launch_vscode_uses_code_command(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Calls 'code' with workspace path."""
        captured_args: list[Any] = []
        captured_kwargs: dict[str, Any] = {}

        def mock_popen(args: Any, **kwargs: Any) -> Mock:
            captured_args.append(args)
            captured_kwargs.update(kwargs)
            return Mock(pid=1)

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.orchestrator.subprocess.Popen",
            mock_popen,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()

        launch_vscode(workspace)

        # The command can be a list or a string (shell=True on Windows)
        cmd = captured_args[0]
        if isinstance(cmd, str):
            # Windows: shell command string like 'code "path"'
            assert "code" in cmd
            assert str(workspace) in cmd
        else:
            # Linux: list like ['code', 'path']
            assert "code" in cmd
            assert str(workspace) in cmd
