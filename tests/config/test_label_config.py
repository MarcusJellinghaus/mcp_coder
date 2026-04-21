"""Tests for config/label_config.py shared configuration loading module."""

# ruff: noqa: S324

import json
from importlib.resources.abc import Traversable
from pathlib import Path

import pytest

from mcp_coder.config.label_config import (
    _get_labels_config_from_pyproject,
    get_labels_config_path,
    load_labels_config,
    validate_labels_config,
)


def test_load_bundled_labels_config() -> None:
    """Regression test: bundled labels.json is loadable via importlib.resources."""
    bundled_ref = get_labels_config_path(None)
    config = load_labels_config(bundled_ref)

    assert isinstance(config["workflow_labels"], list)
    assert len(config["workflow_labels"]) > 0

    required_keys = {"internal_id", "name", "color", "description", "category"}
    for label in config["workflow_labels"]:
        assert required_keys.issubset(
            label.keys()
        ), f"Label missing required keys: {required_keys - label.keys()}"

    assert isinstance(config["ignore_labels"], list)


def test_load_labels_config_valid() -> None:
    """Test loading valid labels.json"""
    # Use the test fixture
    test_config_path = Path("tests/workflows/config/test_labels.json")

    # Should load successfully
    config = load_labels_config(test_config_path)

    # Verify structure
    assert isinstance(config, dict)
    assert "workflow_labels" in config
    assert isinstance(config["workflow_labels"], list)
    assert len(config["workflow_labels"]) == 5  # Test fixture has 5 labels

    # Verify first label has required fields
    first_label = config["workflow_labels"][0]
    assert "internal_id" in first_label
    assert "name" in first_label
    assert "color" in first_label
    assert "description" in first_label
    assert "category" in first_label

    # Verify ignore_labels exists
    assert "ignore_labels" in config
    assert isinstance(config["ignore_labels"], list)


def test_load_labels_config_missing_file() -> None:
    """Test error handling for missing config file"""
    non_existent_path = Path("tests/workflows/config/non_existent.json")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_labels_config(non_existent_path)

    assert "Label configuration not found" in str(exc_info.value)
    assert str(non_existent_path) in str(exc_info.value)


def test_load_labels_config_invalid_json(tmp_path: Path) -> None:
    """Test error handling for invalid JSON"""
    # Create a temporary file with invalid JSON
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("{ this is not valid JSON }", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_labels_config(invalid_json_file)


VALID_CATEGORIES = {"human_action", "bot_pickup", "bot_busy"}
DEPRECATED_FIELDS = {"initial_command", "followup_command"}
REQUIRED_LABEL_KEYS = {"internal_id", "name", "color", "description", "category"}
REQUIRED_VSCODECLAUDE_KEYS = {"emoji", "display_name", "stage_short"}


def test_bundled_labels_schema_validation() -> None:
    """Validate bundled labels.json against the documented schema.

    Catches JSON syntax errors, missing required fields, deprecated fields,
    invalid categories, and vscodeclaude sub-object inconsistencies.
    """
    config = load_labels_config(get_labels_config_path(None))

    assert isinstance(config["workflow_labels"], list)
    assert len(config["workflow_labels"]) > 0
    assert isinstance(config.get("ignore_labels", []), list)

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for label in config["workflow_labels"]:
        # Required keys present
        missing = REQUIRED_LABEL_KEYS - label.keys()
        assert (
            not missing
        ), f"Label {label.get('internal_id', '???')}: missing {missing}"

        # No deprecated fields
        deprecated_found = DEPRECATED_FIELDS & label.keys()
        assert (
            not deprecated_found
        ), f"Label {label['internal_id']}: has deprecated fields {deprecated_found}"

        # Category is valid
        assert (
            label["category"] in VALID_CATEGORIES
        ), f"Label {label['internal_id']}: invalid category '{label['category']}'"

        # Unique internal_id and name
        assert (
            label["internal_id"] not in seen_ids
        ), f"Duplicate internal_id: {label['internal_id']}"
        assert label["name"] not in seen_names, f"Duplicate name: {label['name']}"
        seen_ids.add(label["internal_id"])
        seen_names.add(label["name"])

        # Color is a valid 6-char hex string
        assert (
            len(label["color"]) == 6
        ), f"Label {label['internal_id']}: color must be 6 hex chars"
        int(label["color"], 16)  # raises ValueError if not hex

        # vscodeclaude block validation
        if "vscodeclaude" in label:
            vsc = label["vscodeclaude"]
            vsc_missing = REQUIRED_VSCODECLAUDE_KEYS - vsc.keys()
            assert (
                not vsc_missing
            ), f"Label {label['internal_id']}: vscodeclaude missing {vsc_missing}"
            # commands, if present, must be a list of strings
            if "commands" in vsc:
                assert isinstance(
                    vsc["commands"], list
                ), f"Label {label['internal_id']}: commands must be a list"
                assert all(
                    isinstance(c, str) for c in vsc["commands"]
                ), f"Label {label['internal_id']}: all commands must be strings"

        # stale_timeout_minutes, if present, must be a positive int
        if "stale_timeout_minutes" in label:
            assert isinstance(
                label["stale_timeout_minutes"], int
            ), f"Label {label['internal_id']}: stale_timeout_minutes must be int"
            assert (
                label["stale_timeout_minutes"] > 0
            ), f"Label {label['internal_id']}: stale_timeout_minutes must be positive"


ERROR_STATUS_IDS = [
    "planning_failed",
    "implementing_failed",
    "ci_fix_needed",
    "llm_timeout",
    "pr_creating_failed",
    "task_tracker_prep_failed",
    "no_changes_after_retries",
]


@pytest.mark.parametrize("internal_id", ERROR_STATUS_IDS)
def test_error_statuses_have_vscodeclaude_commands(internal_id: str) -> None:
    """Error statuses must have commands so a Claude session launches."""
    config = load_labels_config(get_labels_config_path(None))
    label = next(
        l for l in config["workflow_labels"] if l["internal_id"] == internal_id
    )
    assert "vscodeclaude" in label, f"{internal_id}: missing vscodeclaude block"
    assert label["vscodeclaude"].get("commands") == ["/check_branch_status"], (
        f"{internal_id}: expected commands=['/check_branch_status'], "
        f"got {label['vscodeclaude'].get('commands')}"
    )


def test_pr_created_has_no_commands() -> None:
    """status-10:pr-created intentionally has no commands."""
    config = load_labels_config(get_labels_config_path(None))
    label = next(
        l for l in config["workflow_labels"] if l["internal_id"] == "pr_created"
    )
    assert "vscodeclaude" in label
    assert "commands" not in label["vscodeclaude"]


def test_load_labels_config_missing_workflow_labels_key(tmp_path: Path) -> None:
    """Test error handling for missing workflow_labels key"""
    # Create a temporary file with valid JSON but missing required key
    missing_key_file = tmp_path / "missing_key.json"
    missing_key_file.write_text('{"other_key": []}', encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        load_labels_config(missing_key_file)

    assert "Configuration missing required key: 'workflow_labels'" in str(
        exc_info.value
    )


class TestValidateLabelsConfig:
    """Tests for validate_labels_config()."""

    def test_valid_config_passes(self) -> None:
        """Bundled config should pass validation."""
        config = load_labels_config(get_labels_config_path(None))
        validate_labels_config(config)  # Should not raise

    def test_missing_default_raises(self) -> None:
        """Config with no default: true label raises ValueError."""
        config = {
            "workflow_labels": [
                {
                    "internal_id": "a",
                    "name": "a",
                    "color": "000000",
                    "description": "a",
                    "category": "human_action",
                },
            ]
        }
        with pytest.raises(ValueError, match="exactly one.*default"):
            validate_labels_config(config)

    def test_multiple_defaults_raises(self) -> None:
        """Config with two default: true labels raises ValueError."""
        config = {
            "workflow_labels": [
                {
                    "internal_id": "a",
                    "name": "a",
                    "color": "000000",
                    "description": "a",
                    "category": "human_action",
                    "default": True,
                },
                {
                    "internal_id": "b",
                    "name": "b",
                    "color": "111111",
                    "description": "b",
                    "category": "human_action",
                    "default": True,
                },
            ]
        }
        with pytest.raises(ValueError, match="exactly one.*default"):
            validate_labels_config(config)

    def test_promotable_without_next_raises(self) -> None:
        """Last label in list with promotable: true raises ValueError."""
        config = {
            "workflow_labels": [
                {
                    "internal_id": "a",
                    "name": "a",
                    "color": "000000",
                    "description": "a",
                    "category": "human_action",
                    "default": True,
                },
                {
                    "internal_id": "b",
                    "name": "b",
                    "color": "111111",
                    "description": "b",
                    "category": "human_action",
                    "promotable": True,
                },
            ]
        }
        with pytest.raises(ValueError, match="no next label"):
            validate_labels_config(config)

    def test_promotable_targeting_failure_raises(self) -> None:
        """Promotable label whose next entry has failure: true raises ValueError."""
        config = {
            "workflow_labels": [
                {
                    "internal_id": "a",
                    "name": "a",
                    "color": "000000",
                    "description": "a",
                    "category": "human_action",
                    "default": True,
                    "promotable": True,
                },
                {
                    "internal_id": "b",
                    "name": "b",
                    "color": "111111",
                    "description": "b",
                    "category": "human_action",
                    "failure": True,
                },
            ]
        }
        with pytest.raises(ValueError, match="failure"):
            validate_labels_config(config)

    def test_valid_promotable_passes(self) -> None:
        """Promotable label with valid non-failure next entry passes."""
        config = {
            "workflow_labels": [
                {
                    "internal_id": "a",
                    "name": "a",
                    "color": "000000",
                    "description": "a",
                    "category": "human_action",
                    "default": True,
                    "promotable": True,
                },
                {
                    "internal_id": "b",
                    "name": "b",
                    "color": "111111",
                    "description": "b",
                    "category": "bot_pickup",
                },
            ]
        }
        validate_labels_config(config)  # Should not raise

    def test_config_without_new_fields_fails(self) -> None:
        """Config missing default field fails validation (exactly one required)."""
        config = {
            "workflow_labels": [
                {
                    "internal_id": "a",
                    "name": "a",
                    "color": "000000",
                    "description": "a",
                    "category": "human_action",
                },
                {
                    "internal_id": "b",
                    "name": "b",
                    "color": "111111",
                    "description": "b",
                    "category": "bot_pickup",
                },
            ]
        }
        with pytest.raises(ValueError, match="exactly one.*default"):
            validate_labels_config(config)


class TestConfigDiscovery:
    """Tests for get_labels_config_path() config discovery."""

    def test_config_override_takes_priority(self, tmp_path: Path) -> None:
        """Explicit config_override is returned even when pyproject.toml exists."""
        # Create a config override file
        override = tmp_path / "custom_labels.json"
        override.write_text('{"workflow_labels": []}', encoding="utf-8")

        # Create pyproject.toml that also points to a config
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.mcp-coder]\nlabels-config = "other.json"\n',
            encoding="utf-8",
        )
        other = tmp_path / "other.json"
        other.write_text('{"workflow_labels": []}', encoding="utf-8")

        result = get_labels_config_path(project_dir=tmp_path, config_override=override)
        assert result == override

    def test_config_override_missing_raises(self, tmp_path: Path) -> None:
        """Non-existent config_override raises FileNotFoundError."""
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            get_labels_config_path(config_override=missing)

    def test_pyproject_toml_labels_config(self, tmp_path: Path) -> None:
        """labels-config in pyproject.toml is used when no override given."""
        labels_file = tmp_path / "my_labels.json"
        labels_file.write_text('{"workflow_labels": []}', encoding="utf-8")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.mcp-coder]\nlabels-config = "my_labels.json"\n',
            encoding="utf-8",
        )

        result = get_labels_config_path(project_dir=tmp_path)
        assert result == labels_file

    def test_pyproject_toml_missing_key_falls_to_bundled(self, tmp_path: Path) -> None:
        """pyproject.toml without labels-config key falls back to bundled."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[tool.mcp-coder]\n# no labels-config key\n",
            encoding="utf-8",
        )

        result = get_labels_config_path(project_dir=tmp_path)
        assert isinstance(result, Traversable)

    def test_no_project_dir_returns_bundled(self) -> None:
        """project_dir=None returns bundled config."""
        result = get_labels_config_path(project_dir=None)
        assert isinstance(result, Traversable)

    def test_pyproject_toml_nonexistent_path_falls_to_bundled(
        self, tmp_path: Path
    ) -> None:
        """labels-config pointing to non-existent file falls back to bundled."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.mcp-coder]\nlabels-config = "does_not_exist.json"\n',
            encoding="utf-8",
        )

        result = get_labels_config_path(project_dir=tmp_path)
        assert isinstance(result, Traversable)

    def test_old_workflows_config_not_used(self, tmp_path: Path) -> None:
        """workflows/config/labels.json is NOT used even if it exists (breaking change)."""
        old_dir = tmp_path / "workflows" / "config"
        old_dir.mkdir(parents=True)
        old_config = old_dir / "labels.json"
        old_config.write_text('{"workflow_labels": []}', encoding="utf-8")

        result = get_labels_config_path(project_dir=tmp_path)
        # Should NOT return the old path — should return bundled
        assert result != old_config
        assert isinstance(result, Traversable)

    def test_malformed_pyproject_toml_falls_back(self, tmp_path: Path) -> None:
        """Invalid TOML content in pyproject.toml causes graceful fallback to bundled config."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is {{{ not valid TOML", encoding="utf-8")

        result = get_labels_config_path(project_dir=tmp_path)
        assert isinstance(result, Traversable)


class TestGetLabelsConfigFromPyproject:
    """Tests for _get_labels_config_from_pyproject() helper."""

    def test_no_pyproject_returns_none(self, tmp_path: Path) -> None:
        """No pyproject.toml file returns None."""
        result = _get_labels_config_from_pyproject(tmp_path)
        assert result is None

    def test_valid_config_returns_path(self, tmp_path: Path) -> None:
        """Valid labels-config key returns resolved path."""
        labels = tmp_path / "labels.json"
        labels.write_text("{}", encoding="utf-8")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.mcp-coder]\nlabels-config = "labels.json"\n',
            encoding="utf-8",
        )

        result = _get_labels_config_from_pyproject(tmp_path)
        assert result == labels

    def test_missing_tool_section_returns_none(self, tmp_path: Path) -> None:
        """pyproject.toml without [tool] section returns None."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'foo'\n", encoding="utf-8")

        result = _get_labels_config_from_pyproject(tmp_path)
        assert result is None

    def test_malformed_toml_returns_none(self, tmp_path: Path) -> None:
        """Malformed TOML returns None gracefully."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("{{{ bad toml", encoding="utf-8")

        result = _get_labels_config_from_pyproject(tmp_path)
        assert result is None

    def test_file_not_found_returns_none(self, tmp_path: Path) -> None:
        """labels-config pointing to missing file returns None."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.mcp-coder]\nlabels-config = "missing.json"\n',
            encoding="utf-8",
        )

        result = _get_labels_config_from_pyproject(tmp_path)
        assert result is None
