"""Tests for find_repo_section_by_url in user_config module."""

from pathlib import Path

import pytest

from mcp_coder.utils.user_config import find_repo_section_by_url


class TestFindRepoSectionByUrl:
    """Tests for find_repo_section_by_url function."""

    def _write_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: str
    ) -> None:
        """Helper to write a config file and monkeypatch the path."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(content, encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

    def test_find_repo_section_exact_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config has repo_url matching input exactly → returns section name."""
        self._write_config(
            tmp_path,
            monkeypatch,
            '[coordinator.repos.my_repo]\nrepo_url = "https://github.com/org/repo.git"\n',
        )

        result = find_repo_section_by_url("https://github.com/org/repo.git")

        assert result == "coordinator.repos.my_repo"

    def test_find_repo_section_normalizes_git_suffix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config URL has .git, input doesn't (and vice versa) → match."""
        self._write_config(
            tmp_path,
            monkeypatch,
            '[coordinator.repos.my_repo]\nrepo_url = "https://github.com/org/repo.git"\n',
        )

        # Input without .git matches config with .git
        assert (
            find_repo_section_by_url("https://github.com/org/repo")
            == "coordinator.repos.my_repo"
        )

        # Now test vice versa: config without .git, input with .git
        self._write_config(
            tmp_path,
            monkeypatch,
            '[coordinator.repos.my_repo]\nrepo_url = "https://github.com/org/repo"\n',
        )
        assert (
            find_repo_section_by_url("https://github.com/org/repo.git")
            == "coordinator.repos.my_repo"
        )

    def test_find_repo_section_normalizes_trailing_slash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config URL has trailing /, input doesn't → match."""
        self._write_config(
            tmp_path,
            monkeypatch,
            '[coordinator.repos.my_repo]\nrepo_url = "https://github.com/org/repo/"\n',
        )

        assert (
            find_repo_section_by_url("https://github.com/org/repo")
            == "coordinator.repos.my_repo"
        )

    def test_find_repo_section_no_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Input URL not in config → returns None."""
        self._write_config(
            tmp_path,
            monkeypatch,
            '[coordinator.repos.my_repo]\nrepo_url = "https://github.com/org/repo.git"\n',
        )

        result = find_repo_section_by_url("https://github.com/org/other-repo")

        assert result is None

    def test_find_repo_section_empty_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No [coordinator] section → returns None."""
        self._write_config(
            tmp_path,
            monkeypatch,
            '[github]\ntoken = "ghp_test"\n',
        )

        result = find_repo_section_by_url("https://github.com/org/repo")

        assert result is None

    def test_find_repo_section_multiple_repos_returns_correct(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two repos in config, matches the right one."""
        self._write_config(
            tmp_path,
            monkeypatch,
            (
                "[coordinator.repos.first_repo]\n"
                'repo_url = "https://github.com/org/first.git"\n\n'
                "[coordinator.repos.second_repo]\n"
                'repo_url = "https://github.com/org/second.git"\n'
            ),
        )

        assert (
            find_repo_section_by_url("https://github.com/org/second")
            == "coordinator.repos.second_repo"
        )
        assert (
            find_repo_section_by_url("https://github.com/org/first")
            == "coordinator.repos.first_repo"
        )
