"""Label configuration loading utilities.

This module provides functions to load and parse GitHub label configurations
from JSON files. It supports two operational modes:

1. LOCAL MODE: Workflow scripts with local project directory
   - Used by: mcp-coder define-labels, validate_labels.py, issue_stats.py
   - Tries: project_dir/workflows/config/labels.json first
   - Falls back to: bundled package config
   - Use case: Development, testing, custom label configurations

2. REMOTE MODE: Operations without local project (coordinator)
   - Used by: coordinator run, remote GitHub operations via repo_url
   - Always uses: bundled mcp_coder/config/labels.json
   - Use case: Centralized automation, consistent labels across repos

Usage patterns:

    # LOCAL MODE: CLI command or workflow script with project directory
    config_path = get_labels_config_path(project_dir)
    labels_config = load_labels_config(config_path)

    # REMOTE MODE: Coordinator without project directory
    config_path = get_labels_config_path(None)  # Uses bundled config
    labels_config = load_labels_config(config_path)

    # Build lookup dictionaries (both modes)
    label_lookups = build_label_lookups(labels_config)

    # Access label information (both modes)
    bot_pickup_labels = {
        name for name, category in label_lookups["name_to_category"].items()
        if category == "bot_pickup"
    }

Design rationale:
- Workflows need flexibility for testing/customization
- Coordinator needs consistency across multiple repositories
- Single bundled source of truth ensures reliable automation
- Backwards compatible with existing workflow scripts
"""

import json
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


def get_labels_config_path(project_dir: Optional[Path] = None) -> Path:
    """Get path to labels.json configuration file.

    This function supports two operational modes:

    MODE 1: Local project with custom labels (project_dir provided)
    ----------------------------------------------------------------
    Used by CLI commands (mcp-coder define-labels) and workflow scripts
    (validate_labels.py, issue_stats.py) that run in a local git repository
    and may want to customize labels.

    - If project_dir is provided AND local config exists:
      Returns: project_dir/workflows/config/labels.json
    - Otherwise falls back to bundled config (see MODE 2)

    MODE 2: Remote operations without local project (project_dir=None)
    -------------------------------------------------------------------
    Used by coordinator and remote GitHub operations that work via repo_url
    without a local git clone. These always use the bundled package config.

    - When project_dir is None:
      Returns: bundled mcp_coder/config/labels.json from installed package

    WHY THIS DESIGN:
    ----------------
    - Workflows need flexibility: Allow customization for testing/development
    - Coordinator needs consistency: Use standard labels across all repos
    - Single source of truth: Bundled config ensures consistent behavior
    - Backwards compatible: Existing workflows continue to work unchanged

    Resolution order:
    1. Project's local workflows/config/labels.json (if project_dir provided and exists)
    2. Package's bundled config (mcp_coder/config/labels.json) - ALWAYS works

    Args:
        project_dir: Optional project directory to check for local config override.
                    Pass None to always use bundled config (coordinator pattern).

    Returns:
        Path to labels.json file (either local override or bundled)

    Examples:
        # Workflow script with local project
        >>> config_path = get_labels_config_path(Path("/my/project"))
        >>> labels = load_labels_config(config_path)

        # Coordinator without local project (repo_url mode)
        >>> config_path = get_labels_config_path(None)  # Uses bundled config
        >>> labels = load_labels_config(config_path)
    """
    from importlib import resources

    # Check for project-local override
    if project_dir is not None:
        local_config = project_dir / "workflows" / "config" / "labels.json"
        if local_config.exists():
            return local_config

    # Fall back to package's bundled config
    config_resource = resources.files("mcp_coder.config") / "labels.json"
    # Convert to Path - resources.files returns Traversable which may not be Path
    if isinstance(config_resource, Path):
        return config_resource
    # For installed packages, we need to handle the resource differently
    # The path might be inside a zip file, so we return it as-is
    return Path(str(config_resource))


def load_labels_config(config_path: Path) -> Dict[str, Any]:
    """Load label configuration from JSON file.

    Args:
        config_path: Path to labels.json

    Returns:
        Dict with 'workflow_labels' and 'ignore_labels' keys

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If required keys are missing
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Label configuration not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config: Dict[str, Any] = json.load(f)

    # Validate required keys
    if "workflow_labels" not in config:
        raise ValueError("Configuration missing required key: 'workflow_labels'")

    return config
