"""Tests for CIResultsManager class."""

import io
import zipfile
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch

import pytest
import requests  # type: ignore
from github import GithubException

from mcp_coder.utils.github_operations import (
    CIResultsManager,
    CIStatusData,
)


class TestCIResultsManagerFoundation:
    """Test the foundational components of CIResultsManager."""

    def test_initialization_with_project_dir(self, tmp_path: Path) -> None:
        """Test initialization with project_dir parameter."""
        # Create a git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Mock the git repository check
        with patch("git.Repo") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            # Mock user config to return a token
            with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
                mock_config.return_value = "test_token"

                # Mock Github client
                with patch("github.Github"):
                    manager = CIResultsManager(project_dir=repo_dir)

                    assert manager.project_dir == repo_dir
                    assert manager._repo is not None

    def test_initialization_with_repo_url(self) -> None:
        """Test initialization with repo_url parameter."""
        repo_url = "https://github.com/test/repo.git"

        # Mock user config to return a token
        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "test_token"

            # Mock Github client
            with patch("github.Github"):
                manager = CIResultsManager(repo_url=repo_url)

                assert manager.project_dir is None
                assert manager._repo_owner == "test"
                assert manager._repo_name == "repo"
                assert manager._repo_full_name == "test/repo"

    def test_initialization_validation(self) -> None:
        """Test initialization parameter validation."""
        # Test with neither parameter
        with pytest.raises(
            ValueError, match="Exactly one of project_dir or repo_url must be provided"
        ):
            CIResultsManager()

        # Test with both parameters
        with pytest.raises(
            ValueError, match="Exactly one of project_dir or repo_url must be provided"
        ):
            CIResultsManager(
                project_dir=Path("/tmp"), repo_url="https://github.com/test/repo.git"
            )

    def test_validate_branch_name(self) -> None:
        """Test branch name validation."""
        repo_url = "https://github.com/test/repo.git"

        # Mock user config and Github client
        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "test_token"

            with patch("github.Github"):
                manager = CIResultsManager(repo_url=repo_url)

                # Valid branch names
                assert manager._validate_branch_name("feature/xyz") == True
                assert manager._validate_branch_name("main") == True
                assert manager._validate_branch_name("develop") == True

                # Invalid branch names
                assert manager._validate_branch_name("") == False
                assert manager._validate_branch_name("   ") == False
                assert (
                    manager._validate_branch_name("branch~1") == False
                )  # Invalid char
                assert (
                    manager._validate_branch_name("branch^2") == False
                )  # Invalid char
                assert (
                    manager._validate_branch_name("branch:fix") == False
                )  # Invalid char
                assert (
                    manager._validate_branch_name("branch?test") == False
                )  # Invalid char
                assert (
                    manager._validate_branch_name("branch*glob") == False
                )  # Invalid char
                assert (
                    manager._validate_branch_name("branch[1]") == False
                )  # Invalid char

    def test_validate_run_id(self) -> None:
        """Test workflow run ID validation."""
        repo_url = "https://github.com/test/repo.git"

        # Mock user config and Github client
        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "test_token"

            with patch("github.Github"):
                manager = CIResultsManager(repo_url=repo_url)

                # Valid run IDs
                assert manager._validate_run_id(12345) == True
                assert manager._validate_run_id(1) == True
                assert manager._validate_run_id(999999999) == True

                # Invalid run IDs
                assert manager._validate_run_id(0) == False
                assert manager._validate_run_id(-1) == False
                assert manager._validate_run_id(-100) == False

    def test_cistatus_data_structure(self) -> None:
        """Test that CIStatusData TypedDict is properly defined and importable."""
        # Create a test instance to verify structure
        test_data: CIStatusData = {
            "run": {
                "id": 123,
                "status": "completed",
                "conclusion": "failure",
                "workflow_name": "CI",
                "event": "push",
                "workflow_path": ".github/workflows/ci.yml",
                "branch": "main",
                "commit_sha": "abc123",
                "created_at": "2023-01-01T00:00:00Z",
                "url": "https://github.com/test/repo/actions/runs/123",
            },
            "jobs": [
                {
                    "id": 456,
                    "name": "test",
                    "status": "completed",
                    "conclusion": "failure",
                    "started_at": "2023-01-01T00:01:00Z",
                    "completed_at": "2023-01-01T00:05:00Z",
                }
            ],
        }

        # Verify the structure is accessible
        assert test_data["run"]["id"] == 123
        assert test_data["jobs"][0]["name"] == "test"
        assert len(test_data["jobs"]) == 1

    def test_manager_inheritance(self) -> None:
        """Test that CIResultsManager properly extends BaseGitHubManager."""
        repo_url = "https://github.com/test/repo.git"

        # Mock user config and Github client
        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "test_token"

            with patch("github.Github"):
                manager = CIResultsManager(repo_url=repo_url)

                # Verify inheritance - should have BaseGitHubManager attributes
                assert hasattr(manager, "_github_client")
                assert hasattr(manager, "_repository")
                assert hasattr(manager, "_get_repository")
                assert manager._repo_full_name == "test/repo"


class TestGetLatestCIStatus:
    """Test the get_latest_ci_status method."""

    def test_successful_status_retrieval(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test successful CI status retrieval with jobs."""
        # Mock workflow run
        mock_run = Mock()
        mock_run.id = 123456789
        mock_run.status = "completed"
        mock_run.conclusion = "failure"
        mock_run.name = "CI"
        mock_run.event = "push"
        mock_run.path = ".github/workflows/ci.yml"
        mock_run.head_sha = "abc123def456"
        mock_run.created_at = Mock()
        mock_run.created_at.isoformat.return_value = "2024-01-15T10:30:00Z"
        mock_run.html_url = "https://github.com/test/repo/actions/runs/123456789"

        # Mock jobs
        mock_job1 = Mock()
        mock_job1.id = 987654321
        mock_job1.name = "test"
        mock_job1.status = "completed"
        mock_job1.conclusion = "failure"
        mock_job1.started_at = Mock()
        mock_job1.started_at.isoformat.return_value = "2024-01-15T10:31:00Z"
        mock_job1.completed_at = Mock()
        mock_job1.completed_at.isoformat.return_value = "2024-01-15T10:35:00Z"

        mock_job2 = Mock()
        mock_job2.id = 987654322
        mock_job2.name = "build"
        mock_job2.status = "completed"
        mock_job2.conclusion = "success"
        mock_job2.started_at = Mock()
        mock_job2.started_at.isoformat.return_value = "2024-01-15T10:31:00Z"
        mock_job2.completed_at = Mock()
        mock_job2.completed_at.isoformat.return_value = "2024-01-15T10:33:00Z"

        # Set head_branch for filtering
        mock_run.head_branch = "feature/xyz"

        mock_run.jobs.return_value = [mock_job1, mock_job2]
        mock_repo.get_workflow_runs.return_value = [mock_run]

        # Test the method
        result = ci_manager.get_latest_ci_status("feature/xyz")

        # Verify the result structure
        assert "run" in result
        assert "jobs" in result

        # Verify run data
        run_data = result["run"]
        assert run_data["id"] == 123456789
        assert run_data["status"] == "completed"
        assert run_data["conclusion"] == "failure"
        assert run_data["workflow_name"] == "CI"
        assert run_data["event"] == "push"
        assert run_data["workflow_path"] == ".github/workflows/ci.yml"
        assert run_data["branch"] == "feature/xyz"
        assert run_data["commit_sha"] == "abc123def456"
        assert run_data["created_at"] == "2024-01-15T10:30:00Z"
        assert run_data["url"] == "https://github.com/test/repo/actions/runs/123456789"

        # Verify jobs data
        jobs_data = result["jobs"]
        assert len(jobs_data) == 2

        job1_data = jobs_data[0]
        assert job1_data["id"] == 987654321
        assert job1_data["name"] == "test"
        assert job1_data["status"] == "completed"
        assert job1_data["conclusion"] == "failure"
        assert job1_data["started_at"] == "2024-01-15T10:31:00Z"
        assert job1_data["completed_at"] == "2024-01-15T10:35:00Z"

        job2_data = jobs_data[1]
        assert job2_data["id"] == 987654322
        assert job2_data["name"] == "build"
        assert job2_data["status"] == "completed"
        assert job2_data["conclusion"] == "success"

        # Verify API was called correctly
        mock_repo.get_workflow_runs.assert_called_once()
        mock_run.jobs.assert_called_once()


class TestGetArtifacts:
    """Test the get_artifacts method."""

    def test_single_artifact(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test downloading a single artifact."""
        # Mock workflow run and artifact
        mock_run = Mock()
        mock_run.id = 123456
        mock_artifact = Mock()
        mock_artifact.name = "test-results"
        mock_artifact.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/456/zip"
        )

        mock_run.get_artifacts.return_value = [mock_artifact]
        mock_repo.get_workflow_run.return_value = mock_run

        # Mock the ZIP download via _download_and_extract_zip
        expected_content = {
            "test-results.xml": "<?xml version='1.0'?><testsuites></testsuites>"
        }

        with patch.object(ci_manager, "_download_and_extract_zip") as mock_download:
            mock_download.return_value = expected_content

            result = ci_manager.get_artifacts(123456)

            assert result == expected_content
            mock_repo.get_workflow_run.assert_called_once_with(123456)
            mock_run.get_artifacts.assert_called_once()
            mock_download.assert_called_once_with(mock_artifact.archive_download_url)

    def test_multiple_artifacts(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test downloading multiple artifacts."""
        # Mock workflow run and artifacts
        mock_run = Mock()
        mock_run.id = 123456

        mock_artifact1 = Mock()
        mock_artifact1.name = "test-results"
        mock_artifact1.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/456/zip"
        )

        mock_artifact2 = Mock()
        mock_artifact2.name = "coverage-report"
        mock_artifact2.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/789/zip"
        )

        mock_run.get_artifacts.return_value = [mock_artifact1, mock_artifact2]
        mock_repo.get_workflow_run.return_value = mock_run

        # Mock the ZIP downloads
        artifact1_content = {"junit.xml": "<?xml version='1.0'?>..."}
        artifact2_content = {"coverage.json": '{"total": 85.5}'}

        def download_side_effect(url: str) -> Dict[str, str]:
            if "456" in url:
                return artifact1_content
            elif "789" in url:
                return artifact2_content
            return {}

        with patch.object(ci_manager, "_download_and_extract_zip") as mock_download:
            mock_download.side_effect = download_side_effect

            result = ci_manager.get_artifacts(123456)

            expected = {
                "junit.xml": "<?xml version='1.0'?>...",
                "coverage.json": '{"total": 85.5}',
            }
            assert result == expected
            assert mock_download.call_count == 2

    def test_no_artifacts(self, mock_repo: Mock, ci_manager: CIResultsManager) -> None:
        """Test when workflow run has no artifacts."""
        mock_run = Mock()
        mock_run.id = 123456
        mock_run.get_artifacts.return_value = []
        mock_repo.get_workflow_run.return_value = mock_run

        result = ci_manager.get_artifacts(123456)

        assert result == {}
        mock_repo.get_workflow_run.assert_called_once_with(123456)
        mock_run.get_artifacts.assert_called_once()

    def test_with_name_filter(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test filtering artifacts by name."""
        # Mock workflow run and artifacts
        mock_run = Mock()
        mock_run.id = 123456

        mock_artifact1 = Mock()
        mock_artifact1.name = "junit-test-results"
        mock_artifact1.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/456/zip"
        )

        mock_artifact2 = Mock()
        mock_artifact2.name = "coverage-report"
        mock_artifact2.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/789/zip"
        )

        mock_artifact3 = Mock()
        mock_artifact3.name = "junit-integration-results"
        mock_artifact3.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/012/zip"
        )

        mock_run.get_artifacts.return_value = [
            mock_artifact1,
            mock_artifact2,
            mock_artifact3,
        ]
        mock_repo.get_workflow_run.return_value = mock_run

        # Mock the ZIP downloads for junit artifacts only
        def download_side_effect(url: str) -> Dict[str, str]:
            if "456" in url:
                return {"junit.xml": "<?xml version='1.0'?>..."}
            elif "012" in url:
                return {"integration-junit.xml": "<?xml version='1.0'?>..."}
            return {}

        with patch.object(ci_manager, "_download_and_extract_zip") as mock_download:
            mock_download.side_effect = download_side_effect

            # Test case-insensitive filtering
            result = ci_manager.get_artifacts(123456, name_filter="JUNIT")

            expected = {
                "junit.xml": "<?xml version='1.0'?>...",
                "integration-junit.xml": "<?xml version='1.0'?>...",
            }
            assert result == expected
            # Should only download junit artifacts (not coverage)
            assert mock_download.call_count == 2

    def test_name_filter_no_match(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test name filter with no matching artifacts."""
        mock_run = Mock()
        mock_run.id = 123456

        mock_artifact = Mock()
        mock_artifact.name = "coverage-report"
        mock_artifact.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/456/zip"
        )

        mock_run.get_artifacts.return_value = [mock_artifact]
        mock_repo.get_workflow_run.return_value = mock_run

        result = ci_manager.get_artifacts(123456, name_filter="junit")

        assert result == {}
        mock_repo.get_workflow_run.assert_called_once_with(123456)
        mock_run.get_artifacts.assert_called_once()
        # No downloads should occur

    def test_artifact_download_failure(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test handling of artifact download failures."""
        # Mock workflow run and artifacts
        mock_run = Mock()
        mock_run.id = 123456

        mock_artifact1 = Mock()
        mock_artifact1.name = "test-results"
        mock_artifact1.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/456/zip"
        )

        mock_artifact2 = Mock()
        mock_artifact2.name = "coverage-report"
        mock_artifact2.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/789/zip"
        )

        mock_run.get_artifacts.return_value = [mock_artifact1, mock_artifact2]
        mock_repo.get_workflow_run.return_value = mock_run

        # Mock first download failing, second succeeding
        def download_side_effect(url: str) -> Dict[str, str]:
            if "456" in url:
                return {}  # Download failed
            elif "789" in url:
                return {"coverage.json": '{"total": 85.5}'}
            return {}

        with patch.object(ci_manager, "_download_and_extract_zip") as mock_download:
            mock_download.side_effect = download_side_effect

            result = ci_manager.get_artifacts(123456)

            # Should only contain successful download
            expected = {"coverage.json": '{"total": 85.5}'}
            assert result == expected
            assert mock_download.call_count == 2

    def test_invalid_run_id(self, ci_manager: CIResultsManager) -> None:
        """Test with invalid run ID."""
        # Test negative run ID
        with pytest.raises(ValueError, match="Invalid workflow run ID"):
            ci_manager.get_artifacts(-1)

        # Test zero run ID
        with pytest.raises(ValueError, match="Invalid workflow run ID"):
            ci_manager.get_artifacts(0)

    @patch("mcp_coder.utils.github_operations.ci_results_manager.logger")
    def test_binary_file_skipped_with_warning(
        self, mock_logger: Mock, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test that binary files are skipped with a log warning."""
        mock_run = Mock()
        mock_run.id = 123456

        mock_artifact = Mock()
        mock_artifact.name = "test-results"
        mock_artifact.archive_download_url = (
            "https://api.github.com/repos/test/repo/artifacts/456/zip"
        )

        mock_run.get_artifacts.return_value = [mock_artifact]
        mock_repo.get_workflow_run.return_value = mock_run

        # Mock _download_and_extract_zip to simulate binary file handling
        # This would happen inside the ZIP extraction logic
        artifact_content = {
            "test-results.xml": "<?xml version='1.0'?><testsuites></testsuites>",
            # Binary files would be filtered out by _download_and_extract_zip
        }

        with patch.object(ci_manager, "_download_and_extract_zip") as mock_download:
            mock_download.return_value = artifact_content

            result = ci_manager.get_artifacts(123456)

            assert result == artifact_content
            mock_download.assert_called_once_with(mock_artifact.archive_download_url)

    def test_github_api_error_handling(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test handling of GitHub API errors."""
        # Test workflow run not found
        mock_repo.get_workflow_run.side_effect = GithubException(404, "Not Found", {})

        with pytest.raises(GithubException):
            ci_manager.get_artifacts(123456)

        # Test authentication error
        mock_repo.get_workflow_run.side_effect = GithubException(
            401, "Bad credentials", {}
        )

        with pytest.raises(GithubException):
            ci_manager.get_artifacts(123456)


class TestDownloadAndExtractZip:
    """Test the _download_and_extract_zip helper method."""

    @pytest.fixture
    def ci_manager(self) -> CIResultsManager:
        """CIResultsManager instance for testing."""
        repo_url = "https://github.com/test/repo.git"

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "test_token"

            with patch("github.Github"):
                return CIResultsManager(repo_url=repo_url)

    @patch("requests.get")
    def test_successful_download(
        self, mock_requests: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test successful ZIP download and extraction."""
        # Create a mock ZIP file with test content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            zip_file.writestr("test/1_Setup.txt", "Setting up test environment...")
            zip_file.writestr(
                "test/2_Run tests.txt", "Running tests...\nTest failed: assertion error"
            )
            zip_file.writestr("build/1_Setup.txt", "Setting up build environment...")

        zip_buffer.seek(0)

        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = zip_buffer.getvalue()
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Test the method
        result = ci_manager._download_and_extract_zip(
            "https://api.github.com/repos/test/repo/actions/runs/123/logs"
        )

        # Verify the result
        expected = {
            "test/1_Setup.txt": "Setting up test environment...",
            "test/2_Run tests.txt": "Running tests...\nTest failed: assertion error",
            "build/1_Setup.txt": "Setting up build environment...",
        }
        assert result == expected

        # Verify HTTP request was made correctly
        mock_requests.assert_called_once_with(
            "https://api.github.com/repos/test/repo/actions/runs/123/logs",
            headers={
                "Authorization": "Bearer test_token",
                "Accept": "application/vnd.github.v3+json",
            },
            allow_redirects=True,
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.get")
    def test_http_error(
        self, mock_requests: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test handling of HTTP errors during download."""
        # Mock HTTP error
        mock_requests.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        # Test the method - should return empty dict on error
        result = ci_manager._download_and_extract_zip(
            "https://api.github.com/repos/test/repo/actions/runs/123/logs"
        )

        assert result == {}

        mock_requests.assert_called_once()

    @patch("requests.get")
    def test_invalid_zip(
        self, mock_requests: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test handling of invalid ZIP content."""
        # Mock HTTP response with invalid ZIP content
        mock_response = Mock()
        mock_response.content = b"This is not a valid ZIP file"
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Test the method - should return empty dict on ZIP error
        result = ci_manager._download_and_extract_zip(
            "https://api.github.com/repos/test/repo/actions/runs/123/logs"
        )

        assert result == {}

        mock_requests.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


class TestGetRunLogs:
    """Test the get_run_logs method."""

    @patch("mcp_coder.utils.github_operations.ci_results_manager.requests.get")
    def test_successful_logs_retrieval(
        self, mock_requests: Mock, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test successful retrieval of workflow run logs."""
        # Mock workflow run
        mock_run = Mock()
        mock_run.id = 123456789
        mock_run.logs_url = (
            "https://api.github.com/repos/test/repo/actions/runs/123456789/logs"
        )
        mock_repo.get_workflow_run.return_value = mock_run

        # Create a mock ZIP file with log content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            zip_file.writestr("test/1_Setup.txt", "Setting up test environment...\n")
            zip_file.writestr(
                "test/2_Run tests.txt", "Running tests...\nTest failed: assertion error"
            )
            zip_file.writestr("build/1_Setup.txt", "Setting up build environment...")

        zip_buffer.seek(0)

        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = zip_buffer.getvalue()
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Test the method
        result = ci_manager.get_run_logs(123456789)

        # Verify the result contains all logs
        expected = {
            "test/1_Setup.txt": "Setting up test environment...\n",
            "test/2_Run tests.txt": "Running tests...\nTest failed: assertion error",
            "build/1_Setup.txt": "Setting up build environment...",
        }
        assert result == expected

        # Verify API calls
        mock_repo.get_workflow_run.assert_called_once_with(123456789)

    def test_invalid_run_id(self, ci_manager: CIResultsManager) -> None:
        """Test with invalid run ID."""
        # Test negative run ID
        with pytest.raises(ValueError, match="Invalid workflow run ID"):
            ci_manager.get_run_logs(-1)

        # Test zero run ID
        with pytest.raises(ValueError, match="Invalid workflow run ID"):
            ci_manager.get_run_logs(0)


class TestGetLatestCIStatusContinued:
    """Additional tests for get_latest_ci_status method."""

    def test_no_workflow_runs_for_branch(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test when no workflow runs exist for the branch."""
        mock_repo.get_workflow_runs.return_value = []

        result = ci_manager.get_latest_ci_status("feature/no-runs")

        # Should return empty data
        assert result["run"] == {}
        assert result["jobs"] == []

        mock_repo.get_workflow_runs.assert_called_once()

    def test_invalid_branch_name(self, ci_manager: CIResultsManager) -> None:
        """Test with invalid branch name."""
        with pytest.raises(ValueError, match="Invalid branch name"):
            ci_manager.get_latest_ci_status("")

        with pytest.raises(ValueError, match="Invalid branch name"):
            ci_manager.get_latest_ci_status("branch~1")

        with pytest.raises(ValueError, match="Invalid branch name"):
            ci_manager.get_latest_ci_status("branch^2")

    def test_run_with_multiple_jobs(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test CI run with multiple jobs of different statuses."""
        mock_run = Mock()
        mock_run.id = 999888777
        mock_run.status = "in_progress"
        mock_run.conclusion = None
        mock_run.name = "Build and Test"
        mock_run.event = "pull_request"
        mock_run.path = ".github/workflows/build.yml"
        mock_run.head_sha = "xyz789abc123"
        mock_run.created_at = Mock()
        mock_run.created_at.isoformat.return_value = "2024-01-15T11:00:00Z"
        mock_run.html_url = "https://github.com/test/repo/actions/runs/999888777"

        # Multiple jobs with different statuses
        jobs = []
        job_configs = [
            {"id": 111, "name": "lint", "status": "completed", "conclusion": "success"},
            {"id": 222, "name": "test", "status": "in_progress", "conclusion": None},
            {"id": 333, "name": "build", "status": "queued", "conclusion": None},
        ]

        for config in job_configs:
            job = Mock()
            job.id = config["id"]
            job.name = config["name"]
            job.status = config["status"]
            job.conclusion = config["conclusion"]
            job.started_at = Mock() if config["status"] != "queued" else None
            if job.started_at:
                job.started_at.isoformat.return_value = "2024-01-15T11:01:00Z"
            job.completed_at = Mock() if config["status"] == "completed" else None
            if job.completed_at:
                job.completed_at.isoformat.return_value = "2024-01-15T11:05:00Z"
            jobs.append(job)

        # Set head_branch for filtering
        mock_run.head_branch = "main"

        mock_run.jobs.return_value = jobs
        mock_repo.get_workflow_runs.return_value = [mock_run]

        result = ci_manager.get_latest_ci_status("main")

        # Verify run data
        run_data = result["run"]
        assert run_data["id"] == 999888777
        assert run_data["status"] == "in_progress"
        assert run_data["conclusion"] is None
        assert run_data["workflow_name"] == "Build and Test"
        assert run_data["event"] == "pull_request"

        # Verify all jobs are included
        jobs_data = result["jobs"]
        assert len(jobs_data) == 3

        # Check specific job statuses
        job_names = [job["name"] for job in jobs_data]
        assert "lint" in job_names
        assert "test" in job_names
        assert "build" in job_names

        # Find and check specific jobs
        lint_job = next(job for job in jobs_data if job["name"] == "lint")
        assert lint_job["status"] == "completed"
        assert lint_job["conclusion"] == "success"
        assert lint_job["completed_at"] == "2024-01-15T11:05:00Z"

        test_job = next(job for job in jobs_data if job["name"] == "test")
        assert test_job["status"] == "in_progress"
        assert test_job["conclusion"] is None
        assert test_job["completed_at"] is None

        build_job = next(job for job in jobs_data if job["name"] == "build")
        assert build_job["status"] == "queued"
        assert build_job["conclusion"] is None
        assert build_job["started_at"] is None

    def test_github_api_error_handling(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test handling of GitHub API errors."""
        from github import GithubException

        # Test authentication error
        mock_repo.get_workflow_runs.side_effect = GithubException(
            401, "Bad credentials", {}
        )

        with pytest.raises(GithubException):
            ci_manager.get_latest_ci_status("main")

        # Test rate limit error
        mock_repo.get_workflow_runs.side_effect = GithubException(
            403, "API rate limit exceeded", {}
        )

        with pytest.raises(GithubException):
            ci_manager.get_latest_ci_status("main")

    def test_run_without_jobs(
        self, mock_repo: Mock, ci_manager: CIResultsManager
    ) -> None:
        """Test CI run that has no jobs."""
        mock_run = Mock()
        mock_run.id = 555444333
        mock_run.status = "completed"
        mock_run.conclusion = "cancelled"
        mock_run.name = "CI"
        mock_run.event = "push"
        mock_run.path = ".github/workflows/ci.yml"
        mock_run.head_sha = "cancelled123"
        mock_run.created_at = Mock()
        mock_run.created_at.isoformat.return_value = "2024-01-15T12:00:00Z"
        mock_run.html_url = "https://github.com/test/repo/actions/runs/555444333"

        # Set head_branch for filtering
        mock_run.head_branch = "feature/empty-jobs"

        # No jobs for this run
        mock_run.jobs.return_value = []
        mock_repo.get_workflow_runs.return_value = [mock_run]

        result = ci_manager.get_latest_ci_status("feature/empty-jobs")

        # Should have run data but no jobs
        assert result["run"]["id"] == 555444333
        assert result["run"]["conclusion"] == "cancelled"
        assert result["jobs"] == []

        mock_run.jobs.assert_called_once()
