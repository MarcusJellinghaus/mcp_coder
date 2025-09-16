"""Test git workflows with end-to-end integration testing."""

import pytest
from pathlib import Path
from git import Repo

from mcp_coder.utils.git_operations import (
    is_git_repository,
    get_staged_changes,
    get_unstaged_changes,
    get_full_status,
    stage_specific_files,
    stage_all_changes,
    commit_staged_files,
    commit_all_changes,
)


class TestGitWorkflows:
    """Test complete git workflow scenarios without mocking."""

    def test_new_project_to_first_commit(self, git_repo: Path) -> None:
        """Test workflow: create new project, add files, stage, and commit."""
        project_dir = git_repo
        repo = Repo(project_dir)
        
        # Verify we start with a clean git repository
        assert is_git_repository(project_dir) is True
        
        # Create project files inline
        files = {
            "main.py": "print('hello world')",
            "README.md": "# My Project\n\nDescription here.",
            "src/utils.py": "def helper():\n    pass",
            "config.json": '{"debug": true}'
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

    def test_modify_existing_files_workflow(self, git_repo_with_files: Path) -> None:
        """Test workflow: modify existing tracked files and commit changes."""
        project_dir = git_repo_with_files
        repo = Repo(project_dir)
        
        # Verify starting state - should have committed files
        initial_commits = list(repo.iter_commits())
        assert len(initial_commits) == 1
        assert initial_commits[0].message == "Initial commit with test files"
        
        # Verify no pending changes initially
        status = get_full_status(project_dir)
        assert status == {"staged": [], "modified": [], "untracked": []}
        
        # Modify existing files
        file1 = project_dir / "file1.txt"
        file2 = project_dir / "subdir" / "file2.py"
        file3 = project_dir / "config.json"
        
        file1.write_text("Updated content for file 1\nAdded a new line")
        file2.write_text("# Updated Python file\nprint('Hello, Updated World!')\nprint('New functionality')")
        file3.write_text('{"setting": "updated_value", "enabled": false, "new_option": 42}')
        
        # Check that modifications are detected
        status = get_full_status(project_dir)
        assert len(status["modified"]) == 3
        assert status["staged"] == []
        assert status["untracked"] == []
        assert "file1.txt" in status["modified"]
        assert "subdir/file2.py" in status["modified"]
        assert "config.json" in status["modified"]
        
        # Stage and commit modified files
        stage_result = stage_all_changes(project_dir)
        assert stage_result is True
        
        # Verify staging
        staged = get_staged_changes(project_dir)
        assert len(staged) == 3
        assert "file1.txt" in staged
        assert "subdir/file2.py" in staged
        assert "config.json" in staged
        
        # Commit changes
        commit_result = commit_staged_files("Update all files with new content", project_dir)
        assert commit_result["success"] is True
        assert commit_result["error"] is None
        
        # Verify final state
        final_commits = list(repo.iter_commits())
        assert len(final_commits) == 2
        assert final_commits[0].message == "Update all files with new content"
        
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_mixed_file_operations_workflow(self, git_repo_with_files: Path) -> None:
        """Test workflow: mix of adding new files, modifying existing, and deletions."""
        project_dir = git_repo_with_files
        repo = Repo(project_dir)
        
        # Verify starting state
        initial_status = get_full_status(project_dir)
        assert initial_status == {"staged": [], "modified": [], "untracked": []}
        
        # Mix of operations:
        # 1. Modify existing file
        file1 = project_dir / "file1.txt"
        file1.write_text("Modified content in file1")
        
        # 2. Add new files
        new_file = project_dir / "new_feature.py"
        new_file.write_text("# New feature implementation\nclass Feature:\n    pass")
        
        nested_new = project_dir / "docs" / "guide.md"
        nested_new.parent.mkdir(exist_ok=True)
        nested_new.write_text("# User Guide\n\n## Getting Started")
        
        # 3. Delete existing file
        file_to_delete = project_dir / "config.json"
        file_to_delete.unlink()
        
        # Check mixed status
        status = get_full_status(project_dir)
        assert len(status["modified"]) >= 1  # file1.txt and possibly config.json deletion
        assert len(status["untracked"]) == 2  # new_feature.py and docs/guide.md
        assert status["staged"] == []
        
        # Stage everything
        stage_result = stage_all_changes(project_dir)
        assert stage_result is True
        
        # Verify all changes staged
        staged = get_staged_changes(project_dir)
        assert len(staged) >= 3  # At minimum: modified file1, new files, deletion
        assert "file1.txt" in staged
        assert "new_feature.py" in staged
        assert "docs/guide.md" in staged
        
        # Commit mixed operations
        commit_result = commit_staged_files("Mixed operations: modify, add, delete", project_dir)
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

    def test_staging_specific_files_workflow(self, git_repo: Path) -> None:
        """Test workflow: selectively stage specific files for commit."""
        project_dir = git_repo
        repo = Repo(project_dir)
        
        # Create multiple files
        files = {
            "feature_a.py": "# Feature A\nclass FeatureA:\n    pass",
            "feature_b.py": "# Feature B\nclass FeatureB:\n    pass",
            "docs/readme.md": "# Documentation\n\nFeature docs",
            "config.ini": "[settings]\ndebug=true",
            "temp_notes.txt": "Temporary development notes"
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
            project_dir / "config.ini"
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
        commit_result = commit_staged_files("Add feature A and documentation", project_dir)
        assert commit_result["success"] is True
        
        # Stage and commit remaining files separately
        remaining_files = [
            project_dir / "feature_b.py",
            project_dir / "temp_notes.txt"
        ]
        
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

    def test_staging_all_changes_workflow(self, git_repo: Path) -> None:
        """Test workflow: stage all changes at once and commit."""
        project_dir = git_repo
        repo = Repo(project_dir)
        
        # Create various types of files
        files = {
            "app.py": "# Main application\nif __name__ == '__main__':\n    print('Hello!')",
            "utils/helpers.py": "def utility_function():\n    return 'helper'",
            "data/sample.json": '{"key": "value", "items": [1, 2, 3]}',
            "README.md": "# Project\n\nThis is a test project.",
            "requirements.txt": "requests==2.28.0\nflask==2.1.0"
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
        commit_result = commit_staged_files("Initial project setup with all files", project_dir)
        assert commit_result["success"] is True
        assert commit_result["error"] is None
        
        # Verify clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}
        
        # Verify commit exists
        commits = list(repo.iter_commits())
        assert len(commits) == 1
        assert commits[0].message == "Initial project setup with all files"

    def test_commit_workflows(self, git_repo: Path) -> None:
        """Test various commit scenarios with different message formats."""
        project_dir = git_repo
        repo = Repo(project_dir)
        
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

    def test_multiple_commit_cycles(self, git_repo: Path) -> None:
        """Test workflow: multiple rounds of changes and commits."""
        project_dir = git_repo
        repo = Repo(project_dir)
        
        # Cycle 1: Initial setup
        cycle1_files = {
            "main.py": "# Main module\nprint('cycle 1')",
            "config.py": "DEBUG = True"
        }
        
        for path, content in cycle1_files.items():
            (project_dir / path).write_text(content)
        
        commit_result1 = commit_all_changes("Cycle 1: Initial setup", project_dir)
        assert commit_result1["success"] is True
        
        # Cycle 2: Add features
        cycle2_files = {
            "features/auth.py": "class AuthManager:\n    pass",
            "features/database.py": "class DatabaseManager:\n    pass"
        }
        
        for path, content in cycle2_files.items():
            file_path = project_dir / path
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)
        
        commit_result2 = commit_all_changes("Cycle 2: Add feature modules", project_dir)
        assert commit_result2["success"] is True
        
        # Cycle 3: Modify existing and add tests
        (project_dir / "main.py").write_text("# Main module\nprint('cycle 3 - updated')")
        (project_dir / "tests" / "test_main.py").parent.mkdir(exist_ok=True)
        (project_dir / "tests" / "test_main.py").write_text("def test_main():\n    assert True")
        
        commit_result3 = commit_all_changes("Cycle 3: Update main and add tests", project_dir)
        assert commit_result3["success"] is True
        
        # Cycle 4: Cleanup and documentation
        (project_dir / "config.py").write_text("DEBUG = False\nVERSION = '1.0.0'")
        (project_dir / "README.md").write_text("# Project Documentation\n\nVersion 1.0.0")
        
        commit_result4 = commit_all_changes("Cycle 4: Production config and docs", project_dir)
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

    def test_cross_platform_paths(self, git_repo: Path) -> None:
        """Test workflow with files in nested directories and various path formats."""
        project_dir = git_repo
        
        # Create files with various path separators and nested structures
        files = {
            "src/core/main.py": "# Core module",
            "src/utils/helpers/string_utils.py": "def clean_string(): pass",
            "tests/unit/test_core.py": "def test_core(): pass",
            "tests/integration/api/test_endpoints.py": "def test_api(): pass",
            "docs/guides/user_guide.md": "# User Guide",
            "data/samples/config.json": '{"test": true}',
            "scripts/build/compile.sh": "#!/bin/bash\necho 'build'"
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
            project_dir / "src" / "utils" / "helpers" / "string_utils.py"
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
        commit_result2 = commit_staged_files("Add tests, docs, and scripts", project_dir)
        assert commit_result2["success"] is True
        
        # Verify all files committed
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}
        
        # Verify all created files exist
        for path in files.keys():
            assert (project_dir / path).exists()

    def test_unicode_and_binary_files(self, git_repo: Path) -> None:
        """Test workflow with unicode filenames and binary file content."""
        project_dir = git_repo
        
        # Create files with unicode content and names
        unicode_files = {
            "测试文件.py": "# 中文注释\nprint('你好世界')",
            "файл.txt": "Привет мир",
            "archivo_español.md": "# Título\n\nContenido en español: áéíóú",
            "émoji_test.txt": "Test with emoji: 🐍 🚀 ✅"
        }
        
        for filename, content in unicode_files.items():
            file_path = project_dir / filename
            file_path.write_text(content, encoding='utf-8')
        
        # Create binary file content (simple binary data)
        binary_file = project_dir / "binary_data.bin"
        binary_content = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])  # PNG header-like
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
        unicode_file.write_text("# 更新的中文注释\nprint('更新后的你好世界')", encoding='utf-8')
        
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

    def test_performance_with_many_files(self, git_repo: Path) -> None:
        """Test workflow performance with large number of files."""
        project_dir = git_repo
        
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
        assert staging_time < 5.0  # Should complete quickly
        
        # Verify all files staged
        staged = get_staged_changes(project_dir)
        assert len(staged) == 60  # 50 + 10 nested files
        
        # Test commit performance
        start_time = time.time()
        commit_result = commit_staged_files("Add many files for performance test", project_dir)
        commit_time = time.time() - start_time
        
        assert commit_result["success"] is True
        assert commit_time < 5.0  # Should commit quickly
        
        # Verify clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_incremental_staging_workflow(self, git_repo: Path) -> None:
        """Test workflow: stage files incrementally and commit in batches."""
        project_dir = git_repo
        
        # Create files for incremental staging
        batch1_files = [
            "batch1_file1.py",
            "batch1_file2.py",
            "batch1_file3.py"
        ]
        
        batch2_files = [
            "batch2_file1.py",
            "batch2_file2.py"
        ]
        
        batch3_files = [
            "batch3_file1.py",
            "batch3_file2.py",
            "batch3_file3.py",
            "batch3_file4.py"
        ]
        
        # Create all files
        all_files = batch1_files + batch2_files + batch3_files
        for filename in all_files:
            (project_dir / filename).write_text(f"# {filename}\nclass {filename.replace('.py', '').title()}:\n    pass")
        
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
        
        commit_result3 = commit_staged_files("Batch 3: Additional features", project_dir)
        assert commit_result3["success"] is True
        
        # Verify all batches committed
        repo = Repo(project_dir)
        commits = list(repo.iter_commits())
        assert len(commits) == 3
        
        # Verify final clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_file_modification_detection_workflow(self, git_repo_with_files: Path) -> None:
        """Test workflow: detect and handle various types of file modifications."""
        project_dir = git_repo_with_files
        
        # Initial state should be clean
        initial_status = get_full_status(project_dir)
        assert initial_status == {"staged": [], "modified": [], "untracked": []}
        
        # Type 1: Content modification
        file1 = project_dir / "file1.txt"
        original_content = file1.read_text()
        file1.write_text(original_content + "\nAdded new line")
        
        # Type 2: Complete rewrite
        file2 = project_dir / "subdir" / "file2.py"
        file2.write_text("# Completely rewritten\nclass NewClass:\n    def new_method(self):\n        pass")
        
        # Type 3: Minor change
        file3 = project_dir / "config.json"
        file3.write_text('{"setting": "initial_value", "enabled": true, "debug": true}')
        
        # Detect all modifications
        status = get_full_status(project_dir)
        assert len(status["modified"]) == 3
        assert "file1.txt" in status["modified"]
        assert "subdir/file2.py" in status["modified"]
        assert "config.json" in status["modified"]
        assert status["staged"] == []
        assert status["untracked"] == []
        
        # Stage modifications selectively
        files_to_stage = [project_dir / "file1.txt", project_dir / "subdir" / "file2.py"]
        stage_result = stage_specific_files(files_to_stage, project_dir)
        assert stage_result is True
        
        # Verify selective staging
        status = get_full_status(project_dir)
        assert len(status["staged"]) == 2
        assert len(status["modified"]) == 1  # config.json still modified
        assert "config.json" in status["modified"]
        
        # Commit staged modifications
        commit_result = commit_staged_files("Update file1 and file2", project_dir)
        assert commit_result["success"] is True
        
        # Verify remaining modification
        status = get_full_status(project_dir)
        assert status["staged"] == []
        assert len(status["modified"]) == 1
        assert "config.json" in status["modified"]
        
        # Commit remaining modification
        commit_result2 = commit_all_changes("Update config file", project_dir)
        assert commit_result2["success"] is True
        
        # Verify final clean state
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_empty_to_populated_repository_workflow(self, git_repo: Path) -> None:
        """Test workflow: transform empty repository to populated with content."""
        project_dir = git_repo
        repo = Repo(project_dir)
        
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
            "README.md": "# Project\n\nEmpty repository to start."
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
            "tests/test_core.py": "def test_core():\n    assert True"
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
            "setup.py": "from setuptools import setup\nsetup(name='project')"
        }
        
        for path_str, content in config_files.items():
            file_path = project_dir / path_str
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)
        
        commit_result3 = commit_all_changes("Add configuration and documentation", project_dir)
        assert commit_result3["success"] is True
        
        # Verify transformation complete
        commits = list(repo.iter_commits())
        assert len(commits) == 3
        
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}
        
        # Verify all files exist
        all_files = list(basic_files.keys()) + list(src_files.keys()) + list(config_files.keys())
        for file_path_str in all_files:
            assert (project_dir / file_path_str).exists()

    def test_staged_vs_unstaged_changes_workflow(self, git_repo_with_files: Path) -> None:
        """Test workflow: manage mix of staged and unstaged changes."""
        project_dir = git_repo_with_files
        
        # Create a mix of changes
        (project_dir / "file1.txt").write_text("Modified file1 content")
        (project_dir / "config.json").write_text('{"modified": true}')
        (project_dir / "new1.py").write_text("# New file 1")
        (project_dir / "new2.py").write_text("# New file 2")
        (project_dir / "new3.py").write_text("# New file 3")
        
        # Stage some changes selectively
        files_to_stage = [project_dir / "file1.txt", project_dir / "new1.py", project_dir / "new2.py"]
        stage_result = stage_specific_files(files_to_stage, project_dir)
        assert stage_result is True
        
        # Verify mixed state
        status = get_full_status(project_dir)
        assert len(status["staged"]) == 3
        assert len(status["modified"]) == 1  # config.json
        assert len(status["untracked"]) == 1  # new3.py
        
        # Commit only staged changes
        commit_result1 = commit_staged_files("Partial commit: file1 and new files 1,2", project_dir)
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

    def test_commit_message_variations_workflow(self, git_repo: Path) -> None:
        """Test workflow: various commit message formats and lengths."""
        project_dir = git_repo
        
        # Test different commit message styles
        test_cases = [
            ("short.txt", "Short"),
            ("conventional.txt", "feat: add conventional commit style"),
            ("detailed.txt", "Add detailed commit\n\n- Feature A\n- Bug fix B"),
            ("emoji.txt", "✨ Add emoji commit message 🚀"),
            ("long.txt", "Very long commit message that exceeds typical length recommendations")
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

    def test_file_tracking_status_workflow(self, git_repo: Path) -> None:
        """Test workflow: track file status changes throughout operations."""
        project_dir = git_repo
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

    def test_directory_structure_workflow(self, git_repo: Path) -> None:
        """Test workflow: create complex directory structures and manage files."""
        project_dir = git_repo
        
        # Create complex nested structure
        structure = {
            "src/main/python/app/core/engine.py": "class Engine: pass",
            "src/test/python/test_core.py": "def test_engine(): pass",
            "docs/api/core.md": "# Core API",
            "config/dev/database.yaml": "host: localhost",
            "scripts/deploy/build.sh": "#!/bin/bash\necho build"
        }
        
        for path, content in structure.items():
            file_path = project_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Stage and commit by groups
        src_files = [project_dir / path for path in structure.keys() if path.startswith("src/")]
        stage_result1 = stage_specific_files(src_files, project_dir)
        assert stage_result1 is True
        commit_result1 = commit_staged_files("Add source code", project_dir)
        assert commit_result1["success"] is True
        
        # Commit remaining
        commit_result2 = commit_all_changes("Add docs, config, and scripts", project_dir)
        assert commit_result2["success"] is True
        
        # Verify all files exist and clean state
        for path in structure.keys():
            assert (project_dir / path).exists()
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}

    def test_git_status_consistency_workflow(self, git_repo_with_files: Path) -> None:
        """Test workflow: verify git status consistency after operations."""
        project_dir = git_repo_with_files
        
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

    def test_complete_project_lifecycle_workflow(self, git_repo: Path) -> None:
        """Test workflow: complete project from initialization to multiple commits."""
        project_dir = git_repo
        
        # Phase 1: Project initialization
        init_files = {"README.md": "# New Project", "setup.py": "from setuptools import setup\nsetup()"}
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

    def test_real_world_development_workflow(self, git_repo: Path) -> None:
        """Test workflow: simulate realistic development patterns."""
        project_dir = git_repo
        
        # Day 1: Initial app setup
        (project_dir / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
        (project_dir / "requirements.txt").write_text("flask==2.1.0")
        commit_all_changes("Initial Flask setup", project_dir)
        
        # Day 2: Add routes (partial staging)
        (project_dir / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef home(): return 'Hello'")
        (project_dir / "templates" / "home.html").parent.mkdir(exist_ok=True)
        (project_dir / "templates" / "home.html").write_text("<h1>Home</h1>")
        (project_dir / "static" / "style.css").parent.mkdir(exist_ok=True)
        (project_dir / "static" / "style.css").write_text("body { font-family: Arial; }")
        
        # Stage only ready changes
        files_to_stage = [project_dir / "app.py", project_dir / "templates" / "home.html"]
        stage_specific_files(files_to_stage, project_dir)
        commit_staged_files("Add home route and template", project_dir)
        
        # Day 3: Complete remaining work
        commit_all_changes("Add styling and finalize", project_dir)
        
        # Day 4: Add tests and docs
        (project_dir / "tests" / "test_app.py").parent.mkdir(exist_ok=True)
        (project_dir / "tests" / "test_app.py").write_text("def test_home(): assert True")
        (project_dir / "README.md").write_text("# Flask App\n\nA simple web application.")
        commit_all_changes("Add tests and documentation", project_dir)
        
        # Verify realistic development history
        repo = Repo(project_dir)
        commits = list(repo.iter_commits())
        assert len(commits) == 4
        
        final_status = get_full_status(project_dir)
        assert final_status == {"staged": [], "modified": [], "untracked": []}
        
        # Verify files exist
        expected_files = ["app.py", "requirements.txt", "templates/home.html", "static/style.css", "tests/test_app.py", "README.md"]
        for file_path_str in expected_files:
            assert (project_dir / file_path_str).exists()
