"""Tests for verify_config function from user_config module."""

from pathlib import Path

import pytest

from mcp_coder.utils.user_config import verify_config


class TestVerifyConfig:
    """Tests for verify_config function."""

    def _clear_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Clear all env vars that verify_config checks."""
        for var in (
            "GITHUB_TOKEN",
            "JENKINS_URL",
            "JENKINS_USER",
            "JENKINS_TOKEN",
        ):
            monkeypatch.delenv(var, raising=False)

    def test_verify_config_missing_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No config file -> warning status, has_error=False, expected path shown."""
        config_file = tmp_path / "nonexistent" / "config.toml"
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        assert result["has_error"] is False
        entries = result["entries"]
        assert entries[0]["status"] == "warning"
        assert entries[0]["value"] == "not found"
        assert entries[1]["label"] == "Expected path"
        assert str(config_file) in entries[1]["value"]
        assert entries[2]["label"] == "Hint"
        assert "mcp-coder init" in entries[2]["value"]

    def test_verify_config_invalid_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bad TOML -> error status, has_error=True, parse error in value."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('key = "unclosed\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        result = verify_config()

        assert result["has_error"] is True
        entries = result["entries"]
        assert entries[0]["status"] == "error"
        assert entries[0]["value"] == "invalid TOML"
        assert entries[1]["label"] == "Parse error"
        assert entries[1]["status"] == "error"
        assert "TOML parse error" in entries[1]["value"]

    def test_verify_config_valid_with_all_sections(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Full config -> ok status for each section, correct summaries."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[llm]
default_provider = "langchain"

[github]
token = "ghp_test"

[jenkins]
server_url = "http://jenkins"
username = "admin"
api_token = "token123"

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/test/repo.git"

[coordinator.repos.mcp_workspace]
repo_url = "https://github.com/test/workspace.git"
""",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        assert result["has_error"] is False
        labels = [e["label"] for e in result["entries"]]
        assert "Config file" in labels
        assert "[llm]" in labels
        assert "[github]" in labels
        assert "[jenkins]" in labels
        assert "[coordinator]" in labels

        # Check statuses are all ok
        for entry in result["entries"]:
            assert entry["status"] == "ok"

        # Check specific values
        by_label = {e["label"]: e for e in result["entries"]}
        assert "default_provider = langchain" in by_label["[llm]"]["value"]
        assert "token configured" in by_label["[github]"]["value"]
        assert "(config.toml)" in by_label["[github]"]["value"]
        assert "server_url configured" in by_label["[jenkins]"]["value"]
        assert "2 repos configured" in by_label["[coordinator]"]["value"]

    def test_verify_config_env_var_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No config file section but env var set -> section shows (env var)."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")  # empty valid TOML
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)
        monkeypatch.setenv("GITHUB_TOKEN", "env_token_value")

        result = verify_config()

        assert result["has_error"] is False
        by_label = {e["label"]: e for e in result["entries"]}
        assert "[github]" in by_label
        assert "(env var)" in by_label["[github]"]["value"]
        assert "config.toml" not in by_label["[github]"]["value"]

    def test_verify_config_dual_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env var AND config both set -> (env var, also in config.toml)."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[github]\ntoken = "ghp_config_token"\n', encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)
        monkeypatch.setenv("GITHUB_TOKEN", "env_token_value")

        result = verify_config()

        by_label = {e["label"]: e for e in result["entries"]}
        assert "[github]" in by_label
        assert "(env var, also in config.toml)" in by_label["[github]"]["value"]

    def test_verify_config_coordinator_repo_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """3 repos -> '3 repos configured'."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[coordinator.repos.repo1]
repo_url = "https://example.com/repo1.git"

[coordinator.repos.repo2]
repo_url = "https://example.com/repo2.git"

[coordinator.repos.repo3]
repo_url = "https://example.com/repo3.git"
""",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        by_label = {e["label"]: e for e in result["entries"]}
        assert "[coordinator]" in by_label
        assert "3 repos configured" in by_label["[coordinator]"]["value"]

    def test_verify_config_llm_default_provider(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[llm] section -> shows default_provider = langchain."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[llm]\ndefault_provider = "langchain"\n', encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        by_label = {e["label"]: e for e in result["entries"]}
        assert "[llm]" in by_label
        assert by_label["[llm]"]["value"] == "default_provider = langchain"

    def test_verify_config_unknown_sections_ignored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unknown [custom] section not in output."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('[custom]\nfoo = "bar"\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        labels = [e["label"] for e in result["entries"]]
        assert "[custom]" not in labels
        # Only the Config file entry should be present
        assert labels == ["Config file"]

    def test_verify_config_empty_valid_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid but empty TOML -> ok config file, no section entries."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        assert result["has_error"] is False
        entries = result["entries"]
        assert len(entries) == 1
        assert entries[0]["label"] == "Config file"
        assert entries[0]["status"] == "ok"
        assert str(config_file) in entries[0]["value"]
