"""Tests for init command functionality."""

import argparse
import importlib.util
import logging
import tomllib
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.init import (
    DEPLOY_SUBDIRS,
    _deploy_skills,
    _find_claude_source_dir,
    _has_all_subdirs,
    execute_init,
)
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

    @patch("mcp_coder.cli.commands.init._deploy_skills", return_value=(0, 0))
    @patch("mcp_coder.cli.commands.init._find_claude_source_dir")
    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_creates_config_success(
        self,
        mock_create: object,
        mock_path: object,
        mock_find: object,
        mock_deploy: object,
        caplog: pytest.LogCaptureFixture,
        tmp_path: Path,
    ) -> None:
        """Test successful config creation prints instructions."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        mock_find.return_value = tmp_path / "source"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init", just_skills=False, project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 0
        assert "Created default config at:" in caplog.text
        assert "Please update it" in caplog.text
        assert "Next steps:" in caplog.text
        assert "mcp-coder verify" in caplog.text
        assert "mcp-coder gh-tool define-labels" in caplog.text

    @patch("mcp_coder.cli.commands.init._deploy_skills", return_value=(0, 0))
    @patch("mcp_coder.cli.commands.init._find_claude_source_dir")
    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_config_already_exists(
        self,
        mock_create: object,
        mock_path: object,
        mock_find: object,
        mock_deploy: object,
        caplog: pytest.LogCaptureFixture,
        tmp_path: Path,
    ) -> None:
        """Test existing config prints already-exists message."""
        mock_create.return_value = False  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        mock_find.return_value = tmp_path / "source"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init", just_skills=False, project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 0
        assert "Config already exists:" in caplog.text

    @patch("mcp_coder.cli.commands.init._deploy_skills", return_value=(0, 0))
    @patch("mcp_coder.cli.commands.init._find_claude_source_dir")
    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_write_failure(
        self,
        mock_create: object,
        mock_path: object,
        mock_find: object,
        mock_deploy: object,
        caplog: pytest.LogCaptureFixture,
        tmp_path: Path,
    ) -> None:
        """Test write failure returns exit code 1 with error message."""
        mock_create.side_effect = OSError("Permission denied")  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        mock_find.return_value = tmp_path / "source"  # type: ignore[attr-defined]
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


class TestFindClaudeSourceDir:
    """Tests for _find_claude_source_dir() resolver."""

    @staticmethod
    def _make_claude_dir(base: Path) -> Path:
        """Create a directory with all required DEPLOY_SUBDIRS."""
        for name in DEPLOY_SUBDIRS:
            (base / name).mkdir(parents=True, exist_ok=True)
        return base

    def test_finds_via_importlib_resources(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns importlib.resources path when resources/claude/skills/ exists."""
        pkg_root = tmp_path / "pkg"
        pkg_root.mkdir()
        claude_dir = pkg_root / "resources" / "claude"
        self._make_claude_dir(claude_dir)

        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.files",
            lambda _name: pkg_root,
        )

        result = _find_claude_source_dir()
        assert result == claude_dir

    def test_falls_back_to_repo_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Falls back to repo-root .claude/ when importlib path is empty."""
        # Make importlib path invalid
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.files",
            lambda _name: tmp_path / "nonexistent",
        )

        # Create a fake repo root with .claude/
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        claude_dir = repo_root / ".claude"
        self._make_claude_dir(claude_dir)

        # Place a fake __file__ inside the repo
        fake_file = repo_root / "src" / "mcp_coder" / "cli" / "commands" / "init.py"
        fake_file.parent.mkdir(parents=True)
        fake_file.touch()

        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.Path.__file__",
            str(fake_file),
            raising=False,
        )
        # We need to monkeypatch __file__ in the module
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.__file__",
            str(fake_file),
        )

        result = _find_claude_source_dir()
        assert result == claude_dir

    def test_exits_when_both_fail(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Calls sys.exit(1) when neither location has the required subdirs."""
        # Make importlib path invalid
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.files",
            lambda _name: tmp_path / "nonexistent",
        )

        # Point __file__ at a location with no .claude/ ancestor
        fake_file = tmp_path / "isolated" / "init.py"
        fake_file.parent.mkdir(parents=True)
        fake_file.touch()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.__file__",
            str(fake_file),
        )

        with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc_info:
            _find_claude_source_dir()

        assert exc_info.value.code == 1
        assert "skills/" in caplog.text
        assert "knowledge_base/" in caplog.text
        assert "agents/" in caplog.text
        assert "pip install --force-reinstall mcp-coder" in caplog.text

    def test_requires_all_subdirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Directory missing any of skills/knowledge_base/agents is rejected."""
        # Make importlib path have only 2 of 3 subdirs
        pkg_root = tmp_path / "pkg"
        pkg_root.mkdir()
        claude_dir = pkg_root / "resources" / "claude"
        claude_dir.mkdir(parents=True)
        (claude_dir / "skills").mkdir()
        (claude_dir / "knowledge_base").mkdir()
        # agents/ is missing

        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.files",
            lambda _name: pkg_root,
        )

        # Point __file__ at a location with no .claude/ ancestor
        fake_file = tmp_path / "isolated" / "init.py"
        fake_file.parent.mkdir(parents=True)
        fake_file.touch()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init.__file__",
            str(fake_file),
        )

        with pytest.raises(SystemExit) as exc_info:
            _find_claude_source_dir()

        assert exc_info.value.code == 1


class TestHasAllSubdirs:
    """Tests for _has_all_subdirs() helper."""

    def test_returns_true_when_all_present(self, tmp_path: Path) -> None:
        for name in DEPLOY_SUBDIRS:
            (tmp_path / name).mkdir()
        assert _has_all_subdirs(tmp_path) is True

    def test_returns_false_when_missing(self, tmp_path: Path) -> None:
        (tmp_path / "skills").mkdir()
        assert _has_all_subdirs(tmp_path) is False

    def test_returns_false_for_nonexistent_dir(self, tmp_path: Path) -> None:
        assert _has_all_subdirs(tmp_path / "nope") is False


class TestDeploySkills:
    """Tests for _deploy_skills() function."""

    @staticmethod
    def _make_source(base: Path) -> Path:
        """Create a source dir with sample files in all DEPLOY_SUBDIRS."""
        for name in DEPLOY_SUBDIRS:
            d = base / name
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{name}.md").write_text(f"content of {name}")
        return base

    def test_deploy_to_empty_project(self, tmp_path: Path) -> None:
        """All files deployed when target .claude/ doesn't exist."""
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        project.mkdir()

        added, skipped = _deploy_skills(source, project)

        assert added == 3
        assert skipped == 0
        for name in DEPLOY_SUBDIRS:
            assert (project / ".claude" / name / f"{name}.md").exists()

    def test_never_overwrites_existing_files(self, tmp_path: Path) -> None:
        """Existing files are skipped, not overwritten."""
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        target = project / ".claude" / "skills"
        target.mkdir(parents=True)
        (target / "skills.md").write_text("original content")

        _deploy_skills(source, project)

        assert (target / "skills.md").read_text() == "original content"

    def test_returns_correct_counts(self, tmp_path: Path) -> None:
        """Returns (added, skipped) counts matching actual operations."""
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        # Pre-create one file to be skipped
        target = project / ".claude" / "skills"
        target.mkdir(parents=True)
        (target / "skills.md").write_text("existing")

        added, skipped = _deploy_skills(source, project)

        assert added == 2
        assert skipped == 1

    def test_skipped_files_emit_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Each skipped file produces a warning log message."""
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "project"
        target = project / ".claude" / "skills"
        target.mkdir(parents=True)
        (target / "skills.md").write_text("existing")

        with caplog.at_level(logging.WARNING):
            _deploy_skills(source, project)

        assert "Skipped (exists):" in caplog.text

    def test_creates_intermediate_directories(self, tmp_path: Path) -> None:
        """Creates nested dirs (e.g., skills/plan_review/) as needed."""
        source = tmp_path / "source"
        nested = source / "skills" / "plan_review"
        nested.mkdir(parents=True)
        (nested / "deep.md").write_text("nested content")
        # Create other required subdirs (empty)
        for name in ("knowledge_base", "agents"):
            (source / name).mkdir(parents=True, exist_ok=True)

        project = tmp_path / "project"
        project.mkdir()

        _deploy_skills(source, project)

        assert (project / ".claude" / "skills" / "plan_review" / "deep.md").exists()
        assert (
            project / ".claude" / "skills" / "plan_review" / "deep.md"
        ).read_text() == "nested content"

    def test_handles_missing_source_subdir(self, tmp_path: Path) -> None:
        """Gracefully handles source dir missing a subdir (e.g., no agents/)."""
        source = tmp_path / "source"
        # Only create skills/ and knowledge_base/, skip agents/
        for name in ("skills", "knowledge_base"):
            d = source / name
            d.mkdir(parents=True)
            (d / f"{name}.md").write_text(f"content of {name}")

        project = tmp_path / "project"
        project.mkdir()

        added, skipped = _deploy_skills(source, project)

        assert added == 2
        assert skipped == 0


class TestExecuteInitWithDeploy:
    """Tests for execute_init() with deploy integration."""

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
    def test_default_creates_config_and_deploys(
        self,
        mock_create: object,
        mock_path: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Default init creates config AND deploys skills."""
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

        result = execute_init(args)

        assert result == 0
        # Skills deployed
        assert (project / ".claude" / "skills" / "skills.md").exists()
        # Config creation was called
        mock_create.assert_called_once()  # type: ignore[attr-defined]

    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_just_skills_skips_config(
        self,
        mock_create: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """--just-skills deploys skills but does NOT create config."""
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
        # Skills deployed
        assert (project / ".claude" / "skills" / "skills.md").exists()
        # Config NOT created
        mock_create.assert_not_called()  # type: ignore[attr-defined]

    def test_project_dir_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """--project-dir targets the specified directory."""
        source = self._make_source(tmp_path / "source")
        project = tmp_path / "target_project"
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
        assert (project / ".claude" / "skills" / "skills.md").exists()

    def test_deploy_failure_exits_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Exit 1 when source cannot be found (from _find_claude_source_dir)."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: (_ for _ in ()).throw(SystemExit(1)),
        )
        args = argparse.Namespace(command="init", just_skills=False, project_dir=None)

        with pytest.raises(SystemExit) as exc_info:
            execute_init(args)

        assert exc_info.value.code == 1

    def test_missing_project_dir_exits_1(self, tmp_path: Path) -> None:
        """--project-dir pointing at a non-existent path exits 1."""
        args = argparse.Namespace(
            command="init",
            just_skills=False,
            project_dir=str(tmp_path / "nonexistent"),
        )

        result = execute_init(args)

        assert result == 1

    @patch("mcp_coder.cli.commands.init._deploy_skills")
    def test_self_deploy_is_skipped(
        self,
        mock_deploy: object,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When source_dir.resolve() == target_base.resolve(), skip deploy."""
        project = tmp_path / "project"
        project.mkdir()
        # source_dir IS the target .claude/ dir
        source = project / ".claude"
        source.mkdir()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.init._find_claude_source_dir",
            lambda: source,
        )
        args = argparse.Namespace(
            command="init", just_skills=True, project_dir=str(project)
        )

        with caplog.at_level(logging.INFO, logger="mcp_coder.cli.commands.init"):
            result = execute_init(args)

        assert result == 0
        mock_deploy.assert_not_called()  # type: ignore[attr-defined]
        assert "Skipping deploy: running inside mcp-coder source repo" in caplog.text
