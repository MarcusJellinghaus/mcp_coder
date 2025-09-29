"""Labels management for GitHub repositories.

This module provides functionality for managing GitHub repository labels.
"""

import re
from pathlib import Path
from typing import Optional, TypedDict

import git
from github import Github

from mcp_coder.utils import user_config


class LabelData(TypedDict):
    """Typed dictionary for GitHub label data."""

    name: str
    color: str
    description: str
    url: str


class LabelsManager:
    """Manager for GitHub repository labels.

    Provides methods for creating, reading, updating, and deleting GitHub labels.
    """

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        """Initialize LabelsManager.

        Args:
            project_dir: Path to the project directory

        Raises:
            ValueError: If project_dir is None, not a directory, not a git repository,
                       or GitHub token is not found
        """
        # Validate project_dir
        if project_dir is None:
            raise ValueError("project_dir is required")

        if not project_dir.exists():
            raise ValueError(f"Directory does not exist: {project_dir}")

        if not project_dir.is_dir():
            raise ValueError(f"Path is not a directory: {project_dir}")

        # Check if it's a git repository
        try:
            repo = git.Repo(project_dir)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Directory is not a git repository: {project_dir}")

        # Get GitHub token
        github_token = user_config.get_config_value("github", "token")
        if not github_token:
            raise ValueError(
                "GitHub token not found. Configure it in ~/.mcp_coder/config.toml "
                "or set GITHUB_TOKEN environment variable"
            )

        self.project_dir = project_dir
        self.github_token = github_token
        self._repo = repo
        self._github_client = Github(github_token)

    def _validate_label_name(self, name: str) -> bool:
        """Validate label name.

        Label names must:
        - Not be empty or whitespace-only
        - Not have leading or trailing whitespace

        Args:
            name: Label name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False

        # Check for empty or whitespace-only
        if not name.strip():
            return False

        # Check for leading or trailing whitespace
        if name != name.strip():
            return False

        return True

    def _validate_color(self, color: str) -> bool:
        """Validate hex color code.

        Valid formats:
        - 6-character hex code (e.g., "FF0000")
        - 6-character hex code with '#' prefix (e.g., "#FF0000")

        Args:
            color: Hex color code to validate

        Returns:
            True if valid, False otherwise
        """
        if not color or not isinstance(color, str):
            return False

        # Check if it matches hex color pattern (with or without #)
        pattern = r"^#?[0-9A-Fa-f]{6}$"
        return bool(re.match(pattern, color))

    def _normalize_color(self, color: str) -> str:
        """Normalize color by removing '#' prefix.

        Args:
            color: Hex color code to normalize

        Returns:
            Normalized color without '#' prefix
        """
        if color.startswith("#"):
            return color[1:]
        return color

    def create_label(self, name: str, color: str, description: str = "") -> LabelData:
        """Create a new label in the repository.

        Args:
            name: Label name
            color: Hex color code (with or without '#' prefix)
            description: Label description

        Returns:
            LabelData with created label information
        """
        # TODO: Implement label creation
        raise NotImplementedError("create_label not yet implemented")

    def get_label(self, name: str) -> LabelData:
        """Get a specific label by name.

        Args:
            name: Label name

        Returns:
            LabelData with label information, or empty dict if not found
        """
        # TODO: Implement get label
        raise NotImplementedError("get_label not yet implemented")

    def get_labels(self) -> list[LabelData]:
        """Get all labels in the repository.

        Returns:
            List of LabelData for all labels
        """
        # TODO: Implement list labels
        raise NotImplementedError("get_labels not yet implemented")

    def update_label(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        new_name: Optional[str] = None,
    ) -> LabelData:
        """Update an existing label.

        Args:
            name: Current label name
            color: New hex color code (optional)
            description: New description (optional)
            new_name: New name for the label (optional)

        Returns:
            LabelData with updated label information
        """
        # TODO: Implement label update
        raise NotImplementedError("update_label not yet implemented")

    def delete_label(self, name: str) -> bool:
        """Delete a label from the repository.

        Args:
            name: Label name

        Returns:
            True if deletion was successful, False otherwise
        """
        # TODO: Implement label deletion
        raise NotImplementedError("delete_label not yet implemented")
