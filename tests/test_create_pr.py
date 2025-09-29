"""Legacy test file - functionality has been reorganized into focused test modules.

The tests from this file have been reorganized into:
- tests/workflows/create_pr/test_file_operations.py: File operations
- tests/workflows/create_pr/test_parsing.py: PR parsing functionality
- tests/workflows/create_pr/test_prerequisites.py: Prerequisites checking
- tests/workflows/create_pr/test_generation.py: PR generation functionality
- tests/workflows/create_pr/test_repository.py: Repository management
- tests/workflows/create_pr/test_main.py: Main workflow tests

This file is kept for backwards compatibility but can be removed.
"""

# Import all test classes from the organized modules to maintain backwards compatibility
from .workflows.create_pr.test_file_operations import (
    TestDeleteStepsDirectory,
    TestTruncateTaskTracker,
)
from .workflows.create_pr.test_generation import TestGeneratePrSummary
from .workflows.create_pr.test_main import TestMainWorkflow
from .workflows.create_pr.test_parsing import TestParsePrSummary
from .workflows.create_pr.test_prerequisites import TestCheckPrerequisites
from .workflows.create_pr.test_repository import (
    TestCleanupRepository,
    TestCreatePullRequest,
)

# All test implementations have been moved to focused modules
# This file now serves as a backwards-compatible import point

__all__ = [
    "TestDeleteStepsDirectory",
    "TestTruncateTaskTracker",
    "TestGeneratePrSummary",
    "TestMainWorkflow",
    "TestParsePrSummary",
    "TestCheckPrerequisites",
    "TestCleanupRepository",
    "TestCreatePullRequest",
]
