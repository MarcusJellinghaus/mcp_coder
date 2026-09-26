"""Tests for the `mcp-coder install` subcommand: parser and dispatch."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from mcp_coder.cli.commands.install import execute_install
from mcp_coder.cli.main import create_parser, main


class TestInstallParser:
    """create_parser() registers `install` and parses its flags."""

    def test_install_is_registered_as_a_subcommand(self) -> None:
        args = create_parser().parse_args(["install", "some/target"])
        assert args.command == "install"
        assert args.target == Path("some/target")

    def test_parser_defaults(self) -> None:
        """The defaults tests/install/'s _namespace helper mirrors.

        --extras and --local-path are sentinels (None means "not passed"),
        and --python defaults to the current interpreter.
        """
        args = create_parser().parse_args(["install", "some/target"])
        assert args.extras is None
        assert args.local_path is None
        assert args.python == sys.executable
        assert args.source == "git"
        assert args.ref == "main"
        assert args.extra_packages == ""
        assert args.use_sync is False
        assert args.skip_overrides is False
        assert args.refresh is False
        assert args.clean is False
        assert args.check is False

    def test_flags_are_parsed(self) -> None:
        args = create_parser().parse_args(
            [
                "install",
                "some/target",
                "--source",
                "local",
                "--local-path",
                "some/checkout",
                "--extras",
                "",
                "--extra-packages",
                "langchain mlflow",
                "--ref",
                "feature-x",
                "--use-sync",
                "--skip-overrides",
                "--refresh",
                "--clean",
                "--check",
            ]
        )
        assert args.source == "local"
        assert args.local_path == Path("some/checkout")
        assert args.extras == ""
        assert args.extra_packages == "langchain mlflow"
        assert args.ref == "feature-x"
        assert args.use_sync is True
        assert args.skip_overrides is True
        assert args.refresh is True
        assert args.clean is True
        assert args.check is True


class TestInstallDispatch:
    """main() routes the install command to execute_install."""

    def test_main_dispatches_install(self) -> None:
        with (
            patch("mcp_coder.cli.main.execute_install", return_value=0) as mock_execute,
            patch("sys.argv", ["mcp-coder", "install", "some/target"]),
        ):
            assert main() == 0
        mock_execute.assert_called_once()
        assert mock_execute.call_args.args[0].command == "install"


class TestExecuteInstall:
    """execute_install resolves the config, runs the install, maps errors to 1."""

    def test_resolved_config_is_installed(self, tmp_path: Path) -> None:
        """The parsed args become an InstallConfig that install() receives."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.install]\nextras = "dev,mlflow"\n', encoding="utf-8"
        )
        args = create_parser().parse_args(
            [
                "install",
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
            ]
        )

        with patch("mcp_coder.cli.commands.install.install") as mock_install:
            assert execute_install(args) == 0

        mock_install.assert_called_once()
        config = mock_install.call_args.args[0]
        assert config.target == tmp_path.resolve()
        assert config.local_path == tmp_path.resolve()
        assert config.source == "local"
        assert config.extras == "dev,mlflow"

    def test_invalid_config_returns_one(self, tmp_path: Path) -> None:
        args = create_parser().parse_args(
            ["install", str(tmp_path), "--source", "local"]
        )
        assert execute_install(args) == 1

    def test_invalid_target_pyproject_returns_one(self, tmp_path: Path) -> None:
        """A pyproject.toml rejected inside a phase is exit 1, not a crash.

        Runs with ``--check`` and a stubbed uv lookup, so no subprocess is
        spawned: the failure comes from ``phase_overrides``' config read.
        """
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.install-from-github]\npackages = "pkg-a"\n',
            encoding="utf-8",
        )
        args = create_parser().parse_args(
            [
                "install",
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--check",
            ]
        )

        with patch("mcp_coder.install.ensure_system_uv", return_value="/stub/bin/uv"):
            assert execute_install(args) == 1
