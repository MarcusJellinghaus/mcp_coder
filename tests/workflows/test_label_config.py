"""Tests for workflows/label_config.py shared configuration loading module."""

import json
from pathlib import Path

import pytest

from mcp_coder.utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
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
    assert len(config["workflow_labels"]) == 4  # Test fixture has 4 labels

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
