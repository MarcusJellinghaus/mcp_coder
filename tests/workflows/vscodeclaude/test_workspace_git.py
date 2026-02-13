"""Test git operations for VSCode Claude workspace."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.subprocess_runner import CommandResult
from mcp_coder.workflows.vscodeclaude.workspace import setup_git_repo


class TestGitOperations:
    """Test git clone/checkout/pull operations."""

    def test_setup_git_repo_clone_new(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clones when folder is empty."""

        commands: list[Any] = []

        def mock_execute(cmd: Any, options: Any = None) -> CommandResult:
            commands.append(cmd)
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        def mock_checkout_branch(branch: str, repo_path: Path) -> bool:
            return True

        def mock_fetch_remote(repo_path: Path) -> bool:
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.checkout_branch",
            mock_checkout_branch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.fetch_remote",
            mock_fetch_remote,
        )

        folder = tmp_path / "new_repo"
        folder.mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", "main")

        # Should have clone, checkout, pull
        assert any("clone" in str(c) for c in commands)

    def test_setup_git_repo_existing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Checkout and pull when .git exists."""

        commands: list[Any] = []

        def mock_execute(cmd: Any, options: Any = None) -> CommandResult:
            commands.append(cmd)
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        def mock_checkout_branch(branch: str, repo_path: Path) -> bool:
            return True

        def mock_fetch_remote(repo_path: Path) -> bool:
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.checkout_branch",
            mock_checkout_branch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.fetch_remote",
            mock_fetch_remote,
        )

        # Create folder with .git
        folder = tmp_path / "existing_repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", "feature-branch")

        # Should NOT clone, but should pull
        assert not any("clone" in str(c) for c in commands)
        assert any("pull" in str(c) for c in commands)

    def test_setup_git_repo_uses_main_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Uses main branch when branch_name is None."""

        commands: list[Any] = []
        checkout_calls: list[tuple[str, Path]] = []

        def mock_execute(cmd: Any, options: Any = None) -> CommandResult:
            commands.append(cmd)
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        def mock_checkout_branch(branch: str, repo_path: Path) -> bool:
            checkout_calls.append((branch, repo_path))
            return True

        def mock_fetch_remote(repo_path: Path) -> bool:
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.checkout_branch",
            mock_checkout_branch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.fetch_remote",
            mock_fetch_remote,
        )

        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", None)

        # Verify checkout_branch was called with "main"
        assert len(checkout_calls) == 1
        assert checkout_calls[0][0] == "main"

    def test_setup_git_repo_folder_with_content_no_git(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises error when folder has content but no .git."""

        def mock_execute(cmd: Any, options: Any = None) -> CommandResult:
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.execute_subprocess",
            mock_execute,
        )

        folder = tmp_path / "has_content"
        folder.mkdir()
        (folder / "somefile.txt").write_text("content")

        with pytest.raises(ValueError, match="not a git repository"):
            setup_git_repo(folder, "https://github.com/owner/repo.git", "main")

    def test_setup_git_repo_corrupted_git_reclones(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Deletes and reclones when .git exists but is corrupted."""

        commands: list[Any] = []
        rmtree_called: list[Path] = []

        def mock_execute(cmd: Any, options: Any = None) -> CommandResult:
            commands.append(cmd)
            # Simulate corrupted git repo - rev-parse fails
            if "rev-parse" in str(cmd):
                return CommandResult(
                    return_code=128,
                    stdout="",
                    stderr="fatal: not a git repo",
                    timed_out=False,
                )
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        def mock_checkout_branch(branch: str, repo_path: Path) -> bool:
            return True

        def mock_fetch_remote(repo_path: Path) -> bool:
            return True

        def mock_rmtree(path: Path, **kwargs: Any) -> None:
            rmtree_called.append(path)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.checkout_branch",
            mock_checkout_branch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.fetch_remote",
            mock_fetch_remote,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.shutil.rmtree", mock_rmtree
        )

        # Create folder with corrupted .git
        folder = tmp_path / "corrupted_repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", "main")

        # Should have called rmtree to delete corrupted folder
        assert len(rmtree_called) == 1
        assert rmtree_called[0] == folder

        # Should have cloned after deleting
        assert any("clone" in str(c) for c in commands)
