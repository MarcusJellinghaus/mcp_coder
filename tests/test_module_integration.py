"""Test module integration and exports for git operations."""

import pytest


class TestModuleIntegration:
    """Test that git operations are properly exported and accessible."""

    def test_shim_import(self) -> None:
        """Test importing directly from the mcp_workspace_git shim module."""
        from mcp_coder.mcp_workspace_git import (
            CommitResult,
            commit_all_changes,
            commit_staged_files,
            get_full_status,
            is_git_repository,
            stage_all_changes,
        )

        # Verify functions are callable
        assert callable(commit_all_changes)
        assert callable(commit_staged_files)
        assert callable(get_full_status)
        assert callable(is_git_repository)
        assert callable(stage_all_changes)

        # Verify CommitResult is a type
        assert CommitResult is not None

    def test_utils_module_import(self) -> None:
        """Test importing surviving re-exports from utils module."""
        from mcp_coder.utils import (
            CommitResult,
            branch_exists,
            checkout_branch,
            commit_all_changes,
            commit_staged_files,
            fetch_remote,
            get_branch_diff,
            get_current_branch_name,
            get_default_branch_name,
            get_full_status,
            get_git_diff_for_commit,
            get_github_repository_url,
            git_push,
            is_working_directory_clean,
            stage_all_changes,
        )

        # Verify functions are callable
        assert callable(commit_all_changes)
        assert callable(commit_staged_files)
        assert callable(get_full_status)

        # Verify CommitResult is available
        assert CommitResult is not None

    def test_main_package_public_api_import(self) -> None:
        """Test importing public API from main mcp_coder package."""
        from mcp_coder import (
            CommitResult,
            commit_all_changes,
            commit_staged_files,
            get_full_status,
            is_git_repository,
        )

        # Verify core public functions are callable
        assert callable(commit_all_changes)
        assert callable(commit_staged_files)
        assert callable(get_full_status)
        assert callable(is_git_repository)

        # Verify CommitResult is available
        assert CommitResult is not None

    def test_function_attributes_preserved(self) -> None:
        """Test that function attributes like docstrings and annotations are preserved."""
        from mcp_coder import commit_all_changes, is_git_repository

        # Check docstrings are preserved
        assert commit_all_changes.__doc__ is not None
        assert (
            "stage all unstaged changes and commit them" in commit_all_changes.__doc__
        )

        assert is_git_repository.__doc__ is not None
        assert (
            "Check if the project directory is a git repository"
            in is_git_repository.__doc__
        )

        # Check type annotations are preserved
        assert hasattr(commit_all_changes, "__annotations__")
        assert hasattr(is_git_repository, "__annotations__")

    def test_commit_result_type_import(self) -> None:
        """Test that CommitResult TypedDict can be imported and used."""
        from mcp_coder import CommitResult

        # Verify it's the expected TypedDict
        assert hasattr(CommitResult, "__annotations__")

        # Create a sample CommitResult to verify structure
        sample_result: CommitResult = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        assert sample_result["success"] is True
        assert sample_result["commit_hash"] == "abc1234"
        assert sample_result["error"] is None

    def test_all_exports_available(self) -> None:
        """Test that __all__ exports are properly defined and available."""
        import mcp_coder as main_module
        import mcp_coder.utils as utils_module

        # Check utils module has __all__ defined
        assert hasattr(utils_module, "__all__")
        utils_all = utils_module.__all__

        # Verify surviving git functions are in utils __all__
        git_functions = [
            "CommitResult",
            "branch_exists",
            "checkout_branch",
            "commit_all_changes",
            "commit_staged_files",
            "fetch_remote",
            "get_branch_diff",
            "get_current_branch_name",
            "get_default_branch_name",
            "get_full_status",
            "get_git_diff_for_commit",
            "get_github_repository_url",
            "git_push",
            "is_working_directory_clean",
            "stage_all_changes",
        ]

        for func_name in git_functions:
            assert func_name in utils_all, f"{func_name} not in utils.__all__"
            assert hasattr(
                utils_module, func_name
            ), f"{func_name} not available in utils module"

        # Verify dead symbols are removed from utils __all__
        dead_symbols = [
            "git_move",
            "is_file_tracked",
            "get_staged_changes",
            "get_unstaged_changes",
            "stage_specific_files",
        ]

        for func_name in dead_symbols:
            assert (
                func_name not in utils_all
            ), f"{func_name} should be removed from utils.__all__"

        # Check main module has __all__ defined
        assert hasattr(main_module, "__all__")
        main_all = main_module.__all__

        # Verify public API functions are in main __all__
        public_api_functions = [
            "CommitResult",
            "commit_all_changes",
            "commit_staged_files",
            "get_full_status",
            "is_git_repository",
        ]

        for func_name in public_api_functions:
            assert func_name in main_all, f"{func_name} not in main.__all__"
            assert hasattr(
                main_module, func_name
            ), f"{func_name} not available in main module"

    def test_no_circular_imports(self) -> None:
        """Test that there are no circular import issues."""
        # This test passes if we can import without ImportError
        try:
            import mcp_coder
            import mcp_coder.mcp_workspace_git
            import mcp_coder.utils

            # Try accessing functions through different paths
            func1 = mcp_coder.is_git_repository
            func2 = mcp_coder.mcp_workspace_git.is_git_repository

            # Verify they're the same function
            assert func1 is func2

        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
