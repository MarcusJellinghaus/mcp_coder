"""Tests for workflows/label_config.py shared configuration loading module."""

import json
from pathlib import Path

import pytest

from mcp_coder.utils.github_operations.label_config import (
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
