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
            "GITHUB_TEST_REPO_URL",
            "JENKINS_URL",
            "JENKINS_USER",
            "JENKINS_TOKEN",
            "MCP_CODER_MCP_CONFIG",
            "MCP_CODER_LLM_LANGCHAIN_BACKEND",
            "MCP_CODER_LLM_LANGCHAIN_MODEL",
            "MCP_CODER_LLM_LANGCHAIN_ENDPOINT",
            "MCP_CODER_LLM_LANGCHAIN_API_VERSION",
            "MLFLOW_TRACKING_URI",
            "MLFLOW_EXPERIMENT_NAME",
            "MLFLOW_DEFAULT_ARTIFACT_ROOT",
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
            """\
[llm]
default_provider = "langchain"

[github]
token = "ghp_test"

[jenkins]
server_url = "http://jenkins"
username = "admin"
api_token = "token123"

[mcp]
default_config_path = ".mcp.json"

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/test/repo.git"
executor_job_path = "Tests/test"
github_credentials_id = "creds"

[coordinator.repos.mcp_workspace]
repo_url = "https://github.com/test/workspace.git"
executor_job_path = "Tests/test2"
github_credentials_id = "creds2"

[vscodeclaude]
workspace_base = "C:/workspaces"

[mlflow]
enabled = true
tracking_uri = "http://mlflow"
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
        assert "[github]" in labels
        assert "[jenkins]" in labels
        assert "[mcp]" in labels
        assert "[llm]" in labels
        assert "[coordinator]" in labels
        assert "[vscodeclaude]" in labels
        assert "[mlflow]" in labels

        # No errors or warnings
        for entry in result["entries"]:
            assert entry["status"] in ("ok", "info")

        # Check github token is configured
        github_entries = [e for e in result["entries"] if e["label"] == "[github]"]
        token_entry = [e for e in github_entries if "token" in e["value"]]
        assert token_entry
        assert "configured" in token_entry[0]["value"]
        assert "(config.toml)" in token_entry[0]["value"]

        # Check jenkins fields configured
        jenkins_entries = [e for e in result["entries"] if e["label"] == "[jenkins]"]
        jenkins_ok = [e for e in jenkins_entries if e["status"] == "ok"]
        assert len(jenkins_ok) >= 3  # server_url, username, api_token

        # Check coordinator repo count
        coord_entries = [e for e in result["entries"] if e["label"] == "[coordinator]"]
        assert any("2 repos configured" in e["value"] for e in coord_entries)

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
        github_entries = [e for e in result["entries"] if e["label"] == "[github]"]
        token_entry = [e for e in github_entries if "token" in e["value"]]
        assert token_entry
        assert "(env var)" in token_entry[0]["value"]
        assert "config.toml" not in token_entry[0]["value"]

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

        github_entries = [e for e in result["entries"] if e["label"] == "[github]"]
        token_entry = [e for e in github_entries if "token" in e["value"]]
        assert token_entry
        assert "(env var, also in config.toml)" in token_entry[0]["value"]

    def test_verify_config_coordinator_repo_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """3 repos -> '3 repos configured'."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """\
[coordinator.repos.repo1]
repo_url = "https://example.com/repo1.git"
executor_job_path = "Tests/test1"
github_credentials_id = "creds1"

[coordinator.repos.repo2]
repo_url = "https://example.com/repo2.git"
executor_job_path = "Tests/test2"
github_credentials_id = "creds2"

[coordinator.repos.repo3]
repo_url = "https://example.com/repo3.git"
executor_job_path = "Tests/test3"
github_credentials_id = "creds3"
""",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        coord_entries = [e for e in result["entries"] if e["label"] == "[coordinator]"]
        assert any("3 repos configured" in e["value"] for e in coord_entries)

    def test_verify_config_llm_default_provider(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[llm] section -> shows default_provider configured."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[llm]\ndefault_provider = "langchain"\n', encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        llm_entries = [e for e in result["entries"] if e["label"] == "[llm]"]
        assert any(
            "default_provider" in e["value"] and e["status"] == "ok"
            for e in llm_entries
        )

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

    def test_verify_config_mcp_configured_in_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[mcp] in config -> ok status with default_config_path configured."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[mcp]\ndefault_config_path = ".mcp.json"\n', encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        mcp_entries = [e for e in result["entries"] if e["label"] == "[mcp]"]
        ok_entries = [e for e in mcp_entries if e["status"] == "ok"]
        assert ok_entries
        assert any("default_config_path" in e["value"] for e in ok_entries)

    def test_verify_config_mcp_not_configured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No [mcp] config and no env var -> info status, not configured."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        mcp_entries = [e for e in result["entries"] if e["label"] == "[mcp]"]
        assert mcp_entries
        assert mcp_entries[0]["status"] == "info"
        assert "not configured" in mcp_entries[0]["value"]

    def test_verify_config_mcp_configured_via_env_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_MCP_CONFIG env var set -> ok status with (env var)."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)
        monkeypatch.setenv("MCP_CODER_MCP_CONFIG", "/path/to/.mcp.json")

        result = verify_config()

        mcp_entries = [e for e in result["entries"] if e["label"] == "[mcp]"]
        ok_entries = [e for e in mcp_entries if e["status"] == "ok"]
        assert ok_entries
        assert "(env var)" in ok_entries[0]["value"]

    def test_verify_config_empty_valid_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid but empty TOML -> ok config file, all sections info."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        assert result["has_error"] is False
        entries = result["entries"]
        assert entries[0]["label"] == "Config file"
        assert entries[0]["status"] == "ok"
        assert str(config_file) in entries[0]["value"]

    def test_verify_config_type_mismatch_reports_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """String in bool field -> error status with type context."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('[mlflow]\nenabled = "true"\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        assert result["has_error"] is True
        errors = [e for e in result["entries"] if e["status"] == "error"]
        assert any(
            "expected bool" in e["value"] and "enabled" in e["value"] for e in errors
        )

    def test_verify_config_missing_required_field(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Present section with missing required field -> error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("[github]\n", encoding="utf-8")  # token missing
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        assert result["has_error"] is True
        errors = [e for e in result["entries"] if e["status"] == "error"]
        assert any("token" in e["value"] and "required" in e["value"] for e in errors)

    def test_verify_config_unknown_key_warns(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unknown key in known section -> warning."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[github]\ntoken = "ghp_test"\nunknown_key = "value"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        warnings = [e for e in result["entries"] if e["status"] == "warning"]
        assert any("unknown_key" in e["value"] for e in warnings)

    def test_verify_config_absent_section_info(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Absent section -> info hint."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        self._clear_env_vars(monkeypatch)

        result = verify_config()

        info_entries = [e for e in result["entries"] if e["status"] == "info"]
        labels = [e["label"] for e in info_entries]
        assert "[github]" in labels
        assert "[jenkins]" in labels
        assert "[mlflow]" in labels
