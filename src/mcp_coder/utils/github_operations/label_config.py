"""Label configuration loading utilities.

This module provides functions to load and parse GitHub label configurations
from JSON files.

Config resolution order:
1. Explicit ``config_override`` path (highest priority, e.g. ``--config`` flag)
2. ``[tool.mcp-coder] labels-config`` in ``pyproject.toml`` (relative to project root)
3. Bundled package defaults (``mcp_coder/config/labels.json``)

Usage patterns:

    # With explicit override (CLI --config flag)
    config_path = get_labels_config_path(project_dir, config_override=Path("custom.json"))
    labels_config = load_labels_config(config_path)

    # Project with pyproject.toml config
    config_path = get_labels_config_path(project_dir)
    labels_config = load_labels_config(config_path)

    # Without project directory (coordinator / remote mode)
    config_path = get_labels_config_path(None)  # Uses bundled config
    labels_config = load_labels_config(config_path)
"""

import json
import tomllib
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict


class LabelLookups(TypedDict):
    """TypedDict for label lookup data structures."""

    id_to_name: dict[str, str]  # internal_id -> label_name
    all_names: set[str]  # All workflow label names
    name_to_category: dict[str, str]  # label_name -> category
    name_to_id: dict[str, str]  # label_name -> internal_id


def build_label_lookups(labels_config: Dict[str, Any]) -> LabelLookups:
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


def validate_labels_config(labels_config: Dict[str, Any]) -> None:
    """Validate label config constraints. Raises ValueError on problems.

    Checks:
    1. Exactly one label has "default": true
    2. Each "promotable": true label has a next label in workflow_labels list
    3. No promotable label's next target has "failure": true
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


def _get_labels_config_from_pyproject(project_dir: Path) -> Optional[Path]:
    """Read labels-config from [tool.mcp-coder] in pyproject.toml.

    Returns absolute Path if configured and file exists, None otherwise.
    """
    path = project_dir / "pyproject.toml"
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return None
    try:
        config_value = data["tool"]["mcp-coder"]["labels-config"]
    except KeyError:
        return None
    resolved = project_dir / config_value
    return resolved if resolved.exists() else None


def get_labels_config_path(
    project_dir: Optional[Path] = None,
    config_override: Optional[Path] = None,
) -> Path | Traversable:
    """Get path to labels.json configuration file.

    Resolution order:
    1. config_override (explicit --config flag, highest priority)
    2. [tool.mcp-coder] labels-config in pyproject.toml (relative to project root)
    3. Bundled package defaults (mcp_coder/config/labels.json)

    Args:
        project_dir: Optional project directory for pyproject.toml lookup.
                    Pass None to always use bundled config (coordinator pattern).
        config_override: Optional explicit path to a labels config file.
                        Raises FileNotFoundError if the file does not exist.

    Returns:
        Path to labels.json file

    Raises:
        FileNotFoundError: If config_override is given but the file does not exist.
    """
    from importlib import resources

    # 1. Explicit override takes priority
    if config_override is not None:
        if not config_override.exists():
            raise FileNotFoundError(f"Config override not found: {config_override}")
        return config_override

    # 2. pyproject.toml lookup
    if project_dir is not None:
        pyproject_path = _get_labels_config_from_pyproject(project_dir)
        if pyproject_path is not None:
            return pyproject_path

    # 3. Bundled package defaults
    return resources.files("mcp_coder.config") / "labels.json"


def load_labels_config(config_path: Path | Traversable) -> Dict[str, Any]:
    """Load label configuration from JSON file.

    Args:
        config_path: Path or Traversable resource pointing to labels.json.
                     Use a plain Path for local overrides; use the Traversable
                     returned by get_labels_config_path() for the bundled config.

    Returns:
        Dict with 'workflow_labels' and 'ignore_labels' keys

    Raises:
        FileNotFoundError: If a Path-based config file doesn't exist
        ValueError: If required keys are missing
    """
    if isinstance(config_path, Path) and not config_path.exists():
        raise FileNotFoundError(f"Label configuration not found: {config_path}")
    config: Dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))

    # Validate required keys
    if "workflow_labels" not in config:
        raise ValueError("Configuration missing required key: 'workflow_labels'")

    return config
