"""Tests for init command functionality."""

import argparse
import importlib.util
import logging
import tomllib
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.init import execute_init
from mcp_coder.cli.main import create_parser


def _load_setup_module() -> types.ModuleType:
    """Load setup.py as a module to access _copy_claude_resources."""
    setup_path = Path(__file__).resolve().parents[3] / "setup.py"
    spec = importlib.util.spec_from_file_location("setup_module", setup_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Prevent setup() from actually running
    with patch("setuptools.setup"):
        spec.loader.exec_module(mod)
    return mod


class TestInitCommand:
    """Tests for execute_init command handler."""

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_creates_config_success(
        self,
        mock_create: object,
        mock_path: object,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test successful config creation prints instructions."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init", just_skills=False, project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 0
        assert "Created default config at:" in caplog.text
        assert "Please update it" in caplog.text
        assert "Next steps:" in caplog.text
        assert "mcp-coder verify" in caplog.text
        assert "mcp-coder gh-tool define-labels" in caplog.text

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_config_already_exists(
        self,
        mock_create: object,
        mock_path: object,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test existing config prints already-exists message."""
        mock_create.return_value = False  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init", just_skills=False, project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 0
        assert "Config already exists:" in caplog.text

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_write_failure(
        self,
        mock_create: object,
        mock_path: object,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write failure returns exit code 1 with error message."""
        mock_create.side_effect = OSError("Permission denied")  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init", just_skills=False, project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 1
        assert "Failed to write config to" in caplog.text
        assert "Permission denied" in caplog.text

    def test_init_template_content_valid_toml_with_sections(
        self,
        tmp_path: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that created config is valid TOML with expected sections."""
        from pathlib import Path

        from mcp_coder.utils.user_config import (
            create_default_config,
            get_config_file_path,
        )

        config_path = Path(str(tmp_path)) / ".mcp_coder" / "config.toml"
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path",
            lambda: config_path,
        )

        created = create_default_config()

        assert created is True
        assert config_path.exists()

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        assert "github" in data
        assert "jenkins" in data
        assert "coordinator" in data


class TestBuildPyWithSkills:
    """Tests for setup.py _copy_claude_resources build hook."""

    def test_copy_claude_resources_creates_target_dirs(self, tmp_path: Path) -> None:
        """_copy_claude_resources copies skills/knowledge_base/agents."""
        setup_mod = _load_setup_module()

        # Create source .claude/ structure
        source = tmp_path / ".claude"
        for subdir in ["skills", "knowledge_base", "agents"]:
            d = source / subdir
            d.mkdir(parents=True)
            (d / "test.md").write_text(f"content of {subdir}")

        dest = tmp_path / "src" / "mcp_coder" / "resources" / "claude"

        # Monkeypatch __file__ in setup module to point at tmp_path
        with patch.object(setup_mod, "__file__", str(tmp_path / "setup.py")):
            setup_mod._copy_claude_resources()

        for subdir in ["skills", "knowledge_base", "agents"]:
            target_file = dest / subdir / "test.md"
            assert target_file.exists(), f"{subdir}/test.md should exist"
            assert target_file.read_text() == f"content of {subdir}"

    def test_copy_claude_resources_skips_claude_md(self, tmp_path: Path) -> None:
        """CLAUDE.md and settings.local.json are not copied."""
        setup_mod = _load_setup_module()

        source = tmp_path / ".claude"
        source.mkdir(parents=True)
        # These live directly in .claude/, not in subdirs — so they should NOT be copied
        (source / "CLAUDE.md").write_text("# Claude instructions")
        (source / "settings.local.json").write_text("{}")
        # Create one subdir so there's something to copy
        skills = source / "skills"
        skills.mkdir()
        (skills / "my_skill.md").write_text("skill content")

        dest = tmp_path / "src" / "mcp_coder" / "resources" / "claude"

        with patch.object(setup_mod, "__file__", str(tmp_path / "setup.py")):
            setup_mod._copy_claude_resources()

        assert not (dest / "CLAUDE.md").exists()
        assert not (dest / "settings.local.json").exists()
        assert (dest / "skills" / "my_skill.md").exists()

    def test_copy_claude_resources_overwrites_stale_build_artifacts(
        self, tmp_path: Path
    ) -> None:
        """Re-running copy replaces stale files (build artifact, not user files)."""
        setup_mod = _load_setup_module()

        source = tmp_path / ".claude"
        skills = source / "skills"
        skills.mkdir(parents=True)
        (skills / "skill.md").write_text("version 1")

        dest = tmp_path / "src" / "mcp_coder" / "resources" / "claude"
        # Pre-create stale artifact
        stale = dest / "skills"
        stale.mkdir(parents=True)
        (stale / "skill.md").write_text("stale version")

        with patch.object(setup_mod, "__file__", str(tmp_path / "setup.py")):
            setup_mod._copy_claude_resources()

        assert (dest / "skills" / "skill.md").read_text() == "version 1"


class TestInitParser:
    """Tests for init command parser flags."""

    def test_init_default_args(self) -> None:
        """init with no flags sets just_skills=False, project_dir=None."""
        parser = create_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"
        assert args.just_skills is False
        assert args.project_dir is None

    def test_init_just_skills_flag(self) -> None:
        """--just-skills sets just_skills=True."""
        parser = create_parser()
        args = parser.parse_args(["init", "--just-skills"])
        assert args.just_skills is True

    def test_init_project_dir_flag(self) -> None:
        """--project-dir sets project_dir to given path."""
        parser = create_parser()
        args = parser.parse_args(["init", "--project-dir", "/tmp/foo"])
        assert args.project_dir == "/tmp/foo"

    def test_init_both_flags(self) -> None:
        """--just-skills --project-dir /tmp/foo sets both."""
        parser = create_parser()
        args = parser.parse_args(["init", "--just-skills", "--project-dir", "/tmp/foo"])
        assert args.just_skills is True
        assert args.project_dir == "/tmp/foo"
