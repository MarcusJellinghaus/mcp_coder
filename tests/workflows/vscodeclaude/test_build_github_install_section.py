"""Regression test for _build_github_install_section output format."""

from pathlib import Path

from mcp_coder.workflows.vscodeclaude.workspace import _build_github_install_section


def _write_pyproject(
    tmp_path: Path,
    packages: list[str] | None = None,
    packages_no_deps: list[str] | None = None,
) -> None:
    """Write a pyproject.toml with [tool.mcp-coder.install-from-github] section."""
    lines = ['[project]\nname = "test-project"\nversion = "0.1.0"\n']
    if packages is not None or packages_no_deps is not None:
        lines.append("[tool.mcp-coder.install-from-github]\n")
        if packages is not None:
            items = ", ".join(f'"{p}"' for p in packages)
            lines.append(f"packages = [{items}]\n")
        if packages_no_deps is not None:
            items = ", ".join(f'"{p}"' for p in packages_no_deps)
            lines.append(f"packages-no-deps = [{items}]\n")
    (tmp_path / "pyproject.toml").write_text("\n".join(lines), encoding="utf-8")


class TestBuildGithubInstallSection:
    """Tests for _build_github_install_section output format."""

    def test_output_contains_install_lines_for_packages(self, tmp_path: Path) -> None:
        """Output contains uv pip install for each package from config."""
        _write_pyproject(
            tmp_path,
            packages=[
                "pkg1 @ git+https://github.com/org/pkg1.git",
                "pkg2 @ git+https://github.com/org/pkg2.git",
            ],
        )
        result = _build_github_install_section(tmp_path)
        assert (
            'uv pip install "pkg1 @ git+https://github.com/org/pkg1.git" '
            '"pkg2 @ git+https://github.com/org/pkg2.git"'
        ) in result
        assert "--no-deps" not in result.split("\n")[2]

    def test_output_contains_no_deps_for_packages_no_deps(self, tmp_path: Path) -> None:
        """Output contains uv pip install --no-deps for packages-no-deps entries."""
        _write_pyproject(
            tmp_path,
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )
        result = _build_github_install_section(tmp_path)
        assert (
            'uv pip install --no-deps "pkg3 @ git+https://github.com/org/pkg3.git"'
            in result
        )

    def test_output_contains_editable_restore(self, tmp_path: Path) -> None:
        """Output contains uv pip install -e . --no-deps to restore editable install."""
        _write_pyproject(
            tmp_path,
            packages=["pkg1 @ git+https://github.com/org/pkg1.git"],
        )
        result = _build_github_install_section(tmp_path)
        assert "uv pip install -e . --no-deps" in result

    def test_empty_config_returns_empty_string(self, tmp_path: Path) -> None:
        """No packages configured returns empty string."""
        _write_pyproject(tmp_path, packages=[], packages_no_deps=[])
        result = _build_github_install_section(tmp_path)
        assert result == ""

    def test_missing_pyproject_returns_empty_string(self, tmp_path: Path) -> None:
        """No pyproject.toml returns empty string."""
        result = _build_github_install_section(tmp_path)
        assert result == ""
