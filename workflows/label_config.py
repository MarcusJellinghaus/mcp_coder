"""Shared label configuration loading utilities."""
import json
from pathlib import Path
from typing import Any, Dict


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
