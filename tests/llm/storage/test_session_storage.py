"""Tests for session storage functionality."""

import json
import os
import tempfile
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.llm.storage.session_storage import extract_session_id, store_session
from mcp_coder.llm.types import LLMResponseDict


class TestStoreSession:
    """Tests for store_session function."""

    def test_store_session_creates_file(self) -> None:
        """Test that store_session creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "Hello",
                "session_id": "test-123",
                "method": "cli",
                "provider": "claude",
                "raw_response": {"session_info": {"model": "claude"}},
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

    def test_store_session_with_llm_response_dict(self) -> None:
        """Test store_session with a proper LLMResponseDict."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00.000000",
                "text": "Hello from LLM",
                "session_id": "llm-session-abc",
                "method": "cli",
                "provider": "claude",
                "raw_response": {"session_info": {"model": "claude-sonnet-4"}},
            }

            file_path = store_session(response_data, "Test prompt", tmp_path)

            with open(file_path, "r") as f:
                data = json.load(f)
            assert data["prompt"] == "Test prompt"
            assert data["response_data"] == response_data
            assert "metadata" in data

    def test_store_session_step_name_filename_format(self) -> None:
        """Test filename format when step_name is provided."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "",
                "session_id": None,
                "method": "cli",
                "provider": "claude",
                "raw_response": {},
            }

            file_path = store_session(
                response_data, "prompt", tmp_path, step_name="step_1"
            )

            filename = os.path.basename(file_path)
            assert filename.endswith("_step_1.json")
            assert not filename.startswith("response_")

    def test_store_session_no_step_name_legacy_format(self) -> None:
        """Test filename format when step_name is not provided."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "",
                "session_id": None,
                "method": "cli",
                "provider": "claude",
                "raw_response": {},
            }

            file_path = store_session(response_data, "prompt", tmp_path)

            filename = os.path.basename(file_path)
            assert filename.startswith("response_")
            assert filename.endswith(".json")

    def test_store_session_branch_name_in_metadata(self) -> None:
        """Test that branch_name appears in metadata when provided."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "",
                "session_id": None,
                "method": "cli",
                "provider": "claude",
                "raw_response": {},
            }

            file_path = store_session(
                response_data, "prompt", tmp_path, branch_name="342-improve-logging"
            )

            with open(file_path, "r") as f:
                data = json.load(f)
            assert data["metadata"]["branch_name"] == "342-improve-logging"

    def test_store_session_step_name_in_metadata(self) -> None:
        """Test that step_name appears in metadata when provided."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "",
                "session_id": None,
                "method": "cli",
                "provider": "claude",
                "raw_response": {},
            }

            file_path = store_session(
                response_data, "prompt", tmp_path, step_name="step_1"
            )

            with open(file_path, "r") as f:
                data = json.load(f)
            assert data["metadata"]["step_name"] == "step_1"

    def test_store_session_model_from_raw_response(self) -> None:
        """Test model extraction from raw_response.session_info.model (LLMResponseDict format)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "response",
                "session_id": "abc",
                "method": "cli",
                "provider": "claude",
                "raw_response": {"session_info": {"model": "claude-sonnet-4-new"}},
            }

            file_path = store_session(response_data, "prompt", tmp_path)

            with open(file_path, "r") as f:
                data = json.load(f)
            assert data["metadata"]["model"] == "claude-sonnet-4-new"

    def test_store_session_model_fallback_to_provider(self) -> None:
        """Test model falls back to provider field when no session_info.model."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "response",
                "session_id": "abc",
                "method": "cli",
                "provider": "claude-fallback",
                "raw_response": {},
            }

            file_path = store_session(response_data, "prompt", tmp_path)

            with open(file_path, "r") as f:
                data = json.load(f)
            assert data["metadata"]["model"] == "claude-fallback"

    def test_store_session_no_branch_name_not_in_metadata(self) -> None:
        """Test that branch_name key is absent from metadata when not provided."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "",
                "session_id": None,
                "method": "cli",
                "provider": "claude",
                "raw_response": {},
            }

            file_path = store_session(response_data, "prompt", tmp_path)

            with open(file_path, "r") as f:
                data = json.load(f)
            assert "branch_name" not in data["metadata"]

    def test_store_session_no_step_name_not_in_metadata(self) -> None:
        """Test that step_name key is absent from metadata when not provided."""
        with tempfile.TemporaryDirectory() as tmp_path:
            response_data: LLMResponseDict = {
                "version": "1.0",
                "timestamp": "2025-10-02T14:30:00",
                "text": "",
                "session_id": None,
                "method": "cli",
                "provider": "claude",
                "raw_response": {},
            }

            file_path = store_session(response_data, "prompt", tmp_path)

            with open(file_path, "r") as f:
                data = json.load(f)
            assert "step_name" not in data["metadata"]


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

    def test_extract_session_id_from_llm_response_dict_format(self) -> None:
        """Test extracting session_id from LLMResponseDict format (response_data.session_id)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            session_data = {
                "prompt": "Test",
                "response_data": {
                    "version": "1.0",
                    "timestamp": "2025-10-02T14:30:00",
                    "text": "response text",
                    "session_id": "llm-dict-session-xyz",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                },
            }

            file_path = os.path.join(tmp_path, "llm_response.json")
            with open(file_path, "w") as f:
                json.dump(session_data, f)

            session_id = extract_session_id(str(file_path))
            assert session_id == "llm-dict-session-xyz"
