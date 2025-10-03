"""Tests for session file finding functionality."""

import json
import os
import tempfile
from typing import List

import pytest

from mcp_coder.llm.storage.session_finder import find_latest_session


class TestFindLatestSession:
    """Tests for find_latest_session function."""

    # Test constants to avoid magic strings
    VALID_TIMESTAMPS = [
        "response_2025-09-19T14-30-20.json",
        "response_2025-09-19T14-30-22.json",
        "response_2025-09-19T14-30-25.json",
    ]

    INVALID_FILES = [
        "response_abc_2025.json",
        "other_file.json",
        "response_invalid.json",
    ]

    def _create_test_files_in_temp_dir(
        self, temp_dir: str, filenames: List[str]
    ) -> None:
        """Create test response files in temporary directory."""
        for filename in filenames:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"test": "data", "filename": filename}, f)

    def test_find_latest_response_file_success(self) -> None:
        """Test successful discovery of latest response file with proper sorting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use constants and helper method
            self._create_test_files_in_temp_dir(temp_dir, self.VALID_TIMESTAMPS)

            # Call the function
            result = find_latest_session(temp_dir)

            # Verify it returns the latest file
            expected_path = os.path.join(temp_dir, "response_2025-09-19T14-30-25.json")
            assert result == expected_path
            assert os.path.exists(result)

    def test_find_latest_response_file_edge_cases(self) -> None:
        """Test edge cases: no directory, no files, mixed file types."""
        # Test 1: Non-existent directory
        non_existent_dir = "/path/that/does/not/exist"
        result = find_latest_session(non_existent_dir)
        assert result is None

        # Test 2: Empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            result = find_latest_session(temp_dir)
            assert result is None

        # Test 3: Directory with no valid response files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some non-response files
            invalid_files = [
                "other_file.json",
                "response_invalid.json",
                "not_a_response.txt",
                "readme.md",
            ]

            for filename in invalid_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("test content")

            result = find_latest_session(temp_dir)
            assert result is None

    def test_find_latest_response_file_mixed_valid_invalid(self) -> None:
        """Test file discovery ignores invalid files and selects latest valid file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use constants and helper method
            test_files = self.VALID_TIMESTAMPS + self.INVALID_FILES
            self._create_test_files_in_temp_dir(temp_dir, test_files)

            # Call the function
            result = find_latest_session(temp_dir)

            # Verify it returns only the latest VALID file
            expected_path = os.path.join(temp_dir, "response_2025-09-19T14-30-25.json")
            assert result == expected_path

            # Verify the file exists and contains expected data
            assert os.path.exists(result)
            with open(result, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["filename"] == "response_2025-09-19T14-30-25.json"

    def test_find_latest_response_file_invalid_datetime_values(self) -> None:
        """Test strict validation rejects files with invalid date/time values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with invalid date/time values but correct format
            invalid_files = [
                "response_2025-13-45T99-99-99.json",  # Invalid month, day, hour, minute, second
                "response_2025-00-01T12-00-00.json",  # Invalid month (0)
                "response_2025-12-32T12-00-00.json",  # Invalid day (32)
                "response_2025-12-01T25-00-00.json",  # Invalid hour (25)
                "response_2025-12-01T12-61-00.json",  # Invalid minute (61)
                "response_2025-12-01T12-00-61.json",  # Invalid second (61)
            ]

            for filename in invalid_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"test": "data"}, f)

            # Should return None when all files have invalid date/time values
            result = find_latest_session(temp_dir)
            assert result is None

    def test_find_latest_response_file_only_invalid_files_remain(self) -> None:
        """Test behavior when valid files are removed leaving only invalid ones."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First create both valid and invalid files
            all_files = [
                "response_2025-09-19T14-30-22.json",  # Valid
                "response_2025-09-19T14-30-25.json",  # Valid
                "response_abc_2025.json",  # Invalid format
                "other_file.json",  # Not a response file
            ]

            for filename in all_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"test": "data"}, f)

            # Verify it initially finds valid files
            result = find_latest_session(temp_dir)
            assert result is not None
            assert "response_2025-09-19T14-30-25.json" in result

            # Remove all valid files
            for filename in [
                "response_2025-09-19T14-30-22.json",
                "response_2025-09-19T14-30-25.json",
            ]:
                os.remove(os.path.join(temp_dir, filename))

            # Should return None when only invalid files remain
            result = find_latest_session(temp_dir)
            assert result is None

    def test_find_latest_response_file_lexicographic_sorting(self) -> None:
        """Test that files are sorted lexicographically to find the latest timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files in non-chronological order to test sorting
            test_files = [
                "response_2025-09-20T10-00-00.json",  # Later date
                "response_2025-09-19T23-59-59.json",  # Earlier date, later time
                "response_2025-09-20T09-59-59.json",  # Later date, earlier time
                "response_2025-09-20T10-00-01.json",  # Latest overall (expected result)
            ]

            for filename in test_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"filename": filename}, f)

            # Call the function
            result = find_latest_session(temp_dir)

            # Verify it returns the lexicographically latest file
            expected_path = os.path.join(temp_dir, "response_2025-09-20T10-00-01.json")
            assert result == expected_path

            # Verify the file contains expected data
            with open(result, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["filename"] == "response_2025-09-20T10-00-01.json"

    def test_find_latest_response_file_user_feedback_message(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that user feedback message shows correct count and filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use constants and helper method
            self._create_test_files_in_temp_dir(temp_dir, self.VALID_TIMESTAMPS)

            # Call the function
            result = find_latest_session(temp_dir)

            # Verify return value
            assert result is not None
            assert "response_2025-09-19T14-30-25.json" in result

            # Verify user feedback message
            captured = capsys.readouterr()
            captured_out = captured.out or ""
            assert (
                "Found 3 previous sessions, continuing from: response_2025-09-19T14-30-25.json"
                in captured_out
            )
