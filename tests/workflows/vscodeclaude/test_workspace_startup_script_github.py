"""Test startup script generation for GitHub override installs."""

from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.workspace import create_startup_script


class TestCreateStartupScriptFromGithub:
    """Test from_github parameter for GitHub override installs."""

    @staticmethod
    def _write_pyproject(
        tmp_path: Path,
        packages: list[str] | None = None,
        packages_no_deps: list[str] | None = None,
    ) -> None:
        """Write a pyproject.toml with [tool.mcp-coder.from-github] section."""
        lines = ['[project]\nname = "test-project"\nversion = "0.1.0"\n']
        if packages is not None or packages_no_deps is not None:
            lines.append("[tool.mcp-coder.from-github]\n")
            if packages is not None:
                items = ", ".join(f'"{p}"' for p in packages)
                lines.append(f"packages = [{items}]\n")
            if packages_no_deps is not None:
                items = ", ".join(f'"{p}"' for p in packages_no_deps)
                lines.append(f"packages-no-deps = [{items}]\n")
        (tmp_path / "pyproject.toml").write_text("\n".join(lines), encoding="utf-8")

    def test_from_github_injects_install_commands(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """from_github=True injects uv pip install commands from pyproject.toml."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )
        self._write_pyproject(
            tmp_path,
            packages=[
                "pkg1 @ git+https://github.com/org/pkg1.git",
                "pkg2 @ git+https://github.com/org/pkg2.git",
            ],
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            from_github=True,
        )

        content = script_path.read_text(encoding="utf-8")
        # With-deps install
        assert (
            'uv pip install "pkg1 @ git+https://github.com/org/pkg1.git" "pkg2 @ git+https://github.com/org/pkg2.git"'
            in content
        )
        # No-deps install
        assert (
            'uv pip install --no-deps "pkg3 @ git+https://github.com/org/pkg3.git"'
            in content
        )
        # Restore editable after github installs
        assert content.count("uv pip install -e . --no-deps") >= 2
        # Marker comment
        assert "GitHub override installs" in content

    def test_from_github_false_no_github_section(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """from_github=False does not inject GitHub install commands."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            from_github=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "GitHub override" not in content

    def test_from_github_missing_config_section(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """from_github=True with no [tool.mcp-coder.from-github] degrades gracefully."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )
        # pyproject.toml without the from-github section
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\n', encoding="utf-8"
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            from_github=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "GitHub override" not in content

    def test_from_github_empty_packages(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """from_github=True with empty package lists produces no install commands."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )
        self._write_pyproject(tmp_path, packages=[], packages_no_deps=[])

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            from_github=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "GitHub override" not in content

    def test_from_github_only_packages(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Only packages (no packages-no-deps) generates with-deps install + restore."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )
        self._write_pyproject(
            tmp_path,
            packages=["pkg1 @ git+https://github.com/org/pkg1.git"],
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            from_github=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "GitHub override installs" in content
        assert 'uv pip install "pkg1 @ git+https://github.com/org/pkg1.git"' in content
        assert 'uv pip install --no-deps "pkg' not in content
        # Restore editable
        assert content.count("uv pip install -e . --no-deps") >= 2

    def test_from_github_only_packages_no_deps(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Only packages-no-deps generates no-deps install + restore."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )
        self._write_pyproject(
            tmp_path,
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            from_github=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "GitHub override installs" in content
        assert (
            'uv pip install --no-deps "pkg3 @ git+https://github.com/org/pkg3.git"'
            in content
        )
        # Restore editable
        assert content.count("uv pip install -e . --no-deps") >= 2

    def test_from_github_missing_pyproject_toml(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """from_github=True with no pyproject.toml at all degrades gracefully."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )
        # Deliberately do NOT create pyproject.toml in tmp_path

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            from_github=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "GitHub override" not in content
        assert "uv pip install" not in content or "uv pip install -e ." in content
