"""Integration tests for git operations - real-world workflows end-to-end."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from git import Repo
from git.exc import GitCommandError

from mcp_coder.utils.git_operations import (
    commit_all_changes,
    commit_staged_files,
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    stage_all_changes,
    stage_specific_files,
)


class TestRealWorldWorkflows:
    """Test complete real-world git workflows end-to-end."""

    def test_complete_workflow_new_project_to_first_commit(self, tmp_path: Path) -> None:
        """Test complete workflow: initialize repo → add files → stage → commit."""
        # Start with empty directory
        assert not is_git_repository(tmp_path)
        assert get_full_status(tmp_path) == {"staged": [], "modified": [], "untracked": []}
        
        # Initialize git repository
        repo = Repo.init(tmp_path)
        assert is_git_repository(tmp_path)
        
        # Create project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "docs").mkdir()
        
        # Create various project files
        files_created = [
            tmp_path / "README.md",
            tmp_path / "requirements.txt",
            tmp_path / ".gitignore",
            tmp_path / "src" / "__init__.py",
            tmp_path / "src" / "main.py",
            tmp_path / "tests" / "test_main.py",
            tmp_path / "docs" / "API.md",
        ]
        
        file_contents = {
            tmp_path / "README.md": "# My Project\n\nProject description",
            tmp_path / "requirements.txt": "requests>=2.25.0\npytest>=6.0.0",
            tmp_path / ".gitignore": "*.pyc\n__pycache__/\n.env",
            tmp_path / "src" / "__init__.py": '"""My project package."""',
            tmp_path / "src" / "main.py": 'def main():\n    print("Hello, World!")',
            tmp_path / "tests" / "test_main.py": "import pytest\nfrom src.main import main",
            tmp_path / "docs" / "API.md": "# API Documentation\n\n## Endpoints",
        }
        
        for file_path in files_created:
            file_path.write_text(file_contents[file_path])
        
        # Check status - should show all as untracked
        status = get_full_status(tmp_path)
        assert len(status["untracked"]) == 7
        assert status["staged"] == []
        assert status["modified"] == []
        
        # Stage all files
        result = stage_all_changes(tmp_path)
        assert result is True
        
        # Check status - should show all as staged
        status = get_full_status(tmp_path)
        assert len(status["staged"]) == 7
        assert status["untracked"] == []
        assert status["modified"] == []
        
        # Commit initial version
        commit_result = commit_staged_files("Initial project setup", tmp_path)
        assert commit_result["success"] is True
        assert commit_result["commit_hash"] is not None
        assert len(commit_result["commit_hash"]) == 7
        
        # Check final status - should be clean
        status = get_full_status(tmp_path)
        assert status == {"staged": [], "modified": [], "untracked": []}
        
        # Verify commit history
        commits = list(repo.iter_commits())
        assert len(commits) == 1
        assert commits[0].message.strip() == "Initial project setup"

    def test_complete_workflow_modify_and_commit_cycle(self, tmp_path: Path) -> None:
        """Test workflow: existing repo → modify files → stage selectively → commit → repeat."""
        # Setup: Create repo with initial commit
        repo = Repo.init(tmp_path)
        
        # Create initial files
        main_file = tmp_path / "main.py"
        config_file = tmp_path / "config.yml"
        readme_file = tmp_path / "README.md"
        
        main_file.write_text('def greet(name):\n    return f"Hello, {name}!"')
        config_file.write_text("debug: false\nport: 8080")
        readme_file.write_text("# Project\n\nInitial version")
        
        repo.index.add([str(main_file), str(config_file), str(readme_file)])
        repo.index.commit("Initial commit")
        
        # === Cycle 1: Modify main.py, add tests ===
        
        # Modify existing file
        main_file.write_text('def greet(name):\n    return f"Hello, {name}!"\n\ndef farewell(name):\n    return f"Goodbye, {name}!"')
        
        # Add new file
        test_file = tmp_path / "test_main.py"
        test_file.write_text("from main import greet, farewell\n\ndef test_greet():\n    assert greet('World') == 'Hello, World!'")
        
        # Check status
        status = get_full_status(tmp_path)
        assert "main.py" in status["modified"]
        assert "test_main.py" in status["untracked"]
        assert len(status["modified"]) == 1
        assert len(status["untracked"]) == 1
        
        # Stage only specific files
        result = stage_specific_files([main_file, test_file], tmp_path)
        assert result is True
        
        # Commit cycle 1
        commit_result = commit_staged_files("Add farewell function and tests", tmp_path)
        assert commit_result["success"] is True
        
        # === Cycle 2: Update config and README ===
        
        # Modify config
        config_file.write_text("debug: true\nport: 3000\nlogging:\n  level: INFO")
        
        # Modify README
        readme_file.write_text("# Project\n\nVersion 2.0\n\n## Features\n- Greeting function\n- Farewell function")
        
        # Add another new file
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\n## v2.0\n- Added farewell function")
        
        # Use commit_all_changes for convenience
        commit_result = commit_all_changes("Update config, README, and add changelog", tmp_path)
        assert commit_result["success"] is True
        
        # === Cycle 3: Delete a file, modify another ===
        
        # Delete test file
        test_file.unlink()
        
        # Modify main file
        main_file.write_text('"""Main module with greetings."""\n\ndef greet(name):\n    return f"Hello, {name}!"\n\ndef farewell(name):\n    return f"Goodbye, {name}!"')
        
        # Check status shows deletion and modification
        status = get_full_status(tmp_path)
        assert "main.py" in status["modified"]
        assert "test_main.py" in status["modified"]  # Deleted files show as modified
        
        # Stage and commit
        result = stage_all_changes(tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Add docstring and remove tests", tmp_path)
        assert commit_result["success"] is True
        
        # Verify final state
        assert len(list(repo.iter_commits())) == 4
        assert not test_file.exists()
        assert main_file.read_text().startswith('"""Main module')
        
        # Final status should be clean
        final_status = get_full_status(tmp_path)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_error_recovery_workflow_invalid_operations(self, tmp_path: Path) -> None:
        """Test workflow with error scenarios and recovery."""
        # Setup: Create repo
        repo = Repo.init(tmp_path)
        
        # Test 1: Try to commit with no staged files
        commit_result = commit_staged_files("Empty commit", tmp_path)
        assert commit_result["success"] is False
        assert commit_result["error"] and ("no staged files" in commit_result["error"].lower() or "nothing to commit" in commit_result["error"].lower())
        
        # Test 2: Try to commit with empty message
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        repo.index.add([str(test_file)])
        
        commit_result = commit_staged_files("", tmp_path)
        assert commit_result["success"] is False
        assert commit_result["error"] and "message" in commit_result["error"].lower()
        
        # Recovery: Commit with proper message
        commit_result = commit_staged_files("Add test file", tmp_path)
        assert commit_result["success"] is True
        
        # Test 3: Try to stage non-existent file
        non_existent = tmp_path / "does_not_exist.txt"
        result = stage_specific_files([non_existent], tmp_path)
        assert result is False
        
        # Test 4: Try operations outside git repo
        non_git_dir = tmp_path / "not_git"
        non_git_dir.mkdir()
        
        assert not is_git_repository(non_git_dir)
        assert get_full_status(non_git_dir) == {"staged": [], "modified": [], "untracked": []}
        assert stage_all_changes(non_git_dir) is False
        
        commit_result = commit_all_changes("Should fail", non_git_dir)
        assert commit_result["success"] is False
        assert commit_result["error"] and ("git repository" in commit_result["error"].lower() or "not a git" in commit_result["error"].lower())
        
        # Recovery: Continue working in valid repo
        another_file = tmp_path / "recovery.txt"
        another_file.write_text("recovery content")
        
        commit_result = commit_all_changes("Recovery commit", tmp_path)
        assert commit_result["success"] is True

    def test_cross_platform_path_handling(self, tmp_path: Path) -> None:
        """Test that paths work correctly across different platforms."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create nested directory structure
        nested_dirs = [
            tmp_path / "src" / "utils",
            tmp_path / "tests" / "unit" / "utils",
            tmp_path / "docs" / "api" / "v1",
        ]
        
        for dir_path in nested_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create files in nested directories
        files_to_create = [
            tmp_path / "src" / "main.py",
            tmp_path / "src" / "utils" / "helpers.py",
            tmp_path / "tests" / "test_main.py",
            tmp_path / "tests" / "unit" / "utils" / "test_helpers.py",
            tmp_path / "docs" / "README.md",
            tmp_path / "docs" / "api" / "v1" / "endpoints.md",
        ]
        
        for file_path in files_to_create:
            file_path.write_text(f"Content for {file_path.name}")
        
        # Stage all files
        result = stage_all_changes(tmp_path)
        assert result is True
        
        # Check that all files are staged with correct paths
        staged_files = get_staged_changes(tmp_path)
        assert len(staged_files) == 6
        
        # Verify paths contain directory separators (but normalize for cross-platform)
        nested_files = [f for f in staged_files if ("/" in f or "\\" in f)]
        assert len(nested_files) >= 4  # At least the nested files
        
        # Commit and verify
        commit_result = commit_staged_files("Add nested structure", tmp_path)
        assert commit_result["success"] is True
        
        # Test modification of nested files
        (tmp_path / "src" / "utils" / "helpers.py").write_text("Modified helper content")
        (tmp_path / "docs" / "api" / "v1" / "endpoints.md").write_text("Modified API docs")
        
        # Check status shows correct relative paths
        status = get_full_status(tmp_path)
        modified_files = status["modified"]
        assert len(modified_files) == 2
        
        # Should contain proper path separators
        helper_found = any("helpers.py" in f and ("utils" in f) for f in modified_files)
        endpoints_found = any("endpoints.md" in f and ("api" in f) for f in modified_files)
        assert helper_found
        assert endpoints_found

    def test_performance_with_many_files(self, tmp_path: Path) -> None:
        """Test performance with larger number of files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create many files efficiently
        file_count = 200  # Reasonable number for testing
        
        # Create directory structure
        for i in range(10):
            (tmp_path / f"dir_{i}").mkdir()
        
        # Create files in different directories
        created_files = []
        for i in range(file_count):
            dir_num = i % 10
            file_path = tmp_path / f"dir_{dir_num}" / f"file_{i:03d}.txt"
            file_path.write_text(f"Content for file {i}")
            created_files.append(file_path)
        
        # Test 1: Status functions should handle many files efficiently
        start_time = time.time()
        status = get_full_status(tmp_path)
        status_time = time.time() - start_time
        
        assert len(status["untracked"]) == file_count
        assert status["staged"] == []
        assert status["modified"] == []
        # Should complete in reasonable time (less than 5 seconds)
        assert status_time < 5.0
        
        # Test 2: Staging many files should be efficient
        start_time = time.time()
        result = stage_all_changes(tmp_path)
        staging_time = time.time() - start_time
        
        assert result is True
        assert staging_time < 5.0
        
        # Verify all files are staged
        staged_files = get_staged_changes(tmp_path)
        assert len(staged_files) == file_count
        
        # Test 3: Committing many files should work
        start_time = time.time()
        commit_result = commit_staged_files("Add many files", tmp_path)
        commit_time = time.time() - start_time
        
        assert commit_result["success"] is True
        assert commit_time < 10.0  # Commits can take longer
        
        # Test 4: Modify many files and test status again
        for i in range(0, file_count, 10):  # Modify every 10th file
            created_files[i].write_text(f"Modified content for file {i}")
        
        start_time = time.time()
        status = get_full_status(tmp_path)
        modified_status_time = time.time() - start_time
        
        assert len(status["modified"]) == file_count // 10
        assert modified_status_time < 5.0

    def test_mixed_operations_complex_scenario(self, tmp_path: Path) -> None:
        """Test complex scenario with multiple types of operations."""
        # Setup: Create repo with initial structure
        repo = Repo.init(tmp_path)
        
        # Initial commit
        initial_files = {
            tmp_path / "src" / "core.py": "# Core module",
            tmp_path / "src" / "utils.py": "# Utilities",
            tmp_path / "tests" / "test_core.py": "# Core tests",
            tmp_path / "README.md": "# Project",
            tmp_path / "config.json": '{"version": "1.0"}',
        }
        
        for file_path, content in initial_files.items():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        repo.index.add([str(f) for f in initial_files.keys()])
        repo.index.commit("Initial commit")
        
        # === Complex change scenario ===
        
        # 1. Modify existing files
        (tmp_path / "src" / "core.py").write_text("# Core module\nclass Core:\n    pass")
        (tmp_path / "README.md").write_text("# Project\n\nUpdated documentation")
        
        # 2. Delete a file
        (tmp_path / "src" / "utils.py").unlink()
        
        # 3. Add new files
        (tmp_path / "src" / "api.py").write_text("# API module")
        (tmp_path / "tests" / "test_api.py").write_text("# API tests")
        (tmp_path / "docs" / "guide.md").parent.mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# User Guide")
        
        # 4. Stage some changes selectively
        files_to_stage = [
            tmp_path / "src" / "core.py",  # Modified
            tmp_path / "src" / "api.py",   # New
        ]
        
        result = stage_specific_files(files_to_stage, tmp_path)
        assert result is True
        
        # Check status shows mixed state
        status = get_full_status(tmp_path)
        assert "src/core.py" in status["staged"] or "src\\core.py" in status["staged"]
        assert "src/api.py" in status["staged"] or "src\\api.py" in status["staged"]
        assert "README.md" in status["modified"]
        assert "src/utils.py" in status["modified"] or "src\\utils.py" in status["modified"]  # Deleted
        assert "tests/test_api.py" in status["untracked"] or "tests\\test_api.py" in status["untracked"]
        assert any("guide.md" in f for f in status["untracked"])
        
        # 5. Commit partial changes
        commit_result = commit_staged_files("Add API module and update core", tmp_path)
        assert commit_result["success"] is True
        
        # 6. Stage and commit remaining changes
        commit_result = commit_all_changes("Update README, remove utils, add tests and docs", tmp_path)
        assert commit_result["success"] is True
        
        # Verify final state
        final_status = get_full_status(tmp_path)
        assert final_status == {"staged": [], "modified": [], "untracked": []}
        
        # Verify commit history
        commits = list(repo.iter_commits())
        assert len(commits) == 3
        
        # Verify final file state
        assert (tmp_path / "src" / "core.py").read_text().startswith("# Core module\nclass Core:")
        assert not (tmp_path / "src" / "utils.py").exists()
        assert (tmp_path / "src" / "api.py").exists()
        assert (tmp_path / "tests" / "test_api.py").exists()
        assert (tmp_path / "docs" / "guide.md").exists()

    def test_workflow_with_gitignore(self, tmp_path: Path) -> None:
        """Test workflow respects .gitignore files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n*.tmp\n__pycache__/\n.env\nbuild/\n")
        
        # Create mix of tracked and ignored files
        tracked_files = [
            tmp_path / "main.py",
            tmp_path / "config.yml",
        ]
        
        ignored_files = [
            tmp_path / "debug.log",
            tmp_path / "temp.tmp",
            tmp_path / ".env",
            tmp_path / "__pycache__" / "main.cpython-39.pyc",
            tmp_path / "build" / "output.bin",
        ]
        
        # Create tracked files
        for file_path in tracked_files:
            file_path.write_text(f"Content for {file_path.name}")
        
        # Create ignored files
        for file_path in ignored_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if file_path.suffix == ".pyc":
                file_path.write_bytes(b"fake bytecode")
            else:
                file_path.write_text(f"Content for {file_path.name}")
        
        # Check status - should only show tracked files and .gitignore
        status = get_full_status(tmp_path)
        
        # Should include .gitignore and tracked files but not ignored files
        untracked_names = [Path(f).name for f in status["untracked"]]
        assert ".gitignore" in untracked_names
        assert "main.py" in untracked_names
        assert "config.yml" in untracked_names
        
        # Should not include ignored files
        assert "debug.log" not in untracked_names
        assert "temp.tmp" not in untracked_names
        assert ".env" not in untracked_names
        assert not any("__pycache__" in f for f in status["untracked"])
        assert not any("build" in f for f in status["untracked"])
        
        # Stage and commit
        result = stage_all_changes(tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Initial commit with gitignore", tmp_path)
        assert commit_result["success"] is True
        
        # Verify ignored files still exist but aren't tracked
        for file_path in ignored_files:
            assert file_path.exists()
        
        # Final status should be clean (ignored files don't show)
        final_status = get_full_status(tmp_path)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_binary_files_handling(self, tmp_path: Path) -> None:
        """Test handling of binary files in git operations."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create text files
        text_file = tmp_path / "text.txt"
        text_file.write_text("This is a text file with normal content.")
        
        # Create binary files (simulate different types)
        binary_files = [
            tmp_path / "image.png",
            tmp_path / "data.bin",
            tmp_path / "document.pdf",
        ]
        
        # Write binary content
        for file_path in binary_files:
            # Create fake binary content
            binary_content = bytes(range(256)) + b"fake binary data" * 100
            file_path.write_bytes(binary_content)
        
        # Check status includes all files
        status = get_full_status(tmp_path)
        assert len(status["untracked"]) == 4  # 1 text + 3 binary
        
        # Stage all files (should handle binary files correctly)
        result = stage_all_changes(tmp_path)
        assert result is True
        
        # Commit all files
        commit_result = commit_staged_files("Add text and binary files", tmp_path)
        assert commit_result["success"] is True
        
        # Modify binary file
        (tmp_path / "image.png").write_bytes(b"different binary content")
        
        # Should detect binary file modification
        status = get_full_status(tmp_path)
        assert "image.png" in status["modified"]
        
        # Should be able to stage and commit binary file changes
        result = stage_specific_files([tmp_path / "image.png"], tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Update binary file", tmp_path)
        assert commit_result["success"] is True


class TestErrorScenarios:
    """Test various error scenarios and edge cases."""

    def test_corrupted_git_repository_handling(self, tmp_path: Path) -> None:
        """Test handling of corrupted or invalid git repositories."""
        # Create a .git directory but not a valid repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Should detect as invalid git repository
        assert not is_git_repository(tmp_path)
        
        # All operations should fail gracefully
        assert get_full_status(tmp_path) == {"staged": [], "modified": [], "untracked": []}
        assert stage_all_changes(tmp_path) is False
        
        commit_result = commit_all_changes("Should fail", tmp_path)
        assert commit_result["success"] is False
        
        # Create file and try to work with it
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        assert stage_specific_files([test_file], tmp_path) is False

    def test_permission_errors_simulation(self, tmp_path: Path) -> None:
        """Test handling of permission-related errors."""
        # Create valid git repo
        repo = Repo.init(tmp_path)
        
        # Create and stage file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        repo.index.add([str(test_file)])
        
        # Simulate git command errors using mocking
        with patch("mcp_coder.utils.git_operations.Repo") as mock_repo:
            mock_instance = mock_repo.return_value
            mock_instance.index.commit.side_effect = GitCommandError("commit", 128, "Permission denied")
            
            # Should handle permission error gracefully
            commit_result = commit_staged_files("Should fail with permission error", tmp_path)
            assert commit_result["success"] is False
            assert commit_result["error"] is not None

    def test_concurrent_access_simulation(self, tmp_path: Path) -> None:
        """Test handling when git operations might conflict."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and commit initial file
        test_file = tmp_path / "test.txt"
        test_file.write_text("initial content")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")
        
        # Modify file
        test_file.write_text("modified content")
        
        # Stage the file
        result = stage_specific_files([test_file], tmp_path)
        assert result is True
        
        # Simulate concurrent modification after staging (like another process changed it)
        test_file.write_text("content modified by another process")
        
        # Check that git operations still work despite the concurrent change
        # The staged version and working directory version will be different
        status = get_full_status(tmp_path)
        
        # File should appear in both staged and modified (working directory changed after staging)
        assert "test.txt" in status["staged"]
        assert "test.txt" in status["modified"]
        
        # Should still be able to commit the staged version
        commit_result = commit_staged_files("Commit staged version", tmp_path)
        assert commit_result["success"] is True
        
        # After commit, file should only appear as modified (working dir different from committed)
        final_status = get_full_status(tmp_path)
        assert "test.txt" in final_status["modified"]
        assert "test.txt" not in final_status["staged"]
        assert final_status["untracked"] == []

    def test_large_commit_message_handling(self, tmp_path: Path) -> None:
        """Test handling of very large commit messages."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create file to commit
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        repo.index.add([str(test_file)])
        
        # Create very large commit message
        large_message = "Large commit message\n" + "x" * 10000  # 10KB message
        
        # Should handle large messages
        commit_result = commit_staged_files(large_message, tmp_path)
        assert commit_result["success"] is True
        
        # Verify message was preserved
        commits = list(repo.iter_commits())
        assert commits[0].message.strip() == large_message

    def test_unicode_content_handling(self, tmp_path: Path) -> None:
        """Test handling of files with unicode content."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files with various unicode content
        unicode_files = {
            tmp_path / "chinese.txt": "你好世界 Chinese text",
            tmp_path / "emoji.txt": "Hello 🌍 World! 🚀 🎉",
            tmp_path / "accents.txt": "Café naïve résumé",
            tmp_path / "mixed.py": '# -*- coding: utf-8 -*-\nprint("Unicode: 🐍")',
        }
        
        for file_path, content in unicode_files.items():
            file_path.write_text(content, encoding='utf-8')
        
        # Should handle unicode files correctly
        status = get_full_status(tmp_path)
        assert len(status["untracked"]) == 4
        
        # Stage and commit
        result = stage_all_changes(tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Add unicode content files 🎯", tmp_path)
        assert commit_result["success"] is True
        
        # Verify unicode commit message
        commits = list(repo.iter_commits())
        assert "🎯" in commits[0].message

    def test_deep_directory_structure(self, tmp_path: Path) -> None:
        """Test with very deep directory structures."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create deep directory structure
        deep_path = tmp_path
        for i in range(20):  # 20 levels deep
            deep_path = deep_path / f"level_{i}"
        
        deep_path.mkdir(parents=True)
        deep_file = deep_path / "deep_file.txt"
        deep_file.write_text("Content in deep directory")
        
        # Should handle deep paths
        status = get_full_status(tmp_path)
        assert len(status["untracked"]) == 1
        
        # Check the path contains multiple separators
        deep_file_path = status["untracked"][0]
        separator_count = deep_file_path.count("/") + deep_file_path.count("\\")
        assert separator_count >= 19  # At least 19 directory separators
        
        # Stage and commit deep file
        result = stage_all_changes(tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Add file in deep directory", tmp_path)
        assert commit_result["success"] is True


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility aspects."""

    def test_path_separator_normalization(self, tmp_path: Path) -> None:
        """Test that path separators work correctly regardless of platform."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files in subdirectories
        files_to_create = [
            tmp_path / "src" / "module" / "file1.py",
            tmp_path / "tests" / "unit" / "test_file1.py",
        ]
        
        for file_path in files_to_create:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"Content for {file_path.name}")
        
        # Stage files using absolute paths
        result = stage_specific_files(files_to_create, tmp_path)
        assert result is True
        
        # Get staged files - should use consistent path format
        staged_files = get_staged_changes(tmp_path)
        assert len(staged_files) == 2
        
        # Paths should be relative and not contain the tmp_path
        for staged_file in staged_files:
            assert str(tmp_path) not in staged_file
            assert staged_file.startswith("src") or staged_file.startswith("tests")

    def test_case_sensitivity_handling(self, tmp_path: Path) -> None:
        """Test handling of case-sensitive/insensitive file systems."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create files with different cases
        file1 = tmp_path / "File.txt"
        file2 = tmp_path / "file.TXT"
        
        file1.write_text("Content 1")
        
        # On case-insensitive systems, this might overwrite file1
        # On case-sensitive systems, this creates a separate file
        try:
            file2.write_text("Content 2")
            both_exist = file1.exists() and file2.exists()
        except Exception:
            both_exist = False
        
        # Stage and commit what exists
        result = stage_all_changes(tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Add case-variant files", tmp_path)
        assert commit_result["success"] is True
        
        # Should work regardless of file system case sensitivity
        status = get_full_status(tmp_path)
        assert status == {"staged": [], "modified": [], "untracked": []}

    @pytest.mark.skipif(os.name == "nt", reason="Long paths test mainly for Unix systems")
    def test_long_filename_handling(self, tmp_path: Path) -> None:
        """Test handling of very long filenames."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create file with very long name (but within limits)
        long_name = "very_long_filename_" + "x" * 200 + ".txt"
        long_file = tmp_path / long_name
        
        try:
            long_file.write_text("Content in file with long name")
            
            # Should handle long filenames
            status = get_full_status(tmp_path)
            assert len(status["untracked"]) == 1
            
            result = stage_all_changes(tmp_path)
            assert result is True
            
            commit_result = commit_staged_files("Add file with long name", tmp_path)
            assert commit_result["success"] is True
            
        except OSError:
            # Skip if filesystem doesn't support long names
            pytest.skip("Filesystem doesn't support long filenames")


class TestPerformanceValidation:
    """Test performance characteristics of git operations."""

    def test_status_performance_with_many_files(self, tmp_path: Path) -> None:
        """Test that status operations complete in reasonable time."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create many files
        file_count = 500
        for i in range(file_count):
            dir_name = f"dir_{i // 50}"  # Group files in directories
            (tmp_path / dir_name).mkdir(exist_ok=True)
            file_path = tmp_path / dir_name / f"file_{i:03d}.txt"
            file_path.write_text(f"Content {i}")
        
        # Test status performance
        start_time = time.time()
        status = get_full_status(tmp_path)
        status_time = time.time() - start_time
        
        assert len(status["untracked"]) == file_count
        assert status_time < 10.0  # Should complete within 10 seconds
        
        # Test staging performance
        start_time = time.time()
        result = stage_all_changes(tmp_path)
        staging_time = time.time() - start_time
        
        assert result is True
        assert staging_time < 15.0  # Should complete within 15 seconds

    def test_memory_usage_with_large_files(self, tmp_path: Path) -> None:
        """Test that operations don't consume excessive memory with large files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create a moderately large file (1MB)
        large_file = tmp_path / "large_file.txt"
        large_content = "Large content line\n" * 50000  # About 1MB
        large_file.write_text(large_content)
        
        # Operations should work with large files
        status = get_full_status(tmp_path)
        assert "large_file.txt" in status["untracked"]
        
        result = stage_all_changes(tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Add large file", tmp_path)
        assert commit_result["success"] is True
        
        # Modify large file
        large_file.write_text(large_content + "\nAdditional content")
        
        # Should handle modification efficiently
        status = get_full_status(tmp_path)
        assert "large_file.txt" in status["modified"]

    def test_repeated_operations_performance(self, tmp_path: Path) -> None:
        """Test performance of repeated operations."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create initial file
        test_file = tmp_path / "test.txt"
        test_file.write_text("initial")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial")
        
        # Perform many small modifications and check performance
        num_iterations = 50
        
        start_time = time.time()
        for i in range(num_iterations):
            # Modify file
            test_file.write_text(f"Content iteration {i}")
            
            # Check status
            status = get_full_status(tmp_path)
            assert "test.txt" in status["modified"]
            
            # Stage and commit
            result = stage_all_changes(tmp_path)
            assert result is True
            
            commit_result = commit_staged_files(f"Commit {i}", tmp_path)
            assert commit_result["success"] is True
        
        total_time = time.time() - start_time
        avg_time_per_iteration = total_time / num_iterations
        
        # Each iteration should average less than 2 seconds (git operations can be slow)
        assert avg_time_per_iteration < 2.0
        
        # Verify all commits were created
        commits = list(repo.iter_commits())
        assert len(commits) == num_iterations + 1  # +1 for initial commit


class TestRealRepositorySimulation:
    """Test with realistic repository structures and workflows."""

    def test_python_project_simulation(self, tmp_path: Path) -> None:
        """Simulate working with a typical Python project."""
        # Initialize project
        repo = Repo.init(tmp_path)
        
        # Create typical Python project structure
        project_structure = {
            # Root files
            tmp_path / "README.md": "# My Python Project\n\nA sample project.",
            tmp_path / "requirements.txt": "requests>=2.25.0\npytest>=6.0.0\nblack>=21.0.0",
            tmp_path / "setup.py": "from setuptools import setup, find_packages\n\nsetup(name='myproject')",
            tmp_path / ".gitignore": "*.pyc\n__pycache__/\n.env\n*.egg-info/\nbuild/\ndist/",
            tmp_path / "pyproject.toml": "[tool.black]\nline-length = 88",
            
            # Source code
            tmp_path / "src" / "myproject" / "__init__.py": "__version__ = '0.1.0'",
            tmp_path / "src" / "myproject" / "main.py": "def main():\n    print('Hello, World!')",
            tmp_path / "src" / "myproject" / "utils.py": "def helper():\n    return 'help'",
            
            # Tests
            tmp_path / "tests" / "__init__.py": "",
            tmp_path / "tests" / "test_main.py": "from myproject.main import main\n\ndef test_main():\n    assert main() is None",
            tmp_path / "tests" / "test_utils.py": "from myproject.utils import helper\n\ndef test_helper():\n    assert helper() == 'help'",
            
            # Documentation
            tmp_path / "docs" / "index.md": "# Documentation\n\nProject documentation.",
            tmp_path / "docs" / "api.md": "# API Reference\n\n## Functions",
        }
        
        # Create all files
        for file_path, content in project_structure.items():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Initial commit
        result = stage_all_changes(tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Initial project setup", tmp_path)
        assert commit_result["success"] is True
        
        # === Development workflow simulation ===
        
        # Add new feature
        feature_file = tmp_path / "src" / "myproject" / "feature.py"
        feature_file.write_text("class Feature:\n    def do_something(self):\n        return 'done'")
        
        # Add feature test
        feature_test = tmp_path / "tests" / "test_feature.py"
        feature_test.write_text("from myproject.feature import Feature\n\ndef test_feature():\n    f = Feature()\n    assert f.do_something() == 'done'")
        
        # Update main to use feature
        main_file = tmp_path / "src" / "myproject" / "main.py"
        main_file.write_text("from .feature import Feature\n\ndef main():\n    f = Feature()\n    print(f.do_something())")
        
        # Commit feature
        commit_result = commit_all_changes("Add feature with tests", tmp_path)
        assert commit_result["success"] is True
        
        # === Bug fix workflow ===
        
        # Fix bug in utils
        utils_file = tmp_path / "src" / "myproject" / "utils.py"
        utils_file.write_text("def helper():\n    return 'help'  # Fixed bug\n\ndef new_helper():\n    return 'new help'")
        
        # Update test
        utils_test = tmp_path / "tests" / "test_utils.py"
        utils_test.write_text("from myproject.utils import helper, new_helper\n\ndef test_helper():\n    assert helper() == 'help'\n\ndef test_new_helper():\n    assert new_helper() == 'new help'")
        
        # Stage only specific files for bug fix
        result = stage_specific_files([utils_file, utils_test], tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Fix bug in utils and add new helper", tmp_path)
        assert commit_result["success"] is True
        
        # === Documentation update ===
        
        # Update documentation
        (tmp_path / "README.md").write_text("# My Python Project\n\nA sample project with features.\n\n## Installation\n\n```bash\npip install -e .\n```")
        (tmp_path / "docs" / "api.md").write_text("# API Reference\n\n## Classes\n\n### Feature\n\nMain feature class.")
        
        commit_result = commit_all_changes("Update documentation", tmp_path)
        assert commit_result["success"] is True
        
        # Verify final state
        commits = list(repo.iter_commits())
        assert len(commits) == 4
        
        final_status = get_full_status(tmp_path)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_web_project_simulation(self, tmp_path: Path) -> None:
        """Simulate working with a web development project."""
        # Initialize project
        repo = Repo.init(tmp_path)
        
        # Create web project structure
        web_structure = {
            # Root files
            tmp_path / "package.json": '{"name": "my-web-app", "version": "1.0.0"}',
            tmp_path / "index.html": "<!DOCTYPE html>\n<html>\n<head><title>My App</title></head>\n<body><h1>Hello</h1></body>\n</html>",
            tmp_path / ".gitignore": "node_modules/\n.env\ndist/\n*.log",
            
            # CSS
            tmp_path / "css" / "style.css": "body { font-family: Arial; }\nh1 { color: blue; }",
            tmp_path / "css" / "responsive.css": "@media (max-width: 768px) { h1 { font-size: 1.5em; } }",
            
            # JavaScript
            tmp_path / "js" / "main.js": "document.addEventListener('DOMContentLoaded', function() {\n    console.log('App loaded');\n});",
            tmp_path / "js" / "utils.js": "function formatDate(date) {\n    return date.toLocaleDateString();\n}",
            
            # Assets
            tmp_path / "images" / "logo.svg": "<svg><!-- Logo SVG content --></svg>",
            tmp_path / "assets" / "data.json": '{"users": [], "settings": {}}',
        }
        
        # Create all files
        for file_path, content in web_structure.items():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Initial commit
        commit_result = commit_all_changes("Initial web project setup", tmp_path)
        assert commit_result["success"] is True
        
        # === Frontend development workflow ===
        
        # Update HTML structure
        (tmp_path / "index.html").write_text("""<!DOCTYPE html>
<html>
<head>
    <title>My App</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/responsive.css">
</head>
<body>
    <header><h1>My Web App</h1></header>
    <main><p>Welcome to my application!</p></main>
    <script src="js/main.js"></script>
</body>
</html>""")
        
        # Enhance CSS
        (tmp_path / "css" / "style.css").write_text("""body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}

header {
    background: #333;
    color: white;
    padding: 1rem;
}

h1 {
    color: white;
    margin: 0;
}

main {
    padding: 2rem;
}""")
        
        # Add JavaScript functionality
        (tmp_path / "js" / "main.js").write_text("""document.addEventListener('DOMContentLoaded', function() {
    console.log('App loaded');
    
    // Add click handler
    const header = document.querySelector('header');
    header.addEventListener('click', function() {
        alert('Header clicked!');
    });
});""")
        
        # Stage frontend changes
        frontend_files = [
            tmp_path / "index.html",
            tmp_path / "css" / "style.css",
            tmp_path / "js" / "main.js",
        ]
        
        result = stage_specific_files(frontend_files, tmp_path)
        assert result is True
        
        commit_result = commit_staged_files("Enhance frontend with styling and interactivity", tmp_path)
        assert commit_result["success"] is True
        
        # === Add new features ===
        
        # Add new page
        (tmp_path / "about.html").write_text("""<!DOCTYPE html>
<html>
<head>
    <title>About - My App</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header><h1>About Us</h1></header>
    <main><p>This is the about page.</p></main>
</body>
</html>""")
        
        # Add navigation JavaScript
        (tmp_path / "js" / "navigation.js").write_text("""function navigate(page) {
    window.location.href = page;
}

function setupNavigation() {
    // Setup navigation logic
    console.log('Navigation setup complete');
}""")
        
        commit_result = commit_all_changes("Add about page and navigation", tmp_path)
        assert commit_result["success"] is True
        
        # Verify project state
        commits = list(repo.iter_commits())
        assert len(commits) == 3
        
        final_status = get_full_status(tmp_path)
        assert final_status == {"staged": [], "modified": [], "untracked": []}
