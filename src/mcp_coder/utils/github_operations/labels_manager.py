"""Labels management for GitHub repositories.

This module provides functionality for managing GitHub repository labels.
"""

import re
from pathlib import Path
from typing import Optional, TypedDict

import git
from github import Github
from github.Repository import Repository

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
        self._repository: Optional[Repository] = None

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

    def _get_repository(self) -> Optional[Repository]:
        """Get the GitHub repository object.

        Returns:
            Repository object if successful, None otherwise
        """
        from github.GithubException import GithubException

        from .github_utils import parse_github_url

        if self._repository is not None:
            return self._repository

        try:
            # Get the remote URL from git repository
            remote_url = None
            for remote in self._repo.remotes:
                if remote.name == "origin":
                    remote_url = remote.url
                    break

            if not remote_url:
                print("No 'origin' remote found in git repository")
                return None

            # Parse the GitHub URL
            parsed = parse_github_url(remote_url)
            if parsed is None:
                print(f"Could not parse GitHub URL: {remote_url}")
                return None

            owner, repo_name = parsed
            repo_full_name = f"{owner}/{repo_name}"

            # Get repository from GitHub API
            self._repository = self._github_client.get_repo(repo_full_name)
            return self._repository

        except GithubException as e:
            print(f"Failed to access repository: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error accessing repository: {e}")
            return None

    def create_label(self, name: str, color: str, description: str = "") -> LabelData:
        """Create a new label in the repository.

        Args:
            name: Label name
            color: Hex color code (with or without '#' prefix)
            description: Label description

        Returns:
            LabelData with created label information, or empty dict on failure
        """
        from typing import cast

        from github import GithubException

        # Validate label name
        if not self._validate_label_name(name):
            return cast(LabelData, {})

        # Validate and normalize color
        if not self._validate_color(color):
            return cast(LabelData, {})
        normalized_color = self._normalize_color(color)

        try:
            # Get repository object
            repo = self._get_repository()
            if repo is None:
                return cast(LabelData, {})

            # Create the label using GitHub API
            label = repo.create_label(
                name=name, color=normalized_color, description=description
            )

            # Return structured dictionary with label information
            return {
                "name": label.name,
                "color": label.color,
                "description": label.description or "",
                "url": label.url,
            }

        except GithubException as e:
            print(f"GitHub API error creating label: {e}")
            return cast(LabelData, {})
        except Exception as e:
            print(f"Unexpected error creating label: {e}")
            return cast(LabelData, {})

    def get_label(self, name: str) -> LabelData:
        """Get a specific label by name.

        Args:
            name: Label name

        Returns:
            LabelData with label information, or empty dict if not found
        """
        from typing import cast

        from github import GithubException

        # Validate label name
        if not self._validate_label_name(name):
            return cast(LabelData, {})

        try:
            # Get repository object
            repo = self._get_repository()
            if repo is None:
                return cast(LabelData, {})

            # Get the label using GitHub API
            label = repo.get_label(name)

            # Return structured dictionary with label information
            return {
                "name": label.name,
                "color": label.color,
                "description": label.description or "",
                "url": label.url,
            }

        except GithubException as e:
            # Label not found or other GitHub API error
            print(f"GitHub API error getting label '{name}': {e}")
            return cast(LabelData, {})
        except Exception as e:
            print(f"Unexpected error getting label '{name}': {e}")
            return cast(LabelData, {})

    def get_labels(self) -> list[LabelData]:
        """Get all labels in the repository.

        Returns:
            List of LabelData for all labels, or empty list on failure
        """
        from github import GithubException

        try:
            # Get repository object
            repo = self._get_repository()
            if repo is None:
                return []

            # Get all labels using GitHub API
            labels = repo.get_labels()

            # Convert to structured list of dictionaries
            label_list = []
            for label in labels:
                label_dict: LabelData = {
                    "name": label.name,
                    "color": label.color,
                    "description": label.description or "",
                    "url": label.url,
                }
                label_list.append(label_dict)

            return label_list

        except GithubException as e:
            print(f"GitHub API error listing labels: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error listing labels: {e}")
            return []

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
            LabelData with updated label information, or empty dict on failure
        """
        from typing import cast

        from github import GithubException

        # Validate current label name
        if not self._validate_label_name(name):
            return cast(LabelData, {})

        # Validate new_name if provided
        if new_name is not None and not self._validate_label_name(new_name):
            return cast(LabelData, {})

        # Validate and normalize color if provided
        normalized_color = None
        if color is not None:
            if not self._validate_color(color):
                return cast(LabelData, {})
            normalized_color = self._normalize_color(color)

        try:
            # Get repository object
            repo = self._get_repository()
            if repo is None:
                return cast(LabelData, {})

            # Get the label using GitHub API
            label = repo.get_label(name)

            # Update the label with new values
            label.edit(
                name=new_name if new_name is not None else label.name,
                color=normalized_color if normalized_color is not None else label.color,
                description=(
                    description if description is not None else label.description
                ),
            )

            # Get updated label information
            updated_label = repo.get_label(new_name if new_name is not None else name)

            # Return structured dictionary with updated label information
            return {
                "name": updated_label.name,
                "color": updated_label.color,
                "description": updated_label.description or "",
                "url": updated_label.url,
            }

        except GithubException as e:
            print(f"GitHub API error updating label '{name}': {e}")
            return cast(LabelData, {})
        except Exception as e:
            print(f"Unexpected error updating label '{name}': {e}")
            return cast(LabelData, {})

    def delete_label(self, name: str) -> bool:
        """Delete a label from the repository.

        Args:
            name: Label name

        Returns:
            True if deletion was successful, False otherwise
        """
        from github import GithubException

        # Validate label name
        if not self._validate_label_name(name):
            return False

        try:
            # Get repository object
            repo = self._get_repository()
            if repo is None:
                return False

            # Get the label using GitHub API
            label = repo.get_label(name)

            # Delete the label
            label.delete()

            return True

        except GithubException as e:
            print(f"GitHub API error deleting label '{name}': {e}")
            return False
        except Exception as e:
            print(f"Unexpected error deleting label '{name}': {e}")
            return False
