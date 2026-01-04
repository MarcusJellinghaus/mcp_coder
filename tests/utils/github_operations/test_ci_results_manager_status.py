"""Tests for CIResultsManager get_latest_ci_status method."""

import io
import zipfile
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch

import pytest
import requests
from github import GithubException

from mcp_coder.utils.github_operations import CIResultsManager, CIStatusData


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
        """Test with invalid branch name returns empty data (decorator catches ValueError)."""
        # Empty branch name - returns default empty data
        result = ci_manager.get_latest_ci_status("")
        assert result["run"] == {}
        assert result["jobs"] == []

        # Invalid character ~ - returns default empty data
        result = ci_manager.get_latest_ci_status("branch~1")
        assert result["run"] == {}
        assert result["jobs"] == []

        # Invalid character ^ - returns default empty data
        result = ci_manager.get_latest_ci_status("branch^2")
        assert result["run"] == {}
        assert result["jobs"] == []

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
