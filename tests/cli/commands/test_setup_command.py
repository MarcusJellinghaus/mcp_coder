"""Tests for the `mcp-coder setup` subcommand: parser, execute_setup, dispatch."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.setup import execute_setup
from mcp_coder.cli.main import create_parser, main
from mcp_coder.install.project_setup import SetupError

_RUN_SETUP = "mcp_coder.cli.commands.setup.run_setup"


class TestSetupParser:
    """create_parser() registers `setup` and parses its flags."""

    def test_defaults(self) -> None:
        args = create_parser().parse_args(["setup"])
        assert args.command == "setup"
        assert args.project_dir is None
        assert args.refresh is False
        assert args.skip_overrides is False

    def test_flags_are_parsed(self) -> None:
        args = create_parser().parse_args(
            ["setup", "--project-dir", "X", "--refresh", "--skip-overrides"]
        )
        assert args.project_dir == "X"
        assert args.refresh is True
        assert args.skip_overrides is True


class TestExecuteSetup:
    """execute_setup resolves the project dir, runs setup, maps errors to 1."""

    def test_passes_resolved_dir_and_flags(self, tmp_path: Path) -> None:
        args = create_parser().parse_args(
            ["setup", "--project-dir", str(tmp_path), "--refresh", "--skip-overrides"]
        )
        with patch(_RUN_SETUP) as mock_run:
            assert execute_setup(args) == 0
        mock_run.assert_called_once_with(
            tmp_path.resolve(), refresh=True, skip_overrides=True
        )

    def test_success_returns_zero(self, tmp_path: Path) -> None:
        args = create_parser().parse_args(["setup", "--project-dir", str(tmp_path)])
        with patch(_RUN_SETUP) as mock_run:
            assert execute_setup(args) == 0
        mock_run.assert_called_once_with(
            tmp_path.resolve(), refresh=False, skip_overrides=False
        )

    def test_no_project_dir_uses_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        args = create_parser().parse_args(["setup"])
        with patch(_RUN_SETUP) as mock_run:
            assert execute_setup(args) == 0
        assert mock_run.call_args.args[0] == tmp_path.resolve()

    def test_value_error_returns_one_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        args = create_parser().parse_args(["setup", "--project-dir", str(tmp_path)])
        with (
            patch(_RUN_SETUP, side_effect=ValueError("bad setup table")),
            caplog.at_level(logging.ERROR),
        ):
            assert execute_setup(args) == 1
        assert "bad setup table" in caplog.text

    def test_setup_error_returns_one_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        args = create_parser().parse_args(["setup", "--project-dir", str(tmp_path)])
        with (
            patch(_RUN_SETUP, side_effect=SetupError("npm ci: exited with code 1")),
            caplog.at_level(logging.ERROR),
        ):
            assert execute_setup(args) == 1
        assert "npm ci: exited with code 1" in caplog.text

    def test_missing_project_dir_returns_one(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        missing = tmp_path / "does-not-exist"
        args = create_parser().parse_args(["setup", "--project-dir", str(missing)])
        mock_run = MagicMock()
        with patch(_RUN_SETUP, mock_run), caplog.at_level(logging.INFO):
            assert execute_setup(args) == 1
        mock_run.assert_not_called()
        assert str(missing.resolve()) in caplog.text
        assert "nothing to do" not in caplog.text

    def test_file_as_project_dir_returns_one(self, tmp_path: Path) -> None:
        a_file = tmp_path / "file.txt"
        a_file.write_text("x", encoding="utf-8")
        args = create_parser().parse_args(["setup", "--project-dir", str(a_file)])
        with patch(_RUN_SETUP) as mock_run:
            assert execute_setup(args) == 1
        mock_run.assert_not_called()


class TestSetupDispatch:
    """main() routes the setup command to execute_setup."""

    def test_main_dispatches_setup(self) -> None:
        with (
            patch("mcp_coder.cli.main.execute_setup", return_value=0) as mock_execute,
            patch("sys.argv", ["mcp-coder", "setup", "--refresh"]),
        ):
            assert main() == 0
        mock_execute.assert_called_once()
        assert mock_execute.call_args.args[0].command == "setup"
