"""Shared label configuration loading utilities."""
import json
from pathlib import Path
from typing import Any, Dict, TypedDict


class LabelLookups(TypedDict):
    """TypedDict for label lookup data structures."""
    id_to_name: dict[str, str]        # internal_id -> label_name
    all_names: set[str]               # All workflow label names
    name_to_category: dict[str, str]  # label_name -> category
    name_to_id: dict[str, str]        # label_name -> internal_id


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
        name_to_id=name_to_id
    )


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
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config: Dict[str, Any] = json.load(f)
    
    # Validate required keys
    if 'workflow_labels' not in config:
        raise ValueError("Configuration missing required key: 'workflow_labels'")
    
    return config
