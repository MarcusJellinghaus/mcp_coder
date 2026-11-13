"""Tests for `resolve_executable`."""

import os
import sys
from pathlib import Path

import pytest

from mcp_coder.utils.executable import (
    resolve_executable,
    venv_python,
    venv_search_path,
)


def _touch(path: Path, mode: int = 0o755) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    path.chmod(mode)
    return path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    path = tmp_path / "project"
    path.mkdir()
    return path


@pytest.fixture
def bin_dir(tmp_path: Path) -> Path:
    path = tmp_path / "bin"
    path.mkdir()
    return path


class TestPosix:
    """POSIX rules, independent of the host platform."""

    @pytest.fixture(autouse=True)
    def _posix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "platform", "linux")

    def test_project_relative_script(self, project_dir: Path) -> None:
        script = _touch(project_dir / "tools" / "lint")
        assert resolve_executable("tools/lint", project_dir) == str(script)

    @pytest.mark.skipif(
        sys.platform == "win32", reason="os.access(X_OK) is true on Windows"
    )
    def test_non_executable_file_not_found(self, project_dir: Path) -> None:
        _touch(project_dir / "tools" / "lint", mode=0o644)
        assert resolve_executable("tools/lint", project_dir) is None

    def test_bare_name_on_path(
        self, project_dir: Path, bin_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tool = _touch(bin_dir / "tool")
        monkeypatch.setenv("PATH", str(bin_dir))
        assert resolve_executable("tool", project_dir) == str(tool)

    def test_bare_name_in_cwd_only(
        self, project_dir: Path, bin_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _touch(project_dir / "tool")
        monkeypatch.chdir(project_dir)
        monkeypatch.setenv("PATH", str(bin_dir))
        assert resolve_executable("tool", project_dir) is None

    def test_relative_and_empty_path_entries_skipped(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _touch(project_dir / "tool")
        monkeypatch.chdir(project_dir)
        monkeypatch.setenv("PATH", os.pathsep.join([".", ""]))
        assert resolve_executable("tool", project_dir) is None

    def test_explicit_path_argument_used(
        self,
        project_dir: Path,
        bin_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        tool = _touch(bin_dir / "tool")
        other = tmp_path / "other"
        other.mkdir()
        _touch(other / "elsewhere")
        monkeypatch.setenv("PATH", str(other))
        assert resolve_executable("tool", project_dir, path=str(bin_dir)) == str(tool)
        assert resolve_executable("elsewhere", project_dir, path=str(bin_dir)) is None

    def test_missing(self, project_dir: Path, bin_dir: Path) -> None:
        assert resolve_executable("tools/lint", project_dir) is None
        assert resolve_executable("tool", project_dir, path=str(bin_dir)) is None


class TestWindows:
    """Windows rules, independent of the host platform."""

    @pytest.fixture(autouse=True)
    def _windows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")

    def test_mvnw_resolves_to_cmd(self, project_dir: Path) -> None:
        _touch(project_dir / "mvnw")
        script = _touch(project_dir / "mvnw.cmd")
        assert resolve_executable("./mvnw", project_dir) == str(script)

    def test_gradlew_resolves_to_bat(self, project_dir: Path) -> None:
        _touch(project_dir / "gradlew")
        script = _touch(project_dir / "gradlew.bat")
        assert resolve_executable("./gradlew", project_dir) == str(script)

    def test_extensionless_only_not_found(self, project_dir: Path) -> None:
        _touch(project_dir / "mvnw")
        assert resolve_executable("./mvnw", project_dir) is None

    @pytest.mark.parametrize(
        ("pathext", "winner"),
        [(".COM;.EXE;.BAT;.CMD", "x.exe"), (".CMD;.EXE", "x.cmd")],
    )
    def test_pathext_order(
        self,
        project_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        pathext: str,
        winner: str,
    ) -> None:
        monkeypatch.setenv("PATHEXT", pathext)
        _touch(project_dir / "x.exe")
        _touch(project_dir / "x.cmd")
        assert resolve_executable("./x", project_dir) == str(project_dir / winner)

    def test_pathext_default_when_unset(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PATHEXT")
        script = _touch(project_dir / "mvnw.cmd")
        assert resolve_executable("./mvnw", project_dir) == str(script)

    def test_bare_name_on_path(self, project_dir: Path, bin_dir: Path) -> None:
        npm = _touch(bin_dir / "npm.cmd")
        assert resolve_executable("npm", project_dir, path=str(bin_dir)) == str(npm)

    def test_known_extension_used_as_is(self, project_dir: Path) -> None:
        tool = _touch(project_dir / "tool.exe")
        _touch(project_dir / "tool.exe.cmd")
        assert resolve_executable("./tool.exe", project_dir) == str(tool)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows path shape")
    def test_backslash_path_is_path_like(self, project_dir: Path) -> None:
        tool = _touch(project_dir / "scripts" / "lint.exe")
        assert resolve_executable("scripts\\lint", project_dir) == str(tool)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows path shape")
    def test_windows_absolute_path(self, project_dir: Path, bin_dir: Path) -> None:
        tool = _touch(bin_dir / "tool.exe")
        assert resolve_executable(str(tool), project_dir) == str(tool)


class TestVenvSearchPath:
    """`venv_search_path` puts the project venv's bin dir first."""

    @pytest.mark.parametrize(
        ("platform", "subdir"), [("linux", "bin"), ("win32", "Scripts")]
    )
    def test_bin_dir_first_then_path(
        self,
        project_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        platform: str,
        subdir: str,
    ) -> None:
        monkeypatch.setattr(sys, "platform", platform)
        monkeypatch.setenv("PATH", "existing")
        expected = str(project_dir / ".venv" / subdir) + os.pathsep + "existing"
        assert venv_search_path(project_dir) == expected


class TestVenvPython:
    """`venv_python` finds the venv's interpreter."""

    @pytest.mark.parametrize(
        ("platform", "rel"),
        [("linux", Path("bin") / "python"), ("win32", Path("Scripts") / "python.exe")],
    )
    def test_interpreter_found(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        platform: str,
        rel: Path,
    ) -> None:
        monkeypatch.setattr(sys, "platform", platform)
        venv = tmp_path / ".venv"
        python = _touch(venv / rel)
        assert venv_python(venv) == python

    @pytest.mark.parametrize("platform", ["linux", "win32"])
    def test_missing_is_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, platform: str
    ) -> None:
        monkeypatch.setattr(sys, "platform", platform)
        assert venv_python(tmp_path / ".venv") is None

    def test_directory_is_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "platform", "linux")
        venv = tmp_path / ".venv"
        (venv / "bin" / "python").mkdir(parents=True)
        assert venv_python(venv) is None
