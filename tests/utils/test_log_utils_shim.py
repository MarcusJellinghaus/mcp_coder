"""Tests for log_utils shim — verifies app-specific log suppression."""

import logging

from mcp_coder.utils.log_utils import setup_logging


class TestLogSuppressionShim:
    """Verify setup_logging() suppresses noisy third-party loggers."""

    def test_urllib3_suppressed_after_setup(self) -> None:
        """urllib3.connectionpool should be at INFO after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("urllib3.connectionpool").level == logging.INFO

    def test_httpx_suppressed_after_setup(self) -> None:
        """httpx should be at WARNING after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("httpx").level == logging.WARNING

    def test_httpcore_suppressed_after_setup(self) -> None:
        """httpcore should be at WARNING after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("httpcore").level == logging.WARNING

    def test_github_suppressed_after_setup(self) -> None:
        """github.Requester should be at INFO after setup_logging()."""
        setup_logging("DEBUG")
        assert logging.getLogger("github.Requester").level == logging.INFO
