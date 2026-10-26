"""Test git operations for VSCode Claude workspace."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.subprocess_runner import CalledProcessError
from mcp_coder.workflows.vscodeclaude.workspace import setup_git_repo

_MODULE = "mcp_coder.workflows.vscodeclaude.workspace"
_URL = "https://github.com/owner/repo.git"


class _GitFakes:
    """Records calls to the shim functions patched into workspace.py."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.clone_args: list[tuple[str, Path]] = []
        self.checkout_args: list[tuple[str, Path]] = []
        self.is_repo = True
        self.clone_error: Exception | None = None
        self.checkout_ok = True
        self.fetch_ok = True
        self.pull_result: dict[str, Any] = {
            "success": True,
            "error": None,
            "returncode": 0,
            "stderr": "",
        }

    def is_git_repository(self, project_dir: Path) -> bool:
        self.calls.append("is_git_repository")
        return self.is_repo

    def clone_repo(self, url: str, target_path: Path) -> None:
        self.calls.append("clone_repo")
        self.clone_args.append((url, target_path))
        if self.clone_error is not None:
            raise self.clone_error

    def checkout_branch(self, branch: str, repo_path: Path) -> bool:
        self.calls.append("checkout_branch")
        self.checkout_args.append((branch, repo_path))
        return self.checkout_ok

    def fetch_remote(self, repo_path: Path) -> bool:
        self.calls.append("fetch_remote")
        return self.fetch_ok

    def pull(self, project_dir: Path) -> dict[str, Any]:
        self.calls.append("pull")
        return self.pull_result


@pytest.fixture
def git_fakes(monkeypatch: pytest.MonkeyPatch) -> _GitFakes:
    """Patch the shim functions in workspace.py with recording fakes."""
    fakes = _GitFakes()
    for name in (
        "is_git_repository",
        "clone_repo",
        "checkout_branch",
        "fetch_remote",
        "pull",
    ):
        monkeypatch.setattr(f"{_MODULE}.{name}", getattr(fakes, name))
    return fakes


class TestGitOperations:
    """Test git clone/checkout/pull operations."""

    def test_setup_git_repo_clone_new(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """Clones when folder is empty, then checkout/fetch/pull."""
        folder = tmp_path / "new_repo"
        folder.mkdir()

        setup_git_repo(folder, _URL, "main")

        assert git_fakes.clone_args == [(_URL, folder)]
        assert git_fakes.calls == [
            "clone_repo",
            "checkout_branch",
            "fetch_remote",
            "pull",
        ]

    def test_setup_git_repo_existing(
        self, tmp_path: Path, git_fakes: _GitFakes, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid .git: no delete, no clone; checkout, fetch and pull."""
        rmtree_called: list[Path] = []
        monkeypatch.setattr(
            f"{_MODULE}.shutil.rmtree",
            lambda path, **kwargs: rmtree_called.append(path),
        )
        folder = tmp_path / "existing_repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, _URL, "feature-branch")

        assert not rmtree_called
        assert "clone_repo" not in git_fakes.calls
        assert git_fakes.checkout_args == [("feature-branch", folder)]
        assert git_fakes.calls[-2:] == ["fetch_remote", "pull"]

    def test_setup_git_repo_uses_main_default(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """Uses main branch when branch_name is None."""
        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, _URL, None)

        assert git_fakes.checkout_args == [("main", folder)]

    def test_setup_git_repo_folder_with_content_no_git(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """Raises error when folder has content but no .git."""
        folder = tmp_path / "has_content"
        folder.mkdir()
        (folder / "somefile.txt").write_text("content")

        with pytest.raises(ValueError, match="not a git repository"):
            setup_git_repo(folder, _URL, "main")

        assert "clone_repo" not in git_fakes.calls

    def test_setup_git_repo_corrupted_git_reclones(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """Deletes folder contents and reclones when .git is not a valid repo."""
        git_fakes.is_repo = False
        folder = tmp_path / "corrupted_repo"
        folder.mkdir()
        (folder / ".git").mkdir()
        (folder / "stale.txt").write_text("stale")

        setup_git_repo(folder, _URL, "main")

        assert folder.exists()
        assert not any(folder.iterdir())
        assert git_fakes.clone_args == [(_URL, folder)]
        assert git_fakes.calls == [
            "is_git_repository",
            "clone_repo",
            "checkout_branch",
            "fetch_remote",
            "pull",
        ]

    def test_setup_git_repo_clone_failure(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """A clone ValueError becomes CalledProcessError without chaining."""
        git_fakes.clone_error = ValueError("Failed to clone 'https://x': boom")
        folder = tmp_path / "new_repo"
        folder.mkdir()

        with pytest.raises(CalledProcessError) as exc_info:
            setup_git_repo(folder, _URL, "main")

        assert exc_info.value.cmd == "clone_repo"
        assert exc_info.value.returncode == 1
        assert exc_info.value.output == "Failed to clone 'https://x': boom"
        assert exc_info.value.__cause__ is None
        assert exc_info.value.__suppress_context__ is True
        assert "checkout_branch" not in git_fakes.calls

    def test_setup_git_repo_checkout_failure(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """Failed checkout raises CalledProcessError(cmd='checkout_branch')."""
        git_fakes.checkout_ok = False
        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        with pytest.raises(CalledProcessError) as exc_info:
            setup_git_repo(folder, _URL, "feature")

        assert exc_info.value.cmd == "checkout_branch"
        assert exc_info.value.output == "Failed to checkout branch 'feature'"
        assert "fetch_remote" not in git_fakes.calls

    def test_setup_git_repo_fetch_failure(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """Failed fetch raises CalledProcessError(cmd='fetch_remote')."""
        git_fakes.fetch_ok = False
        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        with pytest.raises(CalledProcessError) as exc_info:
            setup_git_repo(folder, _URL, "main")

        assert exc_info.value.cmd == "fetch_remote"
        assert "pull" not in git_fakes.calls

    def test_setup_git_repo_pull_failure(
        self, tmp_path: Path, git_fakes: _GitFakes
    ) -> None:
        """Failed pull raises CalledProcessError(cmd='pull') with error/stderr."""
        git_fakes.pull_result = {
            "success": False,
            "error": "git pull failed (exit 1)",
            "returncode": 1,
            "stderr": "fatal: conflict",
        }
        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        with pytest.raises(CalledProcessError) as exc_info:
            setup_git_repo(folder, _URL, "main")

        assert exc_info.value.cmd == "pull"
        assert exc_info.value.output == "git pull failed (exit 1)"
        assert exc_info.value.stderr == "fatal: conflict"
