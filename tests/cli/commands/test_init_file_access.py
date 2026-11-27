"""Tests for the .mcp-file-access and .scratch/ gitignore steps of init."""

import argparse
import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder import mcp_workspace
from mcp_coder.cli.commands.init import DEPLOY_SUBDIRS, execute_init
from mcp_coder.cli.commands.init_file_access import (
    FILE_ACCESS_TEMPLATE_RULES,
    file_access_template,
)
from mcp_coder.mcp_workspace import FileAccess, get_file_access, validate_access_rules
from mcp_coder.utils.log_utils import OUTPUT

REPO_ROOT = Path(__file__).resolve().parents[3]

_MODULE = "mcp_coder.cli.commands.init_file_access"


def _rule_lines(text: str) -> list[str]:
    """Return the non-comment, non-blank lines of a rules file."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _parsed_rules(text: str) -> set[tuple[str, str]]:
    """Return ``(level, pattern)`` for each rule line, whitespace-normalised."""
    rules = set()
    for line in _rule_lines(text):
        level, pattern = line.split(maxsplit=1)
        rules.add((level, "".join(pattern.split())))
    return rules


def _scratch_lines(gitignore: Path) -> list[str]:
    """Return the .gitignore lines that ignore .scratch/."""
    if not gitignore.exists():
        return []
    return [
        line
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() == ".scratch/"
    ]


class TestInitFileAccess:
    """Tests for execute_init() rules-file and .scratch/ handling."""

    @pytest.fixture
    def project(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """A project dir; deploy source and user config are faked."""
        source = tmp_path / "source"
        for name in DEPLOY_SUBDIRS:
            (source / name).mkdir(parents=True)
            (source / name / f"{name}.md").write_text(name, encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir", lambda: source
        )
        project = tmp_path / "project"
        project.mkdir()
        return project

    @pytest.fixture
    def mock_config(self) -> Iterator[MagicMock]:
        """Patch user-config creation; yields the create_default_config mock."""
        with (
            patch("mcp_coder.cli.commands.init.get_config_file_path") as mock_path,
            patch("mcp_coder.cli.commands.init.create_default_config") as mock_create,
        ):
            mock_path.return_value = "/fake/config.toml"
            mock_create.return_value = False
            yield mock_create

    @staticmethod
    def _init(project: Path, just_skills: bool = False) -> int:
        args = argparse.Namespace(
            command="init", just_skills=just_skills, project_dir=str(project)
        )
        return execute_init(args)

    @pytest.mark.parametrize("just_skills", [False, True])
    def test_new_file_created(
        self,
        project: Path,
        mock_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
        just_skills: bool,
    ) -> None:
        """A missing rules file is created (both modes) and .scratch/ ignored."""
        with caplog.at_level(OUTPUT):
            result = self._init(project, just_skills=just_skills)

        assert result == 0
        raw = (project / ".mcp-file-access").read_bytes()
        assert raw.decode("utf-8") == file_access_template()
        assert b"\r\n" not in raw
        assert raw.startswith(b"#")
        assert _scratch_lines(project / ".gitignore") == [".scratch/"]
        assert b"\r\n" not in (project / ".gitignore").read_bytes()
        assert "File access rules: created" in caplog.text
        assert "Gitignore: .scratch/ added" in caplog.text
        assert "Commit .gitignore and .mcp-file-access" in caplog.text

    def test_second_run_changes_nothing(
        self,
        project: Path,
        mock_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A second run leaves both files byte-identical."""
        assert self._init(project) == 0
        rules_before = (project / ".mcp-file-access").read_bytes()
        gitignore_before = (project / ".gitignore").read_bytes()
        caplog.clear()

        with caplog.at_level(OUTPUT):
            assert self._init(project) == 0

        assert (project / ".mcp-file-access").read_bytes() == rules_before
        assert (project / ".gitignore").read_bytes() == gitignore_before
        assert "File access rules: unchanged" in caplog.text
        assert "Gitignore: .scratch/ present" in caplog.text
        assert "Commit .gitignore" not in caplog.text

    def test_existing_file_without_rules_gets_all_appended(
        self,
        project: Path,
        mock_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """User rules stay first; every template rule is appended after them."""
        original = "# mine\nread-only /docs/\n"
        (project / ".mcp-file-access").write_text(original, encoding="utf-8")

        with caplog.at_level(OUTPUT):
            assert self._init(project) == 0

        text = (project / ".mcp-file-access").read_text(encoding="utf-8")
        assert text.startswith(original)
        assert _rule_lines(text)[0] == "read-only /docs/"
        assert _parsed_rules(text) >= {
            (level, pattern) for level, pattern in FILE_ACCESS_TEMPLATE_RULES
        }
        assert f"File access rules: {len(FILE_ACCESS_TEMPLATE_RULES)} rules added" in (
            caplog.text
        )

    def test_existing_file_with_all_rules_unchanged(
        self,
        project: Path,
        mock_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Rules already present (other spacing) are not appended again."""
        original = "".join(
            f"{level}\t{pattern}\n" for level, pattern in FILE_ACCESS_TEMPLATE_RULES
        ).encode("utf-8")
        (project / ".mcp-file-access").write_bytes(original)

        with caplog.at_level(OUTPUT):
            assert self._init(project) == 0

        assert (project / ".mcp-file-access").read_bytes() == original
        assert "File access rules: unchanged" in caplog.text
        assert "Gitignore: .scratch/ added" in caplog.text

    def test_crlf_bom_no_trailing_newline_appends_crlf(
        self, project: Path, mock_config: MagicMock
    ) -> None:
        """Existing bytes are kept; the appended rules start on a new line in the file's CRLF ending."""
        original = b"\xef\xbb\xbf# mine\r\nread-only /docs/"
        (project / ".mcp-file-access").write_bytes(original)

        assert self._init(project) == 0

        raw = (project / ".mcp-file-access").read_bytes()
        assert raw.startswith(original + b"\r\n")
        assert b"\n" not in raw[len(original) :].replace(b"\r\n", b"")
        assert validate_access_rules(project) == []
        assert "read-only /docs/" in _rule_lines(raw.decode("utf-8-sig"))

    def test_overlapping_user_rule_warns(
        self,
        project: Path,
        mock_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A user rule the appended template rule overrides gets a warning."""
        (project / ".mcp-file-access").write_text(
            "read-only .scratch/\n", encoding="utf-8"
        )

        with caplog.at_level(logging.WARNING):
            assert self._init(project) == 0

        assert ".scratch/x" in caplog.text
        assert "overrides it" in caplog.text
        assert get_file_access(".scratch/x", project) == FileAccess.READ_WRITE

    def test_same_pattern_user_rule_kept(
        self,
        project: Path,
        mock_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A same-pattern user rule is kept, not overridden; .scratch/ skipped."""
        (project / ".mcp-file-access").write_text(
            "read-only    /.scratch/ \n", encoding="utf-8"
        )

        with caplog.at_level(OUTPUT):
            assert self._init(project) == 0

        rules = _rule_lines((project / ".mcp-file-access").read_text(encoding="utf-8"))
        assert [r for r in rules if "scratch" in r.casefold()] == [rules[0]]
        assert rules[0].startswith("read-only")
        assert "overrides it" not in caplog.text
        assert "Gitignore: .scratch/ skipped" in caplog.text
        assert _scratch_lines(project / ".gitignore") == []

    def test_invalid_file_left_byte_identical(
        self,
        project: Path,
        mock_config: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An invalid rules file is untouched, exit 0, no .scratch/ line."""
        original = b"writable /.scratch/\n"
        (project / ".mcp-file-access").write_bytes(original)

        with caplog.at_level(OUTPUT):
            result = self._init(project)

        assert result == 0
        assert (project / ".mcp-file-access").read_bytes() == original
        assert _scratch_lines(project / ".gitignore") == []
        assert "File access rules: invalid (line 1: unknown level" in caplog.text
        assert "Gitignore: .scratch/ skipped (rules file invalid)" in caplog.text

    def test_rules_file_not_writable_exits_1_but_finishes_run(
        self,
        project: Path,
        mock_config: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A rules-file write failure exits 1 without aborting the run."""

        def _raise(*_args: object, **_kwargs: object) -> None:
            raise PermissionError("read-only")

        monkeypatch.setattr(f"{_MODULE}.write_repo_text", _raise)

        with caplog.at_level(logging.WARNING):
            result = self._init(project)

        assert result == 1
        assert "Failed to write .mcp-file-access" in caplog.text
        assert not (project / ".mcp-file-access").exists()
        assert _scratch_lines(project / ".gitignore") == []
        # Steps before and after ran
        assert (project / ".claude" / "skills" / "skills.md").exists()
        mock_config.assert_called_once()

    def test_result_is_valid_and_scratch_writable(
        self, project: Path, mock_config: MagicMock
    ) -> None:
        """After init the real API finds the rules valid and .scratch/ writable."""
        assert self._init(project) == 0

        assert validate_access_rules(project) == []
        assert not (project / ".scratch").exists()
        assert get_file_access(".scratch/x", project) == FileAccess.READ_WRITE
        # Gitignored now, so without the rule it would be hidden
        assert mcp_workspace.is_path_gitignored(".scratch/x", project)


class TestTemplateDrift:
    """The init template stays a subset of this repo's own rules file."""

    def test_every_template_rule_is_in_repo_rules_file(self) -> None:
        repo_rules = _parsed_rules(
            (REPO_ROOT / ".mcp-file-access").read_text(encoding="utf-8-sig")
        )
        for level, pattern in FILE_ACCESS_TEMPLATE_RULES:
            assert (level, pattern) in repo_rules, f"{level} {pattern}"
