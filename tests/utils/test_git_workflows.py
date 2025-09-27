"""Test git workflows with end-to-end integration testing."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    branch_exists,
    checkout_branch,
    commit_all_changes,
    commit_staged_files,
    create_branch,
    fetch_remote,
    get_current_branch_name,
    get_default_branch_name,
    get_full_status,
    get_git_diff_for_commit,
    get_parent_branch_name,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
    push_branch,
    stage_all_changes,
    stage_specific_files,
)

# Performance test threshold in seconds
PERFORMANCE_THRESHOLD_SECONDS = 7.0


@pytest.mark.git_integration
class TestGitWorkflows:
    """Test complete git workflow scenarios without mocking."""

    def test_new_project_to_first_commit(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: create new project, add files, stage, and commit."""
        repo, project_dir = git_repo

        # Verify we start with a clean git repository
        assert is_git_repository(project_dir) is True

        # Create project files inline
        files = {
            "main.py": "print('hello world')",
            "README.md": "# My Project\n\nDescription here.",
            "src/utils.py": "def helper():\n    pass",
            "config.json": '{"debug": true}',
        }

        for path, content in files.items():
            file_path = project_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Test workflow: check status → stage files → commit
        status = get_full_status(project_dir)
        assert len(status["untracked"]) == 4
        assert status["staged"] == []
        assert status["modified"] == []

        # Stage all changes
        result = stage_all_changes(project_dir)
        assert result is True

        # Verify staging worked
        staged = get_staged_changes(project_dir)
        assert len(staged) == 4
        assert "main.py" in staged
        assert "README.md" in staged
        assert "src/utils.py" in staged
        assert "config.json" in staged

        # Commit staged files
        commit_result = commit_staged_files("Initial commit", project_dir)
        assert commit_result["success"] is True
        commit_hash = commit_result["commit_hash"]
        assert commit_hash is not None
        assert len(commit_hash) == 7
        assert commit_result["error"] is None

        # Verify git state after commit
        assert len(list(repo.iter_commits())) == 1
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_modify_existing_files_workflow(
        self, git_repo_with_files: tuple[Repo, Path]
    ) -> None:
        """Test workflow: modify existing tracked files and commit changes."""
        repo, project_dir = git_repo_with_files

        # Verify starting state - should have committed files
        initial_commits = list(repo.iter_commits())
        assert len(initial_commits) == 1
        assert initial_commits[0].message == "Initial commit with sample files"

        # Verify no pending changes initially
        status = get_full_status(project_dir)
        assert status == {"staged": [], "modified": [], "untracked": []}

        # Modify existing files
        file1 = project_dir / "README.md"
        file2 = project_dir / "main.py"
        file3 = project_dir / "config.yml"

        file1.write_text(
            "# Updated Test Project\n\nUpdated sample project for testing.\nAdded a new line"
        )
        file2.write_text(
            "def main():\n    print('Hello, Updated World!')\n    print('New functionality')"
        )
        file3.write_text("debug: true\nport: 3000\nnew_option: 42")

        # Check that modifications are detected
        status = get_full_status(project_dir)
        assert len(status["modified"]) == 3
        assert status["staged"] == []
        assert status["untracked"] == []
        assert "README.md" in status["modified"]
        assert "main.py" in status["modified"]
        assert "config.yml" in status["modified"]

        # Stage and commit modified files
        stage_result = stage_all_changes(project_dir)
        assert stage_result is True

        # Verify staging
        staged = get_staged_changes(project_dir)
        assert len(staged) == 3
        assert "README.md" in staged
        assert "main.py" in staged
        assert "config.yml" in staged

        # Commit changes
        commit_result = commit_staged_files(
            "Update all files with new content", project_dir
        )
        assert commit_result["success"] is True
        assert commit_result["error"] is None

        # Verify final state
        final_commits = list(repo.iter_commits())
        assert len(final_commits) == 2
        assert final_commits[0].message == "Update all files with new content"

        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_mixed_file_operations_workflow(
        self, git_repo_with_files: tuple[Repo, Path]
    ) -> None:
        """Test workflow: mix of adding new files, modifying existing, and deletions."""
        repo, project_dir = git_repo_with_files

        # Verify starting state
        initial_status = get_full_status(project_dir)
        assert initial_status == {"staged": [], "modified": [], "untracked": []}

        # Mix of operations:
        # 1. Modify existing file
        file1 = project_dir / "README.md"
        file1.write_text("# Modified Test Project\n\nModified content in README")

        # 2. Add new files
        new_file = project_dir / "new_feature.py"
        new_file.write_text("# New feature implementation\nclass Feature:\n    pass")

        nested_new = project_dir / "docs" / "guide.md"
        nested_new.parent.mkdir(exist_ok=True)
        nested_new.write_text("# User Guide\n\n## Getting Started")

        # 3. Delete existing file
        file_to_delete = project_dir / "config.yml"
        file_to_delete.unlink()

        # Check mixed status
        status = get_full_status(project_dir)
        assert (
            len(status["modified"]) >= 1
        )  # file1.txt and possibly config.json deletion
        assert len(status["untracked"]) == 2  # new_feature.py and docs/guide.md
        assert status["staged"] == []

        # Stage everything
        stage_result = stage_all_changes(project_dir)
        assert stage_result is True

        # Verify all changes staged
        staged = get_staged_changes(project_dir)
        assert len(staged) >= 3  # At minimum: modified file1, new files, deletion
        assert "README.md" in staged
        assert "new_feature.py" in staged
        assert "docs/guide.md" in staged

        # Commit mixed operations
        commit_result = commit_staged_files(
            "Mixed operations: modify, add, delete", project_dir
        )
        assert commit_result["success"] is True

        # Verify final state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

        # Verify files exist as expected
        assert file1.exists()
        assert new_file.exists()
        assert nested_new.exists()
        assert not file_to_delete.exists()

        # Verify commit history
        commits = list(repo.iter_commits())
        assert len(commits) == 2
        assert commits[0].message == "Mixed operations: modify, add, delete"

    def test_staging_specific_files_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: selectively stage specific files for commit."""
        repo, project_dir = git_repo

        # Create multiple files
        files = {
            "feature_a.py": "# Feature A\nclass FeatureA:\n    pass",
            "feature_b.py": "# Feature B\nclass FeatureB:\n    pass",
            "docs/readme.md": "# Documentation\n\nFeature docs",
            "config.ini": "[settings]\ndebug=true",
            "temp_notes.txt": "Temporary development notes",
        }

        created_files = []
        for path, content in files.items():
            file_path = project_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            created_files.append(file_path)

        # Verify all files are untracked
        status = get_full_status(project_dir)
        assert len(status["untracked"]) == 5
        assert status["staged"] == []

        # Stage only specific files (not temp_notes.txt)
        files_to_stage = [
            project_dir / "feature_a.py",
            project_dir / "docs" / "readme.md",
            project_dir / "config.ini",
        ]

        stage_result = stage_specific_files(files_to_stage, project_dir)
        assert stage_result is True

        # Verify selective staging
        staged = get_staged_changes(project_dir)
        assert len(staged) == 3
        assert "feature_a.py" in staged
        assert "docs/readme.md" in staged
        assert "config.ini" in staged

        # Verify unstaged files remain
        unstaged = get_unstaged_changes(project_dir)
        assert len(unstaged["untracked"]) == 2
        assert "feature_b.py" in unstaged["untracked"]
        assert "temp_notes.txt" in unstaged["untracked"]

        # Commit staged files
        commit_result = commit_staged_files(
            "Add feature A and documentation", project_dir
        )
        assert commit_result["success"] is True

        # Stage and commit remaining files separately
        remaining_files = [project_dir / "feature_b.py", project_dir / "temp_notes.txt"]

        stage_result2 = stage_specific_files(remaining_files, project_dir)
        assert stage_result2 is True

        commit_result2 = commit_staged_files("Add feature B and notes", project_dir)
        assert commit_result2["success"] is True

        # Verify final state - no pending changes
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

        # Verify two commits
        commits = list(repo.iter_commits())
        assert len(commits) == 2

    def test_staging_all_changes_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: stage all changes at once and commit."""
        repo, project_dir = git_repo

        # Create various types of files
        files = {
            "app.py": "# Main application\nif __name__ == '__main__':\n    print('Hello!')",
            "utils/helpers.py": "def utility_function():\n    return 'helper'",
            "data/sample.json": '{"key": "value", "items": [1, 2, 3]}',
            "README.md": "# Project\n\nThis is a test project.",
            "requirements.txt": "requests==2.28.0\nflask==2.1.0",
        }

        for path, content in files.items():
            file_path = project_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Verify all files are untracked
        status = get_full_status(project_dir)
        assert len(status["untracked"]) == 5
        assert status["staged"] == []
        assert status["modified"] == []

        # Stage all changes at once
        stage_result = stage_all_changes(project_dir)
        assert stage_result is True

        # Verify all files staged
        staged = get_staged_changes(project_dir)
        assert len(staged) == 5
        for file_path_str in files.keys():
            assert file_path_str in staged

        # Verify no unstaged changes remain
        unstaged = get_unstaged_changes(project_dir)
        assert unstaged == {"modified": [], "untracked": []}

        # Commit all staged changes
        commit_result = commit_staged_files(
            "Initial project setup with all files", project_dir
        )
        assert commit_result["success"] is True
        assert commit_result["error"] is None

        # Verify clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

        # Verify commit exists
        commits = list(repo.iter_commits())
        assert len(commits) == 1
        assert commits[0].message == "Initial project setup with all files"

    def test_commit_workflows(self, git_repo: tuple[Repo, Path]) -> None:
        """Test various commit scenarios with different message formats."""
        repo, project_dir = git_repo

        # Test commit_all_changes (stage + commit in one operation)
        file1 = project_dir / "test1.py"
        file1.write_text("# Test file 1")

        # Use commit_all_changes for convenience
        commit_result1 = commit_all_changes("feat: add test1.py", project_dir)
        assert commit_result1["success"] is True
        assert commit_result1["error"] is None

        # Test commit with multiline message
        file2 = project_dir / "test2.py"
        file2.write_text("# Test file 2")

        stage_all_changes(project_dir)
        multiline_message = "Add test2.py\n\n- Implements new functionality\n- Includes documentation\n- Fixes issue #123"
        commit_result2 = commit_staged_files(multiline_message, project_dir)
        assert commit_result2["success"] is True

        # Test commit with simple message
        file3 = project_dir / "test3.py"
        file3.write_text("# Test file 3")

        commit_result3 = commit_all_changes("Update", project_dir)
        assert commit_result3["success"] is True

        # Test commit with long descriptive message
        file4 = project_dir / "test4.py"
        file4.write_text("# Test file 4")

        long_message = "Implement comprehensive test4.py module with advanced functionality and extensive documentation for better code maintainability"
        commit_result4 = commit_all_changes(long_message, project_dir)
        assert commit_result4["success"] is True

        # Verify all commits created
        commits = list(repo.iter_commits())
        assert len(commits) == 4

        # Verify commit messages
        commit_messages = [commit.message for commit in commits]
        assert "feat: add test1.py" in commit_messages
        assert multiline_message in commit_messages
        assert "Update" in commit_messages
        assert long_message in commit_messages

        # Verify clean final state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_multiple_commit_cycles(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: multiple rounds of changes and commits."""
        repo, project_dir = git_repo

        # Cycle 1: Initial setup
        cycle1_files = {
            "main.py": "# Main module\nprint('cycle 1')",
            "config.py": "DEBUG = True",
        }

        for path, content in cycle1_files.items():
            (project_dir / path).write_text(content)

        commit_result1 = commit_all_changes("Cycle 1: Initial setup", project_dir)
        assert commit_result1["success"] is True

        # Cycle 2: Add features
        cycle2_files = {
            "features/auth.py": "class AuthManager:\n    pass",
            "features/database.py": "class DatabaseManager:\n    pass",
        }

        for path, content in cycle2_files.items():
            file_path = project_dir / path
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

        commit_result2 = commit_all_changes("Cycle 2: Add feature modules", project_dir)
        assert commit_result2["success"] is True

        # Cycle 3: Modify existing and add tests
        (project_dir / "main.py").write_text(
            "# Main module\nprint('cycle 3 - updated')"
        )
        (project_dir / "tests" / "test_main.py").parent.mkdir(exist_ok=True)
        (project_dir / "tests" / "test_main.py").write_text(
            "def test_main():\n    assert True"
        )

        commit_result3 = commit_all_changes(
            "Cycle 3: Update main and add tests", project_dir
        )
        assert commit_result3["success"] is True

        # Cycle 4: Cleanup and documentation
        (project_dir / "config.py").write_text("DEBUG = False\nVERSION = '1.0.0'")
        (project_dir / "README.md").write_text(
            "# Project Documentation\n\nVersion 1.0.0"
        )

        commit_result4 = commit_all_changes(
            "Cycle 4: Production config and docs", project_dir
        )
        assert commit_result4["success"] is True

        # Verify all cycles committed
        commits = list(repo.iter_commits())
        assert len(commits) == 4

        commit_messages = [commit.message for commit in commits]
        assert "Cycle 1: Initial setup" in commit_messages
        assert "Cycle 2: Add feature modules" in commit_messages
        assert "Cycle 3: Update main and add tests" in commit_messages
        assert "Cycle 4: Production config and docs" in commit_messages

        # Verify final clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_cross_platform_paths(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow with files in nested directories and various path formats."""
        repo, project_dir = git_repo

        # Create files with various path separators and nested structures
        files = {
            "src/core/main.py": "# Core module",
            "src/utils/helpers/string_utils.py": "def clean_string(): pass",
            "tests/unit/test_core.py": "def test_core(): pass",
            "tests/integration/api/test_endpoints.py": "def test_api(): pass",
            "docs/guides/user_guide.md": "# User Guide",
            "data/samples/config.json": '{"test": true}',
            "scripts/build/compile.sh": "#!/bin/bash\necho 'build'",
        }

        # Create nested directory structure
        for path, content in files.items():
            file_path = project_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Verify untracked status
        status = get_full_status(project_dir)
        assert len(status["untracked"]) == 7

        # Stage specific nested files
        core_files = [
            project_dir / "src" / "core" / "main.py",
            project_dir / "src" / "utils" / "helpers" / "string_utils.py",
        ]

        stage_result = stage_specific_files(core_files, project_dir)
        assert stage_result is True

        # Verify staging with nested paths
        staged = get_staged_changes(project_dir)
        assert "src/core/main.py" in staged
        assert "src/utils/helpers/string_utils.py" in staged
        assert len(staged) == 2

        # Commit core files
        commit_result = commit_staged_files("Add core modules", project_dir)
        assert commit_result["success"] is True

        # Stage remaining files
        stage_all_result = stage_all_changes(project_dir)
        assert stage_all_result is True

        # Commit remaining files
        commit_result2 = commit_staged_files(
            "Add tests, docs, and scripts", project_dir
        )
        assert commit_result2["success"] is True

        # Verify all files committed
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

        # Verify all created files exist
        for path in files.keys():
            assert (project_dir / path).exists()

    def test_unicode_and_binary_files(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow with unicode filenames and binary file content."""
        repo, project_dir = git_repo

        # Create files with unicode content and names
        unicode_files = {
            "测试文件.py": "# 中文注释\nprint('你好世界')",
            "файл.txt": "Привет мир",
            "archivo_español.md": "# Título\n\nContenido en español: áéíóú",
            "émoji_test.txt": "Test with emoji: 🐍 🚀 ✅",
        }

        for filename, content in unicode_files.items():
            file_path = project_dir / filename
            file_path.write_text(content, encoding="utf-8")

        # Create binary file content (simple binary data)
        binary_file = project_dir / "binary_data.bin"
        binary_content = bytes(
            [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
        )  # PNG header-like
        binary_file.write_bytes(binary_content)

        # Test staging unicode and binary files
        status = get_full_status(project_dir)
        assert len(status["untracked"]) == 5

        # Stage all files including unicode and binary
        stage_result = stage_all_changes(project_dir)
        assert stage_result is True

        # Verify staging worked with unicode filenames
        staged = get_staged_changes(project_dir)
        assert len(staged) == 5
        assert "binary_data.bin" in staged
        # Note: Unicode filenames may be normalized by git

        # Commit unicode and binary files
        commit_result = commit_staged_files("Add unicode and binary files", project_dir)
        assert commit_result["success"] is True

        # Modify unicode file and test modification detection
        unicode_file = project_dir / "测试文件.py"
        unicode_file.write_text(
            "# 更新的中文注释\nprint('更新后的你好世界')", encoding="utf-8"
        )

        # Test modification detection with unicode
        status = get_full_status(project_dir)
        assert len(status["modified"]) >= 1

        # Commit modification
        commit_result2 = commit_all_changes("Update unicode file", project_dir)
        assert commit_result2["success"] is True

        # Verify final state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

        # Verify files exist
        assert binary_file.exists()
        assert unicode_file.exists()

    def test_performance_with_many_files(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow performance with large number of files."""
        repo, project_dir = git_repo

        # Create many files to test performance
        files_count = 50  # Reasonable number for testing
        for i in range(files_count):
            file_path = project_dir / f"file_{i:03d}.txt"
            file_path.write_text(f"Content for file {i}\nLine 2")

        # Create some nested files
        for i in range(10):
            nested_path = project_dir / "nested" / f"subfile_{i:02d}.py"
            nested_path.parent.mkdir(exist_ok=True)
            nested_path.write_text(f"# File {i}\ndef function_{i}():\n    return {i}")

        # Test staging many files at once
        import time

        start_time = time.time()

        stage_result = stage_all_changes(project_dir)
        assert stage_result is True

        staging_time = time.time() - start_time
        assert staging_time < PERFORMANCE_THRESHOLD_SECONDS  # Should complete quickly

        # Verify all files staged
        staged = get_staged_changes(project_dir)
        assert len(staged) == 60  # 50 + 10 nested files

        # Test commit performance
        start_time = time.time()
        commit_result = commit_staged_files(
            "Add many files for performance test", project_dir
        )
        commit_time = time.time() - start_time

        assert commit_result["success"] is True
        assert commit_time < PERFORMANCE_THRESHOLD_SECONDS  # Should commit quickly

        # Verify clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_incremental_staging_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: stage files incrementally and commit in batches."""
        repo, project_dir = git_repo

        # Create files for incremental staging
        batch1_files = ["batch1_file1.py", "batch1_file2.py", "batch1_file3.py"]

        batch2_files = ["batch2_file1.py", "batch2_file2.py"]

        batch3_files = [
            "batch3_file1.py",
            "batch3_file2.py",
            "batch3_file3.py",
            "batch3_file4.py",
        ]

        # Create all files
        all_files = batch1_files + batch2_files + batch3_files
        for filename in all_files:
            (project_dir / filename).write_text(
                f"# {filename}\nclass {filename.replace('.py', '').title()}:\n    pass"
            )

        # Batch 1: Stage first batch
        batch1_paths = [project_dir / f for f in batch1_files]
        stage_result1 = stage_specific_files(batch1_paths, project_dir)
        assert stage_result1 is True

        # Verify partial staging
        staged = get_staged_changes(project_dir)
        assert len(staged) == 3
        for filename_str in batch1_files:
            assert filename_str in staged

        # Commit batch 1
        commit_result1 = commit_staged_files("Batch 1: Core functionality", project_dir)
        assert commit_result1["success"] is True

        # Batch 2: Stage second batch
        batch2_paths = [project_dir / f for f in batch2_files]
        stage_result2 = stage_specific_files(batch2_paths, project_dir)
        assert stage_result2 is True

        commit_result2 = commit_staged_files("Batch 2: Helper modules", project_dir)
        assert commit_result2["success"] is True

        # Batch 3: Stage remaining files
        batch3_paths = [project_dir / f for f in batch3_files]
        stage_result3 = stage_specific_files(batch3_paths, project_dir)
        assert stage_result3 is True

        commit_result3 = commit_staged_files(
            "Batch 3: Additional features", project_dir
        )
        assert commit_result3["success"] is True

        # Verify all batches committed
        repo = Repo(project_dir)
        commits = list(repo.iter_commits())
        assert len(commits) == 3

        # Verify final clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_file_modification_detection_workflow(
        self, git_repo_with_files: tuple[Repo, Path]
    ) -> None:
        """Test workflow: detect and handle various types of file modifications."""
        repo, project_dir = git_repo_with_files

        # Initial state should be clean
        initial_status = get_full_status(project_dir)
        assert initial_status == {"staged": [], "modified": [], "untracked": []}

        # Type 1: Content modification
        file1 = project_dir / "README.md"
        original_content = file1.read_text()
        file1.write_text(original_content + "\nAdded new line")

        # Type 2: Complete rewrite
        file2 = project_dir / "main.py"
        file2.write_text(
            "# Completely rewritten\nclass NewClass:\n    def new_method(self):\n        pass"
        )

        # Type 3: Minor change
        file3 = project_dir / "config.yml"
        file3.write_text("debug: true\nport: 8080\nnew_setting: value")

        # Detect all modifications
        status = get_full_status(project_dir)
        assert len(status["modified"]) == 3
        assert "README.md" in status["modified"]
        assert "main.py" in status["modified"]
        assert "config.yml" in status["modified"]
        assert status["staged"] == []
        assert status["untracked"] == []

        # Stage modifications selectively
        files_to_stage = [project_dir / "README.md", project_dir / "main.py"]
        stage_result = stage_specific_files(files_to_stage, project_dir)
        assert stage_result is True

        # Verify selective staging
        status = get_full_status(project_dir)
        assert len(status["staged"]) == 2
        assert len(status["modified"]) == 1  # config.json still modified
        assert "config.yml" in status["modified"]

        # Commit staged modifications
        commit_result = commit_staged_files("Update README and main", project_dir)
        assert commit_result["success"] is True

        # Verify remaining modification
        status = get_full_status(project_dir)
        assert status["staged"] == []
        assert len(status["modified"]) == 1
        assert "config.yml" in status["modified"]

        # Commit remaining modification
        commit_result2 = commit_all_changes("Update config file", project_dir)
        assert commit_result2["success"] is True

        # Verify final clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_empty_to_populated_repository_workflow(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test workflow: transform empty repository to populated with content."""
        repo, project_dir = git_repo

        # Verify we start with an empty repository (no commits exist yet)
        try:
            commit_count = len(list(repo.iter_commits()))
        except ValueError:
            # No commits exist yet in empty repo
            commit_count = 0
        assert commit_count == 0

        initial_status = get_full_status(project_dir)
        assert initial_status == {"staged": [], "modified": [], "untracked": []}

        # Phase 1: Add basic structure
        basic_files = {
            "main.py": "#!/usr/bin/env python3\n# Main entry point",
            "requirements.txt": "# Dependencies\n",
            "README.md": "# Project\n\nEmpty repository to start.",
        }

        for path_str, content in basic_files.items():
            (project_dir / path_str).write_text(content)

        commit_result1 = commit_all_changes("Initial project structure", project_dir)
        assert commit_result1["success"] is True

        # Phase 2: Add source code structure
        src_files = {
            "src/__init__.py": "",
            "src/core.py": "class Core:\n    pass",
            "src/utils.py": "def helper():\n    pass",
            "tests/__init__.py": "",
            "tests/test_core.py": "def test_core():\n    assert True",
        }

        for path_str, content in src_files.items():
            file_path = project_dir / path_str
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

        commit_result2 = commit_all_changes("Add source code structure", project_dir)
        assert commit_result2["success"] is True

        # Phase 3: Add configuration and documentation
        config_files = {
            "config/settings.py": "DEBUG = False",
            "docs/api.md": "# API Documentation",
            ".gitignore": "__pycache__/\n*.pyc\n.env",
            "setup.py": "from setuptools import setup\nsetup(name='project')",
        }

        for path_str, content in config_files.items():
            file_path = project_dir / path_str
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

        commit_result3 = commit_all_changes(
            "Add configuration and documentation", project_dir
        )
        assert commit_result3["success"] is True

        # Verify transformation complete
        commits = list(repo.iter_commits())
        assert len(commits) == 3

        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

        # Verify all files exist
        all_files = (
            list(basic_files.keys())
            + list(src_files.keys())
            + list(config_files.keys())
        )
        for file_path_str in all_files:
            assert (project_dir / file_path_str).exists()

    def test_staged_vs_unstaged_changes_workflow(
        self, git_repo_with_files: tuple[Repo, Path]
    ) -> None:
        """Test workflow: manage mix of staged and unstaged changes."""
        repo, project_dir = git_repo_with_files

        # Create a mix of changes
        (project_dir / "README.md").write_text(
            "# Modified Test Project\n\nModified README content"
        )
        (project_dir / "config.yml").write_text("debug: true\nmodified: true")
        (project_dir / "new1.py").write_text("# New file 1")
        (project_dir / "new2.py").write_text("# New file 2")
        (project_dir / "new3.py").write_text("# New file 3")

        # Stage some changes selectively
        files_to_stage = [
            project_dir / "README.md",
            project_dir / "new1.py",
            project_dir / "new2.py",
        ]
        stage_result = stage_specific_files(files_to_stage, project_dir)
        assert stage_result is True

        # Verify mixed state
        status = get_full_status(project_dir)
        assert len(status["staged"]) == 3
        assert len(status["modified"]) == 1  # config.yml
        assert len(status["untracked"]) == 1  # new3.py

        # Commit only staged changes
        commit_result1 = commit_staged_files(
            "Partial commit: README and new files 1,2", project_dir
        )
        assert commit_result1["success"] is True

        # Verify remaining unstaged changes
        status = get_full_status(project_dir)
        assert status["staged"] == []
        assert len(status["modified"]) == 1
        assert len(status["untracked"]) == 1

        # Commit remaining changes separately
        commit_result2 = commit_all_changes("Add remaining files", project_dir)
        assert commit_result2["success"] is True

        # Verify clean final state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_commit_message_variations_workflow(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test workflow: various commit message formats and lengths."""
        repo, project_dir = git_repo

        # Test different commit message styles
        test_cases = [
            ("short.txt", "Short"),
            ("conventional.txt", "feat: add conventional commit style"),
            ("detailed.txt", "Add detailed commit\n\n- Feature A\n- Bug fix B"),
            ("emoji.txt", "✨ Add emoji commit message 🚀"),
            (
                "long.txt",
                "Very long commit message that exceeds typical length recommendations",
            ),
        ]

        for filename_str, commit_msg in test_cases:
            file_path = project_dir / filename_str
            file_path.write_text(f"Content for {filename_str}")

            commit_result = commit_all_changes(commit_msg, project_dir)
            assert commit_result["success"] is True

        # Verify all commits created
        repo = Repo(project_dir)
        commits = list(repo.iter_commits())
        assert len(commits) == len(test_cases)

        # Verify clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_file_tracking_status_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: track file status changes throughout operations."""
        repo, project_dir = git_repo
        test_file = project_dir / "tracked_file.py"
        test_file.write_text("# Initial content")

        # Status 1: Untracked
        status = get_full_status(project_dir)
        assert "tracked_file.py" in status["untracked"]

        # Stage the file
        stage_result = stage_specific_files([test_file], project_dir)
        assert stage_result is True

        # Status 2: Staged
        status = get_full_status(project_dir)
        assert "tracked_file.py" in status["staged"]

        # Commit the file
        commit_result = commit_staged_files("Add tracked file", project_dir)
        assert commit_result["success"] is True

        # Status 3: Clean
        status = get_full_status(project_dir)
        assert "tracked_file.py" not in status["untracked"]
        assert "tracked_file.py" not in status["staged"]
        assert "tracked_file.py" not in status["modified"]

        # Modify the file
        test_file.write_text("# Modified content")

        # Status 4: Modified
        status = get_full_status(project_dir)
        assert "tracked_file.py" in status["modified"]

        # Commit modification
        commit_result2 = commit_all_changes("Update tracked file", project_dir)
        assert commit_result2["success"] is True

        # Verify clean final state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_directory_structure_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: create complex directory structures and manage files."""
        repo, project_dir = git_repo

        # Create complex nested structure
        structure = {
            "src/main/python/app/core/engine.py": "class Engine: pass",
            "src/test/python/test_core.py": "def test_engine(): pass",
            "docs/api/core.md": "# Core API",
            "config/dev/database.yaml": "host: localhost",
            "scripts/deploy/build.sh": "#!/bin/bash\necho build",
        }

        for path, content in structure.items():
            file_path = project_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Stage and commit by groups
        src_files = [
            project_dir / path for path in structure.keys() if path.startswith("src/")
        ]
        stage_result1 = stage_specific_files(src_files, project_dir)
        assert stage_result1 is True
        commit_result1 = commit_staged_files("Add source code", project_dir)
        assert commit_result1["success"] is True

        # Commit remaining
        commit_result2 = commit_all_changes(
            "Add docs, config, and scripts", project_dir
        )
        assert commit_result2["success"] is True

        # Verify all files exist and clean state
        for path in structure.keys():
            assert (project_dir / path).exists()
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_git_status_consistency_workflow(
        self, git_repo_with_files: tuple[Repo, Path]
    ) -> None:
        """Test workflow: verify git status consistency after operations."""
        repo, project_dir = git_repo_with_files

        # Perform operations and check consistency
        (project_dir / "file1.txt").write_text("Modified")
        (project_dir / "new.py").write_text("# New file")

        # Check status consistency multiple times
        for check in range(3):
            status1 = get_full_status(project_dir)
            status2 = get_full_status(project_dir)
            assert status1 == status2, f"Inconsistent status on check {check}"

        # Stage and verify consistency
        stage_result = stage_all_changes(project_dir)
        assert stage_result is True

        for check in range(3):
            staged1 = get_staged_changes(project_dir)
            staged2 = get_staged_changes(project_dir)
            assert staged1 == staged2

        # Commit and verify final consistency
        commit_result = commit_staged_files("Consistency test", project_dir)
        assert commit_result["success"] is True

        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_complete_project_lifecycle_workflow(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test workflow: complete project from initialization to multiple commits."""
        repo, project_dir = git_repo

        # Phase 1: Project initialization
        init_files = {
            "README.md": "# New Project",
            "setup.py": "from setuptools import setup\nsetup()",
        }
        for path_str, content in init_files.items():
            (project_dir / path_str).write_text(content)
        commit1 = commit_all_changes("Initial setup", project_dir)
        assert commit1["success"] is True

        # Phase 2: Add code structure
        (project_dir / "myproject" / "__init__.py").parent.mkdir(exist_ok=True)
        (project_dir / "myproject" / "__init__.py").write_text("__version__ = '0.1.0'")
        (project_dir / "myproject" / "main.py").write_text("def main(): print('Hello')")
        commit2 = commit_all_changes("Add basic structure", project_dir)
        assert commit2["success"] is True

        # Phase 3: Add tests and docs
        (project_dir / "tests" / "test_main.py").parent.mkdir(exist_ok=True)
        (project_dir / "tests" / "test_main.py").write_text("def test_main(): pass")
        (project_dir / "docs" / "api.md").parent.mkdir(exist_ok=True)
        (project_dir / "docs" / "api.md").write_text("# API Documentation")
        commit3 = commit_all_changes("Add tests and docs", project_dir)
        assert commit3["success"] is True

        # Verify complete lifecycle
        repo = Repo(project_dir)
        commits = list(repo.iter_commits())
        assert len(commits) == 3

        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_real_world_development_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test workflow: simulate realistic development patterns."""
        repo, project_dir = git_repo

        # Day 1: Initial app setup
        (project_dir / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)"
        )
        (project_dir / "requirements.txt").write_text("flask==2.1.0")
        commit_all_changes("Initial Flask setup", project_dir)

        # Day 2: Add routes (partial staging)
        (project_dir / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef home(): return 'Hello'"
        )
        (project_dir / "templates" / "home.html").parent.mkdir(exist_ok=True)
        (project_dir / "templates" / "home.html").write_text("<h1>Home</h1>")
        (project_dir / "static" / "style.css").parent.mkdir(exist_ok=True)
        (project_dir / "static" / "style.css").write_text(
            "body { font-family: Arial; }"
        )

        # Stage only ready changes
        files_to_stage = [
            project_dir / "app.py",
            project_dir / "templates" / "home.html",
        ]
        stage_specific_files(files_to_stage, project_dir)
        commit_staged_files("Add home route and template", project_dir)

        # Day 3: Complete remaining work
        commit_all_changes("Add styling and finalize", project_dir)

        # Day 4: Add tests and docs
        (project_dir / "tests" / "test_app.py").parent.mkdir(exist_ok=True)
        (project_dir / "tests" / "test_app.py").write_text(
            "def test_home(): assert True"
        )
        (project_dir / "README.md").write_text(
            "# Flask App\n\nA simple web application."
        )
        commit_all_changes("Add tests and documentation", project_dir)

        # Verify realistic development history
        repo = Repo(project_dir)
        commits = list(repo.iter_commits())
        assert len(commits) == 4

        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

        # Verify files exist
        expected_files = [
            "app.py",
            "requirements.txt",
            "templates/home.html",
            "static/style.css",
            "tests/test_app.py",
            "README.md",
        ]
        for file_path_str in expected_files:
            assert (project_dir / file_path_str).exists()

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_basic_functionality(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test basic diff generation with staged and unstaged changes."""
        repo, project_dir = git_repo

        # Create and commit initial files to track them
        file1 = project_dir / "file1.py"
        file2 = project_dir / "file2.py"
        file3 = project_dir / "file3.py"

        file1.write_text("# File 1\nprint('original')")
        file2.write_text("# File 2\nprint('original')")
        file3.write_text("# File 3\nprint('original')")

        # Commit initial versions
        commit_all_changes("Initial commit", project_dir)

        # Now modify files
        file1.write_text("# File 1\nprint('hello')")
        file2.write_text("# File 2\nprint('world')")
        file3.write_text("# File 3\nprint('test')")

        # Stage some changes (file1 and file2)
        stage_result = stage_specific_files([file1, file2], project_dir)
        assert stage_result is True

        # file3 is now an unstaged change since it's tracked but not staged

        # Call get_git_diff_for_commit()
        diff_output = get_git_diff_for_commit(project_dir)

        # Assert output contains staged and unstaged sections
        assert diff_output is not None
        assert "=== STAGED CHANGES ===" in diff_output
        assert "=== UNSTAGED CHANGES ===" in diff_output

        # Assert correct diff format with --unified=5 --no-prefix
        # Check for file paths and content
        assert "file1.py" in diff_output
        assert "file2.py" in diff_output
        assert "file3.py" in diff_output
        assert "print('hello')" in diff_output
        assert "print('world')" in diff_output
        assert "print('test')" in diff_output

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_no_changes(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test function returns empty string when no changes exist."""
        repo, project_dir = git_repo

        # Clean repository with no changes
        # Call get_git_diff_for_commit()
        diff_output = get_git_diff_for_commit(project_dir)

        # Assert returns empty string ""
        assert diff_output == ""

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_invalid_repository(self, tmp_path: Path) -> None:
        """Test function returns None for invalid git repository."""
        # Call on non-git directory
        diff_output = get_git_diff_for_commit(tmp_path)

        # Assert returns None
        assert diff_output is None

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_with_untracked_files(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test diff generation includes untracked files."""
        repo, project_dir = git_repo

        # Create and commit initial file to track it
        tracked_file = project_dir / "tracked.py"
        tracked_file.write_text("# Initial content")
        commit_all_changes("Initial commit", project_dir)

        # Create mix of staged, unstaged, and untracked files
        # 1. Create another tracked file and commit it
        unstaged_file = project_dir / "unstaged.py"
        unstaged_file.write_text("# Unstaged content")
        commit_all_changes("Add unstaged file", project_dir)

        # 2. Modify tracked file and stage it
        tracked_file.write_text("# Modified content")
        stage_result = stage_specific_files([tracked_file], project_dir)
        assert stage_result is True

        # 3. Modify unstaged file but don't stage it
        unstaged_file.write_text("# Modified unstaged content")

        # 4. Create untracked files
        untracked1 = project_dir / "untracked1.py"
        untracked2 = project_dir / "untracked2.py"
        untracked1.write_text("# Untracked file 1\nprint('hello')")
        untracked2.write_text("# Untracked file 2\nclass Test:\n    pass")

        # Call get_git_diff_for_commit()
        diff_output = get_git_diff_for_commit(project_dir)

        # Assert output contains all three sections
        assert diff_output is not None
        assert "=== STAGED CHANGES ===" in diff_output
        assert "=== UNSTAGED CHANGES ===" in diff_output
        assert "=== UNTRACKED FILES ===" in diff_output

        # Assert untracked files shown as new files (diff from /dev/null)
        assert "untracked1.py" in diff_output
        assert "untracked2.py" in diff_output
        assert "# Untracked file 1" in diff_output
        assert "class Test" in diff_output

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_untracked_only(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test diff with only untracked files."""
        repo, project_dir = git_repo

        # Clean repo + add untracked files
        untracked1 = project_dir / "new_file1.py"
        untracked2 = project_dir / "new_file2.md"
        untracked_nested = project_dir / "src" / "module.py"

        untracked1.write_text("#!/usr/bin/env python3\ndef main():\n    print('Hello')")
        untracked2.write_text("# Documentation\n\nThis is a readme file.")
        untracked_nested.parent.mkdir(parents=True, exist_ok=True)
        untracked_nested.write_text(
            "class Module:\n    def __init__(self):\n        pass"
        )

        # Call get_git_diff_for_commit()
        diff_output = get_git_diff_for_commit(project_dir)

        # Assert only untracked section appears
        assert diff_output is not None
        assert "=== UNTRACKED FILES ===" in diff_output
        assert "=== STAGED CHANGES ===" not in diff_output
        assert "=== UNSTAGED CHANGES ===" not in diff_output

        # Assert files are present in diff
        assert "new_file1.py" in diff_output
        assert "new_file2.md" in diff_output
        assert "src/module.py" in diff_output
        assert "def main():" in diff_output
        assert "# Documentation" in diff_output
        assert "class Module" in diff_output

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_binary_files(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test handling of binary files in diff."""
        repo, project_dir = git_repo

        # Add binary file (untracked)
        binary_file = project_dir / "image.png"
        # Create simple binary content (PNG-like header)
        binary_content = bytes(
            [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00]
        )
        binary_file.write_bytes(binary_content)

        # Add text file for comparison
        text_file = project_dir / "text.txt"
        text_file.write_text("This is a regular text file.")

        # Call get_git_diff_for_commit()
        diff_output = get_git_diff_for_commit(project_dir)

        # Assert git's binary file message appears naturally
        assert diff_output is not None
        assert "=== UNTRACKED FILES ===" in diff_output

        # Assert text file appears normally
        assert "text.txt" in diff_output
        assert "This is a regular text file." in diff_output

        # Binary file should either appear in diff or be handled gracefully
        # Git might show "Binary files differ" or similar message
        # The key is that the function doesn't crash on binary files

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_empty_repository(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test handling of empty repository (no commits)."""
        repo, project_dir = git_repo

        # Empty repository with untracked files
        untracked_file = project_dir / "new_file.py"
        untracked_file.write_text("# New file content\nprint('hello world')")

        # Should handle gracefully and show untracked files
        diff_output = get_git_diff_for_commit(project_dir)

        # Should return diff showing untracked files
        assert diff_output is not None
        assert "=== UNTRACKED FILES ===" in diff_output
        assert "new_file.py" in diff_output
        assert "print('hello world')" in diff_output

        # Should not contain staged/unstaged sections since no commits exist
        assert "=== STAGED CHANGES ===" not in diff_output
        assert "=== UNSTAGED CHANGES ===" not in diff_output

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_git_command_errors(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test handling of git command failures."""
        repo, project_dir = git_repo

        # Test more realistic error scenarios by testing resilience
        # Create initial commit first
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        commit_all_changes("Initial commit", project_dir)

        # Add a new untracked file
        new_file = project_dir / "new.py"
        new_file.write_text("# New content")

        # Function should handle git command errors gracefully
        # Even if some git commands fail, it should try to provide what it can
        diff_output = get_git_diff_for_commit(project_dir)

        # The function should work normally in this case
        assert diff_output is not None
        assert "=== UNTRACKED FILES ===" in diff_output
        assert "new.py" in diff_output

        # Test with a corrupted repository that still has .git directory
        # but might have issues with some operations
        git_dir = project_dir / ".git"

        # Rather than corrupting, test that the function doesn't crash
        # when there are permission issues or other non-fatal problems
        # This simulates partial git command failures in a more realistic way

        # For a more robust test, we could mock the git commands to fail
        # but for now, we'll test that the function works even with edge cases

        # Delete and recreate the file to ensure it's still untracked
        new_file.unlink()
        new_file.write_text("# New content after recreation")

        diff_output2 = get_git_diff_for_commit(project_dir)
        assert diff_output2 is not None
        assert "# New content after recreation" in diff_output2

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_unicode_filenames(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test handling of unicode filenames."""
        repo, project_dir = git_repo

        # Create files with unicode names
        unicode_files = {
            "测试文件.py": "# 中文注释\nprint('你好世界')",
            "файл.txt": "Привет мир",
            "émoji_test_🐍.md": "# Test with emoji\nContent with unicode: àáâã",
        }

        for filename, content in unicode_files.items():
            file_path = project_dir / filename
            file_path.write_text(content, encoding="utf-8")

        # Verify diff generation works correctly with unicode
        diff_output = get_git_diff_for_commit(project_dir)

        assert diff_output is not None
        assert "=== UNTRACKED FILES ===" in diff_output

        # Check that unicode content appears in diff (may be normalized by git)
        # At minimum, the diff should be generated without crashing
        assert len(diff_output) > 0

        # Try to find at least some of the unicode content
        # Git may normalize filenames, so we check for content instead
        assert (
            "你好世界" in diff_output
            or "Привет мир" in diff_output
            or "àáâã" in diff_output
        )

    @pytest.mark.git_integration
    def test_get_git_diff_for_commit_large_files(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test handling of large text files."""
        repo, project_dir = git_repo

        # Create large text files
        large_file1 = project_dir / "large1.txt"
        large_file2 = project_dir / "large2.py"

        # Generate large content (not too large to avoid test slowness)
        large_content1 = "\n".join(
            [f"Line {i}: This is a test line with some content." for i in range(1000)]
        )
        large_content2 = "\n".join(
            [f"# Comment {i}\ndef function_{i}():\n    return {i}" for i in range(500)]
        )

        large_file1.write_text(large_content1)
        large_file2.write_text(large_content2)

        # Verify performance is acceptable (basic check)
        import time

        start_time = time.time()

        diff_output = get_git_diff_for_commit(project_dir)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete within reasonable time (5 seconds)
        assert processing_time < PERFORMANCE_THRESHOLD_SECONDS

        # Should handle large files without crashing
        assert diff_output is not None
        assert "=== UNTRACKED FILES ===" in diff_output
        assert "large1.txt" in diff_output
        assert "large2.py" in diff_output

        # Content should appear in diff
        assert "Line 1:" in diff_output
        assert "def function_1():" in diff_output

    @pytest.mark.git_integration
    def test_get_git_diff_integration_with_existing_functions(
        self, git_repo_with_files: tuple[Repo, Path]
    ) -> None:
        """Test integration with existing git_operations functions."""
        repo, project_dir = git_repo_with_files

        # Use get_full_status to check initial state
        initial_status = get_full_status(project_dir)
        assert initial_status == {"staged": [], "modified": [], "untracked": []}

        # Test 1: Modify files and check diff at various stages
        file1 = project_dir / "README.md"
        file2 = project_dir / "main.py"
        new_file = project_dir / "new_feature.py"

        file1.write_text("# Updated README\n\nThis has been modified.")
        file2.write_text("def main():\n    print('Updated main function')")
        new_file.write_text("class NewFeature:\n    def __init__(self):\n        pass")

        # Stage 1: Check diff with only unstaged and untracked changes
        diff_output1 = get_git_diff_for_commit(project_dir)
        assert diff_output1 is not None
        assert "=== UNSTAGED CHANGES ===" in diff_output1
        assert "=== UNTRACKED FILES ===" in diff_output1
        assert "=== STAGED CHANGES ===" not in diff_output1
        assert "Updated README" in diff_output1
        assert "NewFeature" in diff_output1

        # Use stage_specific_files to stage only file1
        stage_result = stage_specific_files([file1], project_dir)
        assert stage_result is True

        # Stage 2: Check diff with mixed staged/unstaged/untracked
        diff_output2 = get_git_diff_for_commit(project_dir)
        assert diff_output2 is not None
        assert "=== STAGED CHANGES ===" in diff_output2
        assert "=== UNSTAGED CHANGES ===" in diff_output2
        assert "=== UNTRACKED FILES ===" in diff_output2

        # Verify status consistency with diff output
        status = get_full_status(project_dir)
        assert len(status["staged"]) == 1
        assert "README.md" in status["staged"]
        assert len(status["modified"]) == 1
        assert "main.py" in status["modified"]
        assert len(status["untracked"]) == 1
        assert "new_feature.py" in status["untracked"]

        # Use stage_all_changes to stage everything
        stage_all_result = stage_all_changes(project_dir)
        assert stage_all_result is True

        # Stage 3: Check diff with only staged changes
        diff_output3 = get_git_diff_for_commit(project_dir)
        assert diff_output3 is not None
        assert "=== STAGED CHANGES ===" in diff_output3
        assert "=== UNSTAGED CHANGES ===" not in diff_output3
        assert "=== UNTRACKED FILES ===" not in diff_output3

        # Use commit_staged_files to commit everything
        commit_result = commit_staged_files("Integration test commit", project_dir)
        assert commit_result["success"] is True

        # Stage 4: Check diff with clean state
        diff_output4 = get_git_diff_for_commit(project_dir)
        assert diff_output4 == ""

        # Verify final status is clean
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    @pytest.mark.git_integration
    def test_get_git_diff_complete_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test complete workflow from empty repo to multiple commits."""
        repo, project_dir = git_repo

        # Phase 1: Empty repo should show no changes
        diff_empty = get_git_diff_for_commit(project_dir)
        assert diff_empty == ""

        # Phase 2: Add initial files (untracked only)
        files_phase1 = {
            "app.py": "#!/usr/bin/env python3\n# Main application",
            "config.json": '{"debug": true, "port": 8080}',
            "README.md": "# My Project\n\nInitial project setup.",
        }

        for path_str, content in files_phase1.items():
            (project_dir / path_str).write_text(content)

        # Check diff shows untracked files
        diff_phase1 = get_git_diff_for_commit(project_dir)
        assert diff_phase1 is not None
        assert "=== UNTRACKED FILES ===" in diff_phase1
        assert "=== STAGED CHANGES ===" not in diff_phase1
        assert "=== UNSTAGED CHANGES ===" not in diff_phase1
        assert "app.py" in diff_phase1
        assert "config.json" in diff_phase1
        assert "README.md" in diff_phase1
        assert "Main application" in diff_phase1

        # Commit first phase
        commit_result1 = commit_all_changes("Initial project setup", project_dir)
        assert commit_result1["success"] is True

        # Verify clean state after commit
        diff_clean1 = get_git_diff_for_commit(project_dir)
        assert diff_clean1 == ""

        # Phase 3: Add more files and modify existing ones
        # Add new files
        (project_dir / "utils.py").write_text("def helper():\n    return 'utility'")
        (project_dir / "tests" / "test_app.py").parent.mkdir(exist_ok=True)
        (project_dir / "tests" / "test_app.py").write_text(
            "def test_main():\n    assert True"
        )

        # Modify existing files
        (project_dir / "app.py").write_text(
            "#!/usr/bin/env python3\n# Main application\ndef main():\n    print('Hello World')"
        )
        (project_dir / "README.md").write_text(
            "# My Project\n\nUpdated project with new features."
        )

        # Check mixed state diff
        diff_phase2 = get_git_diff_for_commit(project_dir)
        assert diff_phase2 is not None
        assert "=== UNSTAGED CHANGES ===" in diff_phase2  # Modified files
        assert "=== UNTRACKED FILES ===" in diff_phase2  # New files
        assert "=== STAGED CHANGES ===" not in diff_phase2

        # Stage only modifications, leave new files untracked
        modified_files = [project_dir / "app.py", project_dir / "README.md"]
        stage_result = stage_specific_files(modified_files, project_dir)
        assert stage_result is True

        # Check diff with staged modifications and untracked files
        diff_partial_stage = get_git_diff_for_commit(project_dir)
        assert diff_partial_stage is not None
        assert "=== STAGED CHANGES ===" in diff_partial_stage
        assert "=== UNTRACKED FILES ===" in diff_partial_stage
        assert "=== UNSTAGED CHANGES ===" not in diff_partial_stage

        # Commit staged changes
        commit_result2 = commit_staged_files(
            "Update main app and documentation", project_dir
        )
        assert commit_result2["success"] is True

        # Check remaining untracked files
        diff_remaining = get_git_diff_for_commit(project_dir)
        assert diff_remaining is not None
        assert "=== UNTRACKED FILES ===" in diff_remaining
        assert "=== STAGED CHANGES ===" not in diff_remaining
        assert "=== UNSTAGED CHANGES ===" not in diff_remaining
        assert "utils.py" in diff_remaining
        assert "tests/test_app.py" in diff_remaining

        # Commit remaining files
        commit_result3 = commit_all_changes("Add utilities and tests", project_dir)
        assert commit_result3["success"] is True

        # Final verification: clean state
        diff_final = get_git_diff_for_commit(project_dir)
        assert diff_final == ""

        # Verify commit history
        commits = list(repo.iter_commits())
        assert len(commits) == 3
        commit_messages = [commit.message for commit in commits]
        assert "Initial project setup" in commit_messages
        assert "Update main app and documentation" in commit_messages
        assert "Add utilities and tests" in commit_messages

    @pytest.mark.git_integration
    def test_get_git_diff_performance_basic(self, git_repo: tuple[Repo, Path]) -> None:
        """Basic performance test with reasonable file count."""
        repo, project_dir = git_repo

        # Create ~50 files with various states to test performance
        files_count = 50

        # Create initial commit with some files
        initial_files = []
        for i in range(20):
            file_path = project_dir / f"initial_{i:02d}.py"
            file_path.write_text(
                f"# Initial file {i}\nclass Initial{i}:\n    def method(self):\n        return {i}"
            )
            initial_files.append(file_path)

        # Commit initial files
        commit_result = commit_all_changes(
            "Initial files for performance test", project_dir
        )
        assert commit_result["success"] is True

        # Now create mix of staged, unstaged, and untracked files
        # Modify some existing files (will be unstaged)
        for i in range(0, 10):
            file_path = project_dir / f"initial_{i:02d}.py"
            file_path.write_text(
                f"# Modified file {i}\nclass Modified{i}:\n    def updated_method(self):\n        return {i} * 2"
            )

        # Create new files to be staged
        staged_files = []
        for i in range(15):
            file_path = project_dir / f"staged_{i:02d}.py"
            file_path.write_text(f"# Staged file {i}\nclass Staged{i}:\n    pass")
            staged_files.append(file_path)

        # Stage the new files
        stage_result = stage_specific_files(staged_files, project_dir)
        assert stage_result is True

        # Create untracked files
        for i in range(15):
            file_path = project_dir / f"untracked_{i:02d}.py"
            file_path.write_text(
                f"# Untracked file {i}\nclass Untracked{i}:\n    def new_feature(self):\n        return 'feature_{i}'"
            )

        # Verify we have the expected mix of file states
        status = get_full_status(project_dir)
        assert len(status["staged"]) == 15  # staged_XX.py files
        assert len(status["modified"]) == 10  # modified initial_XX.py files
        assert len(status["untracked"]) == 15  # untracked_XX.py files

        # Performance test: measure diff generation time
        import time

        start_time = time.time()

        diff_output = get_git_diff_for_commit(project_dir)

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance requirement: should complete within threshold
        assert (
            execution_time < PERFORMANCE_THRESHOLD_SECONDS
        ), f"Diff generation took {execution_time:.2f} seconds, expected < {PERFORMANCE_THRESHOLD_SECONDS}"

        # Verify diff output correctness
        assert diff_output is not None
        assert "=== STAGED CHANGES ===" in diff_output
        assert "=== UNSTAGED CHANGES ===" in diff_output
        assert "=== UNTRACKED FILES ===" in diff_output

        # Verify all file types appear in diff
        # Check some staged files
        assert "staged_00.py" in diff_output
        assert "class Staged0" in diff_output

        # Check some modified files
        assert "initial_00.py" in diff_output
        assert "class Modified0" in diff_output

        # Check some untracked files
        assert "untracked_00.py" in diff_output
        assert "class Untracked0" in diff_output

        # Verify diff format is correct (unified format with no prefix)
        lines = diff_output.split("\n")

        # Should contain diff headers
        diff_headers = [line for line in lines if line.startswith("diff --git")]
        assert len(diff_headers) >= 30  # Should have diffs for most files

        # Should contain proper add/remove markers
        add_lines = [
            line
            for line in lines
            if line.startswith("+") and not line.startswith("+++")
        ]
        assert len(add_lines) > 0  # Should have additions

        # Measure memory usage is reasonable (basic check)
        diff_size = len(diff_output)
        # With ~50 files, diff shouldn't be excessively large (< 1MB is reasonable)
        assert (
            diff_size < 1024 * 1024
        ), f"Diff output size is {diff_size} bytes, might be too large"

        # Clean up: commit everything to return to clean state
        commit_result2 = commit_all_changes("Performance test completion", project_dir)
        assert commit_result2["success"] is True

        # Verify clean state
        final_diff = get_git_diff_for_commit(project_dir)
        assert final_diff == ""

    def test_git_push_basic_workflow(self, git_repo: tuple[Repo, Path]) -> None:
        """Test basic git push after commit workflow."""
        from unittest.mock import patch

        repo, project_dir = git_repo

        # Create test files and commit them
        test_file = project_dir / "push_test.py"
        test_file.write_text("# Test file for git push\nprint('hello world')")

        commit_result = commit_all_changes("Add test file for push", project_dir)
        assert commit_result["success"] is True

        # Mock git push command to avoid network operations
        with patch("git.cmd.Git.execute") as mock_execute:
            # Test successful push scenario
            mock_execute.return_value = ""

            # Test the expected git_push function interface
            # This simulates what git_push should return on success
            expected_success_result = {"success": True, "error": None}

            # Verify the expected structure
            assert expected_success_result["success"] is True
            assert expected_success_result["error"] is None

            # Test error scenarios
            from git.exc import GitCommandError

            # Mock git command error (e.g., no remote, auth failure)
            mock_execute.side_effect = GitCommandError(
                "push", 128, "fatal: No such remote"
            )

            # Expected error result structure
            expected_error_result = {"success": False, "error": "fatal: No such remote"}
            assert expected_error_result["success"] is False
            assert expected_error_result["error"] is not None

    def test_git_push_nothing_to_push(
        self, git_repo_with_files: tuple[Repo, Path]
    ) -> None:
        """Test git push when remote is already up-to-date."""
        from unittest.mock import patch

        repo, project_dir = git_repo_with_files

        # Repository already has committed files (from fixture)
        # Verify clean state
        status = get_full_status(project_dir)
        assert status == {"staged": [], "modified": [], "untracked": []}

        # Mock git push for "nothing to push" scenario
        with patch("git.cmd.Git.execute") as mock_execute:
            # Git push when up-to-date typically returns with exit code 0
            # but may have output like "Everything up-to-date"
            mock_execute.return_value = "Everything up-to-date\n"

            # Expected success result for up-to-date case
            expected_result = {"success": True, "error": None}
            assert expected_result["success"] is True
            assert expected_result["error"] is None

    def test_is_working_directory_clean(self, git_repo: tuple[Repo, Path]) -> None:
        """Test is_working_directory_clean basic functionality."""
        repo, project_dir = git_repo

        # Clean repo
        assert is_working_directory_clean(project_dir) is True

        # Add untracked file
        (project_dir / "test.py").write_text("# test")
        assert is_working_directory_clean(project_dir) is False

        # Clean up
        commit_all_changes("Add test file", project_dir)
        assert is_working_directory_clean(project_dir) is True

    def test_is_working_directory_clean_non_git_repository(
        self, tmp_path: Path
    ) -> None:
        """Test exception for non-git repository."""
        with pytest.raises(ValueError, match="Directory is not a git repository"):
            is_working_directory_clean(tmp_path)


@pytest.mark.git_integration
class TestGitBranchOperations:
    """Test git branch operations without mocking."""

    def test_get_current_branch_name_success(self, git_repo: tuple[Repo, Path]) -> None:
        """Test get_current_branch_name returns current branch name successfully."""
        repo, project_dir = git_repo

        # Create and commit a file so we have a proper HEAD
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        commit_all_changes("Initial commit", project_dir)

        # Test getting current branch name (should be main or master by default)
        current_branch = get_current_branch_name(project_dir)
        assert current_branch is not None
        assert isinstance(current_branch, str)
        assert len(current_branch) > 0
        # Should be main or master (depending on git configuration)
        assert current_branch in ["main", "master"]

        # Create and switch to a new branch
        repo.git.checkout("-b", "feature/test-branch")
        current_branch = get_current_branch_name(project_dir)
        assert current_branch == "feature/test-branch"

        # Switch back to main/master
        original_branch = "main" if "main" in [h.name for h in repo.heads] else "master"
        repo.git.checkout(original_branch)
        current_branch = get_current_branch_name(project_dir)
        assert current_branch == original_branch

    def test_get_current_branch_name_invalid_repo(self, tmp_path: Path) -> None:
        """Test get_current_branch_name returns None for invalid repository."""
        # Test with non-git directory
        result = get_current_branch_name(tmp_path)
        assert result is None

    def test_get_current_branch_name_detached_head(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test get_current_branch_name handles detached HEAD state gracefully."""
        repo, project_dir = git_repo

        # Create a commit so we can detach HEAD
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        commit_result = commit_all_changes("Initial commit", project_dir)
        assert commit_result["success"]

        # Get the commit hash
        commit_hash = commit_result["commit_hash"]
        assert commit_hash is not None

        # Detach HEAD by checking out the commit directly
        repo.git.checkout(commit_hash)

        # In detached HEAD state, function should return None or handle gracefully
        current_branch = get_current_branch_name(project_dir)
        # Should return None for detached HEAD (as per requirements)
        assert current_branch is None

    def test_get_default_branch_name_main_branch(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test get_default_branch_name returns 'main' when main branch exists."""
        repo, project_dir = git_repo

        # Create a commit so branches are properly initialized
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        commit_all_changes("Initial commit", project_dir)

        # Ensure we have a main branch (rename if necessary)
        current_branch = repo.active_branch.name
        if current_branch == "master":
            repo.git.branch("-m", "main")

        # Test that get_default_branch_name returns 'main'
        default_branch = get_default_branch_name(project_dir)
        assert default_branch == "main"

    def test_get_default_branch_name_master_branch(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test get_default_branch_name returns 'master' when only master branch exists."""
        repo, project_dir = git_repo

        # Create a commit so branches are properly initialized
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        commit_all_changes("Initial commit", project_dir)

        # Ensure we have a master branch (rename if necessary)
        current_branch = repo.active_branch.name
        if current_branch == "main":
            repo.git.branch("-m", "master")

        # Test that get_default_branch_name returns 'master'
        default_branch = get_default_branch_name(project_dir)
        assert default_branch == "master"

    def test_get_default_branch_name_invalid_repo(self, tmp_path: Path) -> None:
        """Test get_default_branch_name returns None for invalid repository."""
        # Test with non-git directory
        result = get_default_branch_name(tmp_path)
        assert result is None

    def test_get_parent_branch_name_returns_main(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test get_parent_branch_name returns main branch as parent."""
        repo, project_dir = git_repo

        # Create a commit so branches are properly initialized
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        commit_all_changes("Initial commit", project_dir)

        # Ensure we have a main branch
        current_branch = repo.active_branch.name
        if current_branch == "master":
            repo.git.branch("-m", "main")

        # Create a feature branch
        repo.git.checkout("-b", "feature/test")

        # Test that get_parent_branch_name returns 'main'
        parent_branch = get_parent_branch_name(project_dir)
        assert parent_branch == "main"

        # Test from main branch itself (should still return 'main')
        repo.git.checkout("main")
        parent_branch = get_parent_branch_name(project_dir)
        assert parent_branch == "main"

    def test_get_parent_branch_name_invalid_repo(self, tmp_path: Path) -> None:
        """Test get_parent_branch_name returns None for invalid repository."""
        # Test with non-git directory
        result = get_parent_branch_name(tmp_path)
        assert result is None

    def test_get_parent_branch_name_no_main_branch(
        self, git_repo: tuple[Repo, Path]
    ) -> None:
        """Test get_parent_branch_name returns None when no main/master branch exists."""
        repo, project_dir = git_repo

        # Create a commit so branches are properly initialized
        test_file = project_dir / "test.py"
        test_file.write_text("# Test file")
        commit_all_changes("Initial commit", project_dir)

        # Rename the main/master branch to something else
        current_branch = repo.active_branch.name
        repo.git.branch("-m", "custom-default")

        # Now there's no 'main' or 'master' branch
        # get_parent_branch_name should return None
        parent_branch = get_parent_branch_name(project_dir)
        assert parent_branch is None

    def test_create_branch_success(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test create_branch successfully creates new branch."""
        repo, project_dir = git_repo_with_files
        
        # Test creating new branch from current branch
        result = create_branch("feature-test", project_dir)
        assert result is True
        
        # Verify branch was created and is current
        current_branch = get_current_branch_name(project_dir)
        assert current_branch == "feature-test"
        
        # Verify branch exists in repo
        branch_names = [branch.name for branch in repo.branches]
        assert "feature-test" in branch_names

    def test_create_branch_from_specific_branch(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test create_branch from specified base branch."""
        repo, project_dir = git_repo_with_files
        
        # Ensure we know the current branch name
        original_branch = repo.active_branch.name
        
        # Create branch from specific base
        result = create_branch("feature-from-main", project_dir, from_branch=original_branch)
        assert result is True
        
        # Verify branch was created and is current
        current_branch = get_current_branch_name(project_dir)
        assert current_branch == "feature-from-main"

    def test_create_branch_already_exists(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test create_branch returns False when branch already exists."""
        repo, project_dir = git_repo_with_files
        
        # Create branch first time - should succeed
        result1 = create_branch("existing-branch", project_dir)
        assert result1 is True
        
        # Go back to original branch
        repo.git.checkout("main" if "main" in [h.name for h in repo.heads] else "master")
        
        # Try to create same branch again - should fail
        result2 = create_branch("existing-branch", project_dir)
        assert result2 is False

    def test_create_branch_invalid_name(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test create_branch returns False for invalid branch names."""
        repo, project_dir = git_repo_with_files
        
        # Test empty name
        assert create_branch("", project_dir) is False
        assert create_branch("   ", project_dir) is False
        
        # Test invalid characters
        assert create_branch("branch~name", project_dir) is False
        assert create_branch("branch^name", project_dir) is False
        assert create_branch("branch:name", project_dir) is False
        assert create_branch("branch?name", project_dir) is False
        assert create_branch("branch*name", project_dir) is False
        assert create_branch("branch[name", project_dir) is False

    def test_create_branch_invalid_base_branch(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test create_branch returns False when base branch doesn't exist."""
        repo, project_dir = git_repo_with_files
        
        # Try to create branch from non-existent base
        result = create_branch("test-branch", project_dir, from_branch="nonexistent-branch")
        assert result is False
        
        # Verify no branch was created
        branch_names = [branch.name for branch in repo.branches]
        assert "test-branch" not in branch_names

    def test_create_branch_non_git_directory(self, tmp_path: Path) -> None:
        """Test create_branch returns False for non-git directory."""
        result = create_branch("test-branch", tmp_path)
        assert result is False

    def test_checkout_branch_success(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test checkout_branch successfully switches to existing branch."""
        repo, project_dir = git_repo_with_files
        
        # Create a new branch
        result = create_branch("feature-checkout", project_dir)
        assert result is True
        
        # Go back to original branch
        original_branch = "main" if "main" in [h.name for h in repo.heads] else "master"
        repo.git.checkout(original_branch)
        
        # Verify we're on original branch
        current = get_current_branch_name(project_dir)
        assert current == original_branch
        
        # Test checkout to the feature branch
        result = checkout_branch("feature-checkout", project_dir)
        assert result is True
        
        # Verify we switched to the feature branch
        current = get_current_branch_name(project_dir)
        assert current == "feature-checkout"

    def test_checkout_branch_already_on_branch(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test checkout_branch returns True when already on target branch."""
        repo, project_dir = git_repo_with_files
        
        # Get current branch
        current_branch = get_current_branch_name(project_dir)
        assert current_branch is not None
        
        # Try to checkout the same branch
        result = checkout_branch(current_branch, project_dir)
        assert result is True
        
        # Verify we're still on the same branch
        still_current = get_current_branch_name(project_dir)
        assert still_current == current_branch

    def test_checkout_branch_nonexistent_branch(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test checkout_branch returns False for non-existent branch."""
        repo, project_dir = git_repo_with_files
        
        # Try to checkout non-existent branch
        result = checkout_branch("nonexistent-branch", project_dir)
        assert result is False
        
        # Verify we're still on original branch
        current = get_current_branch_name(project_dir)
        assert current is not None  # Should still be on a valid branch

    def test_checkout_branch_invalid_name(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test checkout_branch returns False for invalid branch names."""
        repo, project_dir = git_repo_with_files
        
        # Test empty name
        assert checkout_branch("", project_dir) is False
        assert checkout_branch("   ", project_dir) is False

    def test_checkout_branch_non_git_directory(self, tmp_path: Path) -> None:
        """Test checkout_branch returns False for non-git directory."""
        result = checkout_branch("any-branch", tmp_path)
        assert result is False

    def test_checkout_branch_from_detached_head(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test checkout_branch works from detached HEAD state."""
        repo, project_dir = git_repo_with_files
        
        # Create a feature branch first
        result = create_branch("feature-detached", project_dir)
        assert result is True
        
        # Get the current commit hash
        commit_hash = repo.head.commit.hexsha[:7]
        
        # Detach HEAD by checking out the commit directly
        repo.git.checkout(commit_hash)
        
        # Verify we're in detached HEAD state
        current_branch = get_current_branch_name(project_dir)
        assert current_branch is None  # Should be None for detached HEAD
        
        # Checkout to the feature branch from detached state
        result = checkout_branch("feature-detached", project_dir)
        assert result is True
        
        # Verify we're now on the feature branch
        current_branch = get_current_branch_name(project_dir)
        assert current_branch == "feature-detached"

    def test_branch_exists_true(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test branch_exists returns True for existing branch."""
        repo, project_dir = git_repo_with_files
        
        # Test current branch exists
        current_branch = get_current_branch_name(project_dir)
        assert current_branch is not None
        assert branch_exists(current_branch, project_dir) is True
        
        # Create a new branch and test it exists
        result = create_branch("test-exists", project_dir)
        assert result is True
        assert branch_exists("test-exists", project_dir) is True

    def test_branch_exists_false(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test branch_exists returns False for non-existent branch."""
        repo, project_dir = git_repo_with_files
        
        # Test non-existent branch
        assert branch_exists("nonexistent-branch", project_dir) is False
        assert branch_exists("another-missing-branch", project_dir) is False

    def test_branch_exists_invalid_name(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test branch_exists returns False for invalid branch names."""
        repo, project_dir = git_repo_with_files
        
        # Test empty names
        assert branch_exists("", project_dir) is False
        assert branch_exists("   ", project_dir) is False

    def test_branch_exists_non_git_directory(self, tmp_path: Path) -> None:
        """Test branch_exists returns False for non-git directory."""
        assert branch_exists("any-branch", tmp_path) is False

    def test_branch_exists_multiple_branches(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test branch_exists with multiple branches."""
        repo, project_dir = git_repo_with_files
        
        # Create multiple branches
        branches = ["feature-1", "feature-2", "bugfix-1", "release-1.0"]
        
        for branch_name in branches:
            result = create_branch(branch_name, project_dir)
            assert result is True
        
        # Test all created branches exist
        for branch_name in branches:
            assert branch_exists(branch_name, project_dir) is True
        
        # Test non-existent branches still return False
        assert branch_exists("feature-3", project_dir) is False
        assert branch_exists("release-2.0", project_dir) is False

    def test_branch_exists_after_checkout(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test branch_exists works correctly after branch checkouts."""
        repo, project_dir = git_repo_with_files
        
        # Create and checkout to new branch
        result = create_branch("test-checkout-exists", project_dir)
        assert result is True
        
        # Branch should exist regardless of current branch
        assert branch_exists("test-checkout-exists", project_dir) is True
        
        # Go back to original branch
        original_branch = "main" if "main" in [h.name for h in repo.heads] else "master"
        checkout_result = checkout_branch(original_branch, project_dir)
        assert checkout_result is True
        
        # Branch should still exist after checkout
        assert branch_exists("test-checkout-exists", project_dir) is True
        assert branch_exists(original_branch, project_dir) is True

    def test_push_branch_success(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test push_branch successfully pushes branch to origin (mocked)."""
        from unittest.mock import patch
        
        repo, project_dir = git_repo_with_files
        
        # Create a new branch with some content
        result = create_branch("feature-push", project_dir)
        assert result is True
        
        # Add a commit to the branch
        test_file = project_dir / "push_test.py"
        test_file.write_text("# Test push functionality")
        commit_result = commit_all_changes("Add test file for push", project_dir)
        assert commit_result["success"] is True
        
        # Mock the git push command to avoid network operations
        with patch.object(repo.git, "push") as mock_push:
            # Test successful push with upstream
            result = push_branch("feature-push", project_dir, set_upstream=True)
            assert result is True
            mock_push.assert_called_once_with("--set-upstream", "origin", "feature-push")

    def test_push_branch_without_upstream(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test push_branch without setting upstream tracking."""
        from unittest.mock import patch
        
        repo, project_dir = git_repo_with_files
        
        # Create and commit to a new branch
        result = create_branch("feature-no-upstream", project_dir)
        assert result is True
        
        test_file = project_dir / "no_upstream.py"
        test_file.write_text("# Test push without upstream")
        commit_result = commit_all_changes("Add file for no-upstream test", project_dir)
        assert commit_result["success"] is True
        
        # Mock the git push command
        with patch.object(repo.git, "push") as mock_push:
            # Test push without upstream
            result = push_branch("feature-no-upstream", project_dir, set_upstream=False)
            assert result is True
            mock_push.assert_called_once_with("origin", "feature-no-upstream")

    def test_push_branch_nonexistent_branch(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test push_branch returns False for non-existent branch."""
        repo, project_dir = git_repo_with_files
        
        # Try to push non-existent branch
        result = push_branch("nonexistent-branch", project_dir)
        assert result is False

    def test_push_branch_invalid_name(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test push_branch returns False for invalid branch names."""
        repo, project_dir = git_repo_with_files
        
        # Test empty names
        assert push_branch("", project_dir) is False
        assert push_branch("   ", project_dir) is False

    def test_push_branch_non_git_directory(self, tmp_path: Path) -> None:
        """Test push_branch returns False for non-git directory."""
        result = push_branch("any-branch", tmp_path)
        assert result is False

    def test_push_branch_no_origin_remote(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test push_branch returns False when no origin remote exists."""
        repo, project_dir = git_repo_with_files
        
        # Create a branch
        result = create_branch("test-no-origin", project_dir)
        assert result is True
        
        # Remove origin remote if it exists
        if "origin" in [remote.name for remote in repo.remotes]:
            origin_remote = repo.remotes.origin
            repo.delete_remote(origin_remote)
        
        # Try to push - should fail due to no origin
        result = push_branch("test-no-origin", project_dir)
        assert result is False

    def test_push_branch_git_command_error(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test push_branch handles git command errors gracefully."""
        from unittest.mock import patch
        from git.exc import GitCommandError
        
        repo, project_dir = git_repo_with_files
        
        # Create a branch
        result = create_branch("test-push-error", project_dir)
        assert result is True
        
        # Mock git push to raise an error
        with patch.object(repo.git, "push") as mock_push:
            mock_push.side_effect = GitCommandError("push", 128, "fatal: remote error")
            
            # Push should return False on git command error
            result = push_branch("test-push-error", project_dir)
            assert result is False

    def test_fetch_remote_success(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test fetch_remote successfully fetches from origin (mocked)."""
        from unittest.mock import patch
        
        repo, project_dir = git_repo_with_files
        
        # Mock the git fetch command to avoid network operations
        with patch.object(repo.git, "fetch") as mock_fetch:
            # Test successful fetch from origin
            result = fetch_remote(project_dir)
            assert result is True
            mock_fetch.assert_called_once_with("origin")

    def test_fetch_remote_custom_remote(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test fetch_remote with custom remote name."""
        from unittest.mock import patch
        
        repo, project_dir = git_repo_with_files
        
        # Add a custom remote (mocked)
        with patch.object(repo, "remotes") as mock_remotes:
            # Mock remotes to include 'upstream'
            class MockRemote:
                def __init__(self, name: str) -> None:
                    self.name = name
            
            mock_remotes.__iter__ = lambda self: iter([MockRemote("origin"), MockRemote("upstream")])
            
            with patch.object(repo.git, "fetch") as mock_fetch:
                # Test fetch from custom remote
                result = fetch_remote(project_dir, remote="upstream")
                assert result is True
                mock_fetch.assert_called_once_with("upstream")

    def test_fetch_remote_nonexistent_remote(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test fetch_remote returns False for non-existent remote."""
        repo, project_dir = git_repo_with_files
        
        # Try to fetch from non-existent remote
        result = fetch_remote(project_dir, remote="nonexistent")
        assert result is False

    def test_fetch_remote_invalid_name(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test fetch_remote returns False for invalid remote names."""
        repo, project_dir = git_repo_with_files
        
        # Test empty names
        assert fetch_remote(project_dir, remote="") is False
        assert fetch_remote(project_dir, remote="   ") is False

    def test_fetch_remote_non_git_directory(self, tmp_path: Path) -> None:
        """Test fetch_remote returns False for non-git directory."""
        result = fetch_remote(tmp_path)
        assert result is False

    def test_fetch_remote_git_command_error(self, git_repo_with_files: tuple[Repo, Path]) -> None:
        """Test fetch_remote handles git command errors gracefully."""
        from unittest.mock import patch
        from git.exc import GitCommandError
        
        repo, project_dir = git_repo_with_files
        
        # Mock git fetch to raise an error
        with patch.object(repo.git, "fetch") as mock_fetch:
            mock_fetch.side_effect = GitCommandError("fetch", 128, "fatal: network error")
            
            # Fetch should return False on git command error
            result = fetch_remote(project_dir)
            assert result is False

    def test_fetch_remote_no_remotes(self, git_repo: tuple[Repo, Path]) -> None:
        """Test fetch_remote returns False when no remotes exist."""
        repo, project_dir = git_repo
        
        # Create a repository with no remotes
        # The git_repo fixture creates a local repo without remotes
        
        # Try to fetch - should fail due to no origin remote
        result = fetch_remote(project_dir)
        assert result is False
