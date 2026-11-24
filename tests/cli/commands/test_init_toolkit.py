"""Tests for the toolkit-dependent part of the init deploy."""

import argparse
import logging
from pathlib import Path

import pytest

from mcp_coder.cli.commands.init import _ADAPT_URL, DEPLOY_SUBDIRS, execute_init


class TestInitToolkit:
    """execute_init() deploys python.md only for the mcp-tools-py toolkit."""

    @staticmethod
    def _run_init(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        config: tuple[str, str] | None,
    ) -> tuple[int, Path]:
        """Deploy a sample source, including knowledge_base/python.md.

        Args:
            tmp_path: Test temp dir.
            monkeypatch: Pytest monkeypatch fixture.
            caplog: Pytest log capture fixture.
            config: ``(file name, content)`` written to the project root, or
                None for no config file.

        Returns:
            The exit code and the project dir.
        """
        source = tmp_path / "source"
        for name in DEPLOY_SUBDIRS:
            d = source / name
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{name}.md").write_text(f"content of {name}")
        (source / "knowledge_base" / "python.md").write_text("python notes")
        project = tmp_path / "project"
        project.mkdir()
        if config is not None:
            (project / config[0]).write_text(config[1])
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )
        args = argparse.Namespace(
            command="init", just_skills=True, project_dir=str(project)
        )
        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)
        return result, project

    def test_command_toolkit_skips_python_md_and_reminds(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A non-Python toolkit skips python.md and prints the reminder."""
        result, project = self._run_init(
            tmp_path,
            monkeypatch,
            caplog,
            ("mcp-coder.toml", '[tool.mcp-coder.toolkit]\ntoolkit = "command"\n'),
        )

        assert result == 0
        claude = project / ".claude"
        assert not (claude / "knowledge_base" / "python.md").exists()
        for name in DEPLOY_SUBDIRS:
            assert (claude / name / f"{name}.md").exists()
        assert "are generic" in caplog.text
        assert _ADAPT_URL in caplog.text

    def test_python_toolkit_deploys_python_md_without_reminder(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The mcp-tools-py toolkit deploys python.md and prints no reminder."""
        result, project = self._run_init(
            tmp_path,
            monkeypatch,
            caplog,
            ("pyproject.toml", '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n'),
        )

        assert result == 0
        assert (project / ".claude" / "knowledge_base" / "python.md").exists()
        assert "are generic" not in caplog.text

    @pytest.mark.real_toolkit_config
    def test_no_toolkit_warns_and_skips_python_md(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """No toolkit table: warn with the config error, skip python.md, remind."""
        result, project = self._run_init(tmp_path, monkeypatch, caplog, None)

        assert result == 0
        assert not (project / ".claude" / "knowledge_base" / "python.md").exists()
        warnings = [
            r.getMessage() for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert any(
            "No [tool.mcp-coder.toolkit] table in pyproject.toml or mcp-coder.toml."
            in msg
            and 'toolkit = "command"' in msg
            for msg in warnings
        )
        assert "are generic" in caplog.text
