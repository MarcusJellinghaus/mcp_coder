"""Tests for .gitignore handling in the init command."""

import argparse
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.init import (
    DEPLOY_SUBDIRS,
    _missing_session_log_lines,
    _spellings,
    _write_session_log_entries,
    execute_init,
)
from mcp_coder.cli.commands.init_file_access import file_access_template
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflows.vscodeclaude.templates import GITIGNORE_ENTRY

_SESSION_LOG_BLOCK = "\n# mcp-coder session logs\n/.mcp-coder/*\n/logs/\n"


def _lines(path: Path) -> list[str]:
    """Return the stripped lines of a UTF-8 file."""
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]


class TestMissingSessionLogLines:
    """Tests for the pure _missing_session_log_lines() check."""

    @pytest.mark.parametrize(
        "text",
        [f"{s}\n/logs/\n" for s in sorted(_spellings(".mcp-coder"))]
        + [f"/.mcp-coder/*\n{s}\n" for s in sorted(_spellings("logs"))]
        + ["/.mcp-coder/*\n  logs/  \n"],
    )
    def test_every_spelling_counts_as_present(self, text: str) -> None:
        """Each accepted spelling of a folder line counts as present."""
        assert not _missing_session_log_lines(text)

    def test_spellings_has_eight_entries(self) -> None:
        """Two leads times four tails give eight exact lines."""
        assert len(_spellings("logs")) == 8

    def test_empty_text_misses_both(self) -> None:
        """An empty .gitignore lacks both lines, in fixed order."""
        assert _missing_session_log_lines("") == ["/.mcp-coder/*", "/logs/"]

    def test_narrower_line_does_not_count(self) -> None:
        """A line ignoring only a subfolder does not cover the whole folder."""
        text = "logs/claude-sessions/\n/.mcp-coder/*\n"
        assert _missing_session_log_lines(text) == ["/logs/"]

    def test_own_repo_gitignore_has_both(self) -> None:
        """mcp-coder's own .gitignore already ignores both folders."""
        gitignore = Path(__file__).resolve().parents[3] / ".gitignore"
        text = gitignore.read_text(encoding="utf-8-sig")
        assert not _missing_session_log_lines(text)


class TestWriteSessionLogEntries:
    """Tests for _write_session_log_entries() on its own."""

    def test_bom_crlf_no_trailing_newline(self, tmp_path: Path) -> None:
        """BOM and CRLF are tolerated; the block starts on its own line, LF."""
        gitignore = tmp_path / ".gitignore"
        original = b"\xef\xbb\xbf.mcp-coder/\r\n*.pyc"
        gitignore.write_bytes(original)

        assert _write_session_log_entries(tmp_path) == (True, True)

        assert gitignore.read_bytes() == (
            original + b"\n\n# mcp-coder session logs\n/logs/\n"
        )


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
        lines = _lines(gitignore)
        assert lines.count("/logs/") == 1
        assert lines.count("/.mcp-coder/*") == 1

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_crlf_gitignore_stays_crlf(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Both .gitignore writers of init follow a CRLF file's ending."""
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
        gitignore.write_bytes(b"*.pyc\r\n")

        assert execute_init(args) == 0

        raw = gitignore.read_bytes()
        assert b".vscodeclaude_session.json" in raw  # update_gitignore ran
        assert b".scratch/" in raw  # ensure_scratch_gitignored ran
        assert b"\n" not in raw.replace(b"\r\n", b"")  # no lone LF

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
        assert "/logs/" in _lines(project / ".gitignore")
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
        assert "Gitignore: /.mcp-coder/*, /logs/ present" in caplog.text

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
        # The .scratch/ writer ran too and gave up on the same file
        assert "Failed to add .scratch/ to .gitignore" in caplog.text
        assert "Failed to add session log entries to .gitignore" in caplog.text
        # The run continued past the failure
        mock_create.assert_called_once()  # type: ignore[attr-defined]
        # The undecodable file is left untouched
        assert gitignore.read_bytes() == original_bytes

    def _setup_project(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create an empty project and point init at a fake source dir."""
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )
        return project

    @staticmethod
    def _args(project: Path) -> argparse.Namespace:
        """Full-init arguments for *project*."""
        return argparse.Namespace(
            command="init", just_skills=False, project_dir=str(project)
        )

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_session_log_block_in_empty_project(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An empty project gets both session-log lines under their header."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        project = self._setup_project(tmp_path, monkeypatch)

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.commands.init"):
            result = execute_init(self._args(project))

        assert result == 0
        text = (project / ".gitignore").read_text(encoding="utf-8")
        assert _SESSION_LOG_BLOCK in text
        assert "Gitignore: /.mcp-coder/*, /logs/ added" in caplog.text
        assert "Commit .gitignore and .mcp-file-access" in caplog.text

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_only_missing_session_log_line_added(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An existing .mcp-coder/ spelling means only /logs/ is appended."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        project = self._setup_project(tmp_path, monkeypatch)
        gitignore = project / ".gitignore"
        gitignore.write_text(".mcp-coder/\n", encoding="utf-8")

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.commands.init"):
            result = execute_init(self._args(project))

        assert result == 0
        assert "Gitignore: /logs/ added" in caplog.text
        lines = _lines(gitignore)
        assert "/logs/" in lines
        assert "/.mcp-coder/*" not in lines

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_session_log_write_failure_exits_1_but_finishes_run(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A failed session-log write exits 1 without aborting the run."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        project = self._setup_project(tmp_path, monkeypatch)

        def _raise_permission_error(*_args: object, **_kwargs: object) -> None:
            raise PermissionError("read-only")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.append_gitignore_block",
            _raise_permission_error,
        )

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.commands.init"):
            result = execute_init(self._args(project))

        assert result == 1
        assert "Failed to add session log entries" in caplog.text
        mock_create.assert_called_once()  # type: ignore[attr-defined]

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_commit_hint_from_session_log_block_alone(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Adding only the session-log lines still prints the commit hint."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        project = self._setup_project(tmp_path, monkeypatch)
        (project / ".mcp-file-access").write_bytes(file_access_template().encode())
        (project / ".gitignore").write_bytes((GITIGNORE_ENTRY + ".scratch/\n").encode())

        # Parent logger: the rules and .scratch/ lines come from init_file_access
        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.commands"):
            result = execute_init(self._args(project))

        assert result == 0
        assert "Gitignore: /.mcp-coder/*, /logs/ added" in caplog.text
        assert "Gitignore: 0 entries added" in caplog.text
        assert "File access rules: unchanged" in caplog.text
        assert "Gitignore: .scratch/ present" in caplog.text
        assert "Commit .gitignore and .mcp-file-access" in caplog.text

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_session_log_lines_written_despite_invalid_rules_file(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The session-log lines do not depend on the rules-file outcome."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/config.toml"  # type: ignore[attr-defined]
        project = self._setup_project(tmp_path, monkeypatch)
        (project / ".mcp-file-access").write_bytes(b"bogus /x\n")

        # Parent logger: the .scratch/ line comes from init_file_access
        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.commands"):
            execute_init(self._args(project))

        assert "Gitignore: .scratch/ skipped (rules file invalid)" in caplog.text
        lines = _lines(project / ".gitignore")
        assert "/.mcp-coder/*" in lines
        assert "/logs/" in lines
