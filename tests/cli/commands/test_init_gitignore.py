"""Tests for .gitignore handling in the init command."""

import argparse
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.init import DEPLOY_SUBDIRS, execute_init
from mcp_coder.utils.log_utils import OUTPUT


class TestExecuteInitGitignore:
    """Tests for execute_init() .gitignore integration."""

    @staticmethod
    def _make_source(base: Path) -> Path:
        """Create a source dir with sample files in all DEPLOY_SUBDIRS."""
        for name in DEPLOY_SUBDIRS:
            d = base / name
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{name}.md").write_text(f"content of {name}")
        return base

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_gitignore_block_written_and_second_run_is_noop(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Entries land in .gitignore; a second run changes nothing."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )
        args = argparse.Namespace(
            command="init", just_skills=False, project_dir=str(project)
        )
        gitignore = project / ".gitignore"

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.commands.init"):
            result = execute_init(args)

        assert result == 0
        assert ".vscodeclaude_session.json" in gitignore.read_text(encoding="utf-8")
        # No .git/ in the project -> warning
        assert "no .git/" in caplog.text

        content_after_first_run = gitignore.read_bytes()
        caplog.clear()

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.commands.init"):
            result = execute_init(args)

        assert result == 0
        assert gitignore.read_bytes() == content_after_first_run
        # Nothing written -> no warning
        assert "no .git/" not in caplog.text

    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_just_skills_still_writes_gitignore(
        self,
        mock_create: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """--just-skills skips user config but still writes .gitignore."""
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )
        args = argparse.Namespace(
            command="init", just_skills=True, project_dir=str(project)
        )

        result = execute_init(args)

        assert result == 0
        assert ".vscodeclaude_session.json" in (project / ".gitignore").read_text(
            encoding="utf-8"
        )
        mock_create.assert_not_called()  # type: ignore[attr-defined]

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_gitignore_write_failure_exits_1_but_finishes_run(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A .gitignore write failure exits 1 without aborting the run."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )

        def _raise_permission_error(_folder_path: Path) -> list[str]:
            raise PermissionError("read-only")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.update_gitignore",
            _raise_permission_error,
        )
        args = argparse.Namespace(
            command="init", just_skills=False, project_dir=str(project)
        )

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.commands.init"):
            result = execute_init(args)

        assert result == 1
        assert "Failed to update .gitignore" in caplog.text
        # The step before gitignore ran
        assert (project / ".claude" / "skills" / "skills.md").exists()
        # The step after gitignore still ran
        mock_create.assert_called_once()  # type: ignore[attr-defined]

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_gitignore_reports_what_it_did(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Init reports how many entries it added, zero included."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )
        args = argparse.Namespace(
            command="init", just_skills=False, project_dir=str(project)
        )

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.commands.init"):
            result = execute_init(args)

        assert result == 0
        assert "Gitignore: 5 entries added" in caplog.text

        caplog.clear()

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.commands.init"):
            result = execute_init(args)

        assert result == 0
        assert "Gitignore: 0 entries added" in caplog.text

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_non_utf8_gitignore_does_not_abort_init(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An undecodable .gitignore is left alone and does not abort init."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )
        gitignore = project / ".gitignore"
        original_bytes = b"\xff\xfe*.pyc\n"
        gitignore.write_bytes(original_bytes)
        args = argparse.Namespace(
            command="init", just_skills=False, project_dir=str(project)
        )

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.commands.init"):
            result = execute_init(args)

        assert result == 1
        assert "Failed to update .gitignore" in caplog.text
        # The run continued past the failure
        mock_create.assert_called_once()  # type: ignore[attr-defined]
        # The undecodable file is left untouched
        assert gitignore.read_bytes() == original_bytes
