"""Tests for config schema and type validation in user_config module."""

from pathlib import Path

import pytest

from mcp_coder.utils.user_config import (
    _CONFIG_SCHEMA,
    FieldDef,
    _get_field_def,
    get_config_values,
)


class TestConfigTypeValidation:
    """Tests for schema-driven type validation in get_config_values."""

    def test_string_in_bool_field_raises_valueerror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TOML string 'true' in a bool field raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('[mlflow]\nenabled = "true"\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected bool.*got str"):
            get_config_values([("mlflow", "enabled", None)])

    def test_string_in_int_field_raises_valueerror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TOML string "3" in an int field raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[vscodeclaude]\nworkspace_base = "/tmp"\nmax_sessions = "3"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected int.*got str"):
            get_config_values([("vscodeclaude", "max_sessions", None)])

    def test_bool_in_int_field_raises_valueerror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TOML boolean true in an int field raises ValueError (bool is subclass of int)."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[vscodeclaude]\nworkspace_base = "/tmp"\nmax_sessions = true\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected int.*got bool"):
            get_config_values([("vscodeclaude", "max_sessions", None)])

    def test_native_bool_in_bool_field_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Native TOML bool in a bool field passes validation."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("[mlflow]\nenabled = true\n", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        result = get_config_values([("mlflow", "enabled", None)])
        assert result[("mlflow", "enabled")] is True

    def test_unknown_section_key_no_validation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keys not in schema pass through without validation."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('[custom]\nfoo = "bar"\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        result = get_config_values([("custom", "foo", None)])
        assert result[("custom", "foo")] == "bar"

    def test_env_var_bypasses_type_validation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env var values are strings and bypass schema type validation."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token_string")

        result = get_config_values([("github", "token", None)])
        assert result[("github", "token")] == "env_token_string"

    def test_valueerror_message_includes_context(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValueError message includes section, key, expected type, actual type, value."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('[mlflow]\nenabled = "yes"\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match=r"\[mlflow\].*enabled.*bool.*str.*yes"):
            get_config_values([("mlflow", "enabled", None)])

    def test_wildcard_section_validates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """coordinator.repos.* fields are validated against wildcard schema."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[coordinator.repos.myrepo]\nrepo_url = "https://example.com"\n'
            'update_issue_labels = "true"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected bool.*got str"):
            get_config_values(
                [("coordinator.repos.myrepo", "update_issue_labels", None)]
            )


class TestConfigSchema:
    """Tests for FieldDef and _CONFIG_SCHEMA."""

    def test_field_def_creation(self) -> None:
        """FieldDef stores type, required, and env_var."""
        f = FieldDef(str, required=True, env_var="MY_VAR")
        assert f.field_type is str
        assert f.required is True
        assert f.env_var == "MY_VAR"

    def test_field_def_defaults(self) -> None:
        """FieldDef defaults: required=False, env_var=None."""
        f = FieldDef(bool)
        assert f.required is False
        assert f.env_var is None

    def test_schema_has_all_known_sections(self) -> None:
        """Schema contains all expected top-level sections."""
        expected = {
            "github",
            "jenkins",
            "mcp",
            "llm",
            "llm.langchain",
            "coordinator",
            "coordinator.repos.*",
            "vscodeclaude",
            "mlflow",
        }
        assert set(_CONFIG_SCHEMA.keys()) == expected

    def test_schema_github_token_env_var(self) -> None:
        """github.token maps to GITHUB_TOKEN."""
        assert _CONFIG_SCHEMA["github"]["token"].env_var == "GITHUB_TOKEN"

    def test_schema_langchain_env_vars(self) -> None:
        """llm.langchain fields have correct env var mappings."""
        lc = _CONFIG_SCHEMA["llm.langchain"]
        assert lc["backend"].env_var == "MCP_CODER_LLM_LANGCHAIN_BACKEND"
        assert lc["model"].env_var == "MCP_CODER_LLM_LANGCHAIN_MODEL"
        assert lc["endpoint"].env_var == "MCP_CODER_LLM_LANGCHAIN_ENDPOINT"
        assert lc["api_version"].env_var == "MCP_CODER_LLM_LANGCHAIN_API_VERSION"

    def test_get_field_def_exact_match(self) -> None:
        """_get_field_def returns FieldDef for exact section match."""
        result = _get_field_def("github", "token")
        assert result is not None
        assert result.env_var == "GITHUB_TOKEN"

    def test_get_field_def_wildcard_match(self) -> None:
        """_get_field_def matches coordinator.repos.* sections."""
        result = _get_field_def("coordinator.repos.mcp_coder", "repo_url")
        assert result is not None
        assert result.required is True

    def test_get_field_def_unknown_returns_none(self) -> None:
        """_get_field_def returns None for unknown section/key."""
        assert _get_field_def("unknown", "key") is None
        assert _get_field_def("github", "unknown_key") is None

    def test_field_def_is_frozen(self) -> None:
        """FieldDef instances are immutable."""
        f = FieldDef(str)
        with pytest.raises(AttributeError):
            f.required = True  # type: ignore[misc]
