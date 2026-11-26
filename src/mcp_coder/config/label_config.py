"""Label configuration loading utilities.

This module provides functions to load and parse GitHub label configurations
from JSON files.

Workflow labels always come from the bundled ``mcp_coder/config/labels.json``:

    labels_config = load_labels_config(get_labels_config_path())
"""

import json
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, TypedDict


class LabelLookups(TypedDict):
    """TypedDict for label lookup data structures."""

    id_to_name: dict[str, str]  # internal_id -> label_name
    all_names: set[str]  # All workflow label names
    name_to_category: dict[str, str]  # label_name -> category
    name_to_id: dict[str, str]  # label_name -> internal_id


def build_label_lookups(labels_config: dict[str, Any]) -> LabelLookups:
    """Build lookup dictionaries from label configuration.

    Args:
        labels_config: Loaded label configuration from JSON

    Returns:
        LabelLookups TypedDict with all lookup structures
    """
    # Initialize empty data structures
    id_to_name: dict[str, str] = {}
    all_names: set[str] = set()
    name_to_category: dict[str, str] = {}
    name_to_id: dict[str, str] = {}

    # Loop through workflow labels and populate all lookups
    for label in labels_config["workflow_labels"]:
        internal_id = label["internal_id"]
        label_name = label["name"]
        category = label["category"]

        # Populate all lookup structures
        id_to_name[internal_id] = label_name
        all_names.add(label_name)
        name_to_category[label_name] = category
        name_to_id[label_name] = internal_id

    # Return LabelLookups TypedDict
    return LabelLookups(
        id_to_name=id_to_name,
        all_names=all_names,
        name_to_category=name_to_category,
        name_to_id=name_to_id,
    )


def validate_labels_config(labels_config: dict[str, Any]) -> None:
    """Validate label config constraints. Raises ValueError on problems.

    Checks:
    1. Exactly one label has "default": true
    2. Each "promotable": true label has a next label in workflow_labels list
    3. No promotable label's next target has "failure": true
    4. Each label name is at most 50 characters (GitHub limit)
    5. Each label description is at most 100 characters (GitHub limit)

    Raises:
        ValueError: If any label config constraint is violated.
    """
    labels = labels_config["workflow_labels"]

    # Check exactly one default
    defaults = [label for label in labels if label.get("default")]
    if len(defaults) != 1:
        raise ValueError(
            f"Expected exactly one label with 'default': true, found {len(defaults)}"
        )

    # Check promotable constraints
    for i, label in enumerate(labels):
        if label.get("promotable"):
            if i + 1 >= len(labels):
                raise ValueError(
                    f"Label '{label['internal_id']}' is promotable but has "
                    f"no next label in the workflow_labels list"
                )
            next_label = labels[i + 1]
            if next_label.get("failure"):
                raise ValueError(
                    f"Label '{label['internal_id']}' is promotable but its "
                    f"next label '{next_label['internal_id']}' has failure: true"
                )

    # Check GitHub length limits
    for label in labels:
        name_len = len(label["name"])
        if name_len > 50:
            raise ValueError(
                f"Label '{label['internal_id']}' name is {name_len} characters "
                f"(GitHub limit: 50)"
            )
        desc_len = len(label.get("description", ""))
        if desc_len > 100:
            raise ValueError(
                f"Label '{label['internal_id']}' description is {desc_len} "
                f"characters (GitHub limit: 100)"
            )


def get_labels_config_path() -> Traversable:
    """Return the bundled labels.json (mcp_coder/config/labels.json)."""
    from importlib import resources

    return resources.files("mcp_coder.config") / "labels.json"


def load_labels_config(config_path: Path | Traversable) -> dict[str, Any]:
    """Load label configuration from JSON file.

    Args:
        config_path: Path or Traversable resource pointing to labels.json:
                     a plain Path (e.g. a test fixture) or the Traversable
                     from get_labels_config_path().

    Returns:
        Dict with 'workflow_labels' and 'ignore_labels' keys

    Raises:
        FileNotFoundError: If a Path-based config file doesn't exist
        ValueError: If required keys are missing
    """
    if isinstance(config_path, Path) and not config_path.exists():
        raise FileNotFoundError(f"Label configuration not found: {config_path}")
    config: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))

    # Validate required keys
    if "workflow_labels" not in config:
        raise ValueError("Configuration missing required key: 'workflow_labels'")

    return config
