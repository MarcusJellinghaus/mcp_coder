"""Tests for session storage functionality."""

import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.llm.storage.session_storage import extract_session_id, store_session


class TestStoreSession:
    """Tests for store_session function."""

    def test_store_session_creates_file(self) -> None:
        """Test that store_session creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data = {
                "text": "Hello",
                "session_info": {"session_id": "test-123", "model": "claude"},
                "result_info": {},
            }

            store_path = str(tmp_path)
            file_path = store_session(response_data, "Test prompt", store_path)

            # Verify file created
            assert os.path.exists(file_path)
            assert file_path.startswith(store_path)
            assert file_path.endswith(".json")

            # Verify content
            with open(file_path, "r") as f:
                data = json.load(f)
                assert data["prompt"] == "Test prompt"
                assert data["response_data"]["text"] == "Hello"


class TestExtractSessionId:
    """Tests for extract_session_id function."""

    def test_extract_session_id_from_detailed_response(self) -> None:
        """Test extracting session ID from detailed API response format."""
        with tempfile.TemporaryDirectory() as tmp_path:
            session_data = {
                "prompt": "Test",
                "response_data": {"session_info": {"session_id": "extracted-id-123"}},
            }

            file_path = os.path.join(tmp_path, "test_session.json")
            with open(file_path, "w") as f:
                json.dump(session_data, f)

            session_id = extract_session_id(str(file_path))
            assert session_id == "extracted-id-123"

    def test_extract_session_id_file_not_found(self) -> None:
        """Test graceful handling when file doesn't exist."""
        session_id = extract_session_id("/nonexistent/file.json")
        assert session_id is None

    def test_extract_session_id_invalid_json(self) -> None:
        """Test graceful handling of invalid JSON."""
        with tempfile.TemporaryDirectory() as tmp_path:
            file_path = os.path.join(tmp_path, "invalid.json")
            with open(file_path, "w") as f:
                f.write("{ invalid json }")

            session_id = extract_session_id(str(file_path))
            assert session_id is None

    def test_extract_session_id_missing_session_info(self) -> None:
        """Test graceful handling when session_info is missing."""
        with tempfile.TemporaryDirectory() as tmp_path:
            session_data = {
                "prompt": "Test",
                "response_data": {"text": "Response without session info"},
            }

            file_path = os.path.join(tmp_path, "no_session.json")
            with open(file_path, "w") as f:
                json.dump(session_data, f)

            session_id = extract_session_id(str(file_path))
            assert session_id is None
