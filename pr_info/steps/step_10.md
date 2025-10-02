# Step 10: Extract Storage/Session Tests

## Objective
Extract storage and session tests from `test_prompt.py` to dedicated test files, completing the test reorganization to mirror code structure.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 9 extracted formatting tests, all tests passing
- **Current State**: Storage/session tests in `test_prompt.py`
- **Target State**: Tests organized under `tests/llm/storage/` and `tests/llm/session/`

## Files to Create

```
tests/llm/storage/test_session_storage.py  (NEW - extract from test_prompt.py)
tests/llm/storage/test_session_finder.py   (NEW - extract from test_prompt.py)
tests/llm/session/test_resolver.py         (NEW - extract from test_prompt.py)
```

## Files to Modify

```
tests/cli/commands/test_prompt.py          (Remove extracted tests, slim down)
```

## Implementation

### WHERE
- Extract from: `tests/cli/commands/test_prompt.py`
- Create: `tests/llm/storage/test_session_storage.py`
- Create: `tests/llm/storage/test_session_finder.py`
- Create: `tests/llm/session/test_resolver.py`

### WHAT

**Tests to Extract to `test_session_storage.py` (~80 lines):**
1. `test_store_response()` - Test session storage
2. Tests for session ID extraction

**Tests to Extract to `test_session_finder.py` (~180 lines):**
1. `test_find_latest_response_file_success()` - Test finding latest
2. `test_find_latest_response_file_edge_cases()` - Edge cases
3. `test_find_latest_response_file_mixed_valid_invalid()` - Validation
4. `test_find_latest_response_file_invalid_datetime_values()` - Date validation
5. `test_find_latest_response_file_only_invalid_files_remain()` - Filtering
6. `test_find_latest_response_file_lexicographic_sorting()` - Sorting
7. `test_find_latest_response_file_user_feedback_message()` - User feedback

**Tests to Extract to `test_resolver.py` (~140 lines):**
1. `test_continue_from_success()` - Session continuation
2. `test_continue_from_file_not_found()` - Error handling
3. `test_continue_from_invalid_json()` - Error handling
4. `test_continue_from_missing_required_fields()` - Validation
5. Tests for `parse_llm_method()` if any exist

### HOW

**Step 10.1: Create `test_session_storage.py`**

```python
"""Tests for session storage functionality."""

import json
import os
import tempfile
from unittest.mock import Mock, mock_open, patch
from typing import Dict, Any

import pytest

from mcp_coder.llm.storage.session_storage import (
    store_session,
    extract_session_id,
)


class TestStoreSession:
    """Tests for store_session function."""
    
    def test_store_session_creates_file(self, tmp_path):
        """Test that store_session creates a JSON file."""
        response_data = {
            "text": "Hello",
            "session_info": {"session_id": "test-123", "model": "claude"},
            "result_info": {}
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
    
    def test_store_session_default_path(self):
        """Test store_session with default path."""
        # Extract and adapt test_store_response() from test_prompt.py
        pass


class TestExtractSessionId:
    """Tests for extract_session_id function."""
    
    def test_extract_session_id_from_detailed_response(self, tmp_path):
        """Test extracting session ID from detailed API response format."""
        session_data = {
            "prompt": "Test",
            "response_data": {
                "session_info": {"session_id": "extracted-id-123"}
            }
        }
        
        file_path = tmp_path / "test_session.json"
        with open(file_path, "w") as f:
            json.dump(session_data, f)
        
        session_id = extract_session_id(str(file_path))
        assert session_id == "extracted-id-123"
    
    def test_extract_session_id_file_not_found(self):
        """Test graceful handling when file doesn't exist."""
        session_id = extract_session_id("/nonexistent/file.json")
        assert session_id is None
    
    def test_extract_session_id_invalid_json(self, tmp_path):
        """Test graceful handling of invalid JSON."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, "w") as f:
            f.write("{ invalid json }")
        
        session_id = extract_session_id(str(file_path))
        assert session_id is None
```

**Step 10.2: Create `test_session_finder.py`**

```python
"""Tests for session file finding functionality."""

import json
import os
import tempfile
from typing import List

import pytest

from mcp_coder.llm.storage.session_finder import find_latest_session


class TestFindLatestSession:
    """Tests for find_latest_session function."""
    
    @pytest.fixture
    def sample_sessions(self, tmp_path) -> tuple[str, List[str]]:
        """Create sample session files for testing."""
        session_dir = tmp_path / "responses"
        session_dir.mkdir()
        
        # Create valid timestamp files
        valid_files = [
            "response_2025-09-19T14-30-20.json",
            "response_2025-09-19T14-30-22.json",
            "response_2025-09-19T14-30-25.json",  # Latest
        ]
        
        for filename in valid_files:
            file_path = session_dir / filename
            with open(file_path, "w") as f:
                json.dump({"test": "data", "filename": filename}, f)
        
        return str(session_dir), valid_files
    
    def test_find_latest_success(self, sample_sessions):
        """Test finding latest session file with proper sorting."""
        session_dir, valid_files = sample_sessions
        
        result = find_latest_session(session_dir)
        
        # Should return the latest file
        assert result is not None
        assert "response_2025-09-19T14-30-25.json" in result
    
    # ... (additional test methods as shown in full implementation)
```

**Step 10.3: Create `test_resolver.py`**

```python
"""Tests for session resolution and LLM method parsing."""

import json
from unittest.mock import Mock, mock_open, patch
from typing import Dict, Any

import pytest

from mcp_coder.llm.session.resolver import parse_llm_method


class TestParseLlmMethod:
    """Tests for parse_llm_method function."""
    
    def test_parse_claude_code_cli(self):
        """Test parsing 'claude_code_cli' method."""
        provider, method = parse_llm_method("claude_code_cli")
        assert provider == "claude"
        assert method == "cli"
    
    def test_parse_claude_code_api(self):
        """Test parsing 'claude_code_api' method."""
        provider, method = parse_llm_method("claude_code_api")
        assert provider == "claude"
        assert method == "api"
    
    def test_parse_invalid_method(self):
        """Test error handling for unsupported method."""
        with pytest.raises(ValueError, match="Unsupported llm_method"):
            parse_llm_method("invalid_method")
```

**Step 10.4: Remove Tests from `test_prompt.py`**

Remove all extracted tests, keeping only CLI orchestration tests (~200 lines):
- `test_basic_prompt_success()`
- `test_prompt_api_error()`
- Tests that verify CLI argument parsing
- Tests that verify CLI output printing
- Integration tests of CLI flow (not business logic)

### ALGORITHM
```
1. Create test_session_storage.py with storage tests
2. Create test_session_finder.py with file finding tests
3. Create test_resolver.py with parse_llm_method tests
4. Extract relevant tests from test_prompt.py
5. Adapt tests to call functions directly (not via CLI)
6. Remove extracted tests from test_prompt.py
7. Run storage tests
8. Run session tests
9. Run slim prompt tests
10. Run full test suite
```

### DATA

**Test Organization:**
```python
{
    "test_session_storage.py": ["store_session", "extract_session_id"],  # ~80 lines
    "test_session_finder.py": ["find_latest_session"],  # ~180 lines
    "test_resolver.py": ["parse_llm_method"],  # ~140 lines
    "test_prompt.py": ["CLI orchestration only"],  # ~200 lines remaining
}
```

**Test Count Reduction:**
```
test_prompt.py: ~800 lines → ~200 lines (75% reduction)
Total extracted to llm/: ~400 lines (80 + 180 + 140)
```

## Testing

### Test Strategy (TDD)

**Test 10.1: Run Storage Tests**

```bash
pytest tests/llm/storage/test_session_storage.py -v
pytest tests/llm/storage/test_session_finder.py -v
pytest tests/llm/storage/ -v
```

**Test 10.2: Run Session Tests**

```bash
pytest tests/llm/session/test_resolver.py -v
pytest tests/llm/session/ -v
```

**Test 10.3: Run Slim Prompt Tests**

```bash
# Should be much faster now (only ~200 lines of CLI tests)
pytest tests/cli/commands/test_prompt.py -v
```

**Test 10.4: Run All LLM Tests**

```bash
pytest tests/llm/ -v
```

**Test 10.5: Run Full Test Suite**

```bash
pytest tests/ -v
```

### Expected Results
- Storage tests pass independently
- Session tests pass independently
- `test_prompt.py` reduced to ~200 lines, still passes
- All LLM tests organized under `tests/llm/`
- Test structure perfectly mirrors code structure
- Full test suite passes

## Verification Checklist
- [ ] `test_session_storage.py` created with storage tests
- [ ] `test_session_finder.py` created with finder tests
- [ ] `test_resolver.py` created with resolver tests
- [ ] Tests adapted to call functions directly
- [ ] Extracted tests removed from `test_prompt.py`
- [ ] `test_prompt.py` reduced to ~200 lines (CLI only)
- [ ] Storage tests pass
- [ ] Session tests pass
- [ ] Prompt tests pass (slimmed down)
- [ ] Full test suite passes
- [ ] Test structure mirrors code structure
- [ ] Create `tests/llm/storage/conftest.py` only if shared fixtures are needed
- [ ] Create `tests/llm/session/conftest.py` only if shared fixtures are needed

## LLM Prompt for Implementation

```
I'm implementing Step 10 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Extract storage and session tests from test_prompt.py to dedicated test files.

Please:
1. Create tests/llm/storage/test_session_storage.py
   - Extract: test_store_response and session ID extraction tests
   - Import from mcp_coder.llm.storage.session_storage

2. Create tests/llm/storage/test_session_finder.py
   - Extract: all test_find_latest_response_file_* tests
   - Import from mcp_coder.llm.storage.session_finder

3. Create tests/llm/session/test_resolver.py
   - Add: tests for parse_llm_method()
   - Extract: session continuation/resolution tests if applicable
   - Import from mcp_coder.llm.session.resolver

4. Slim down test_prompt.py to ~200 lines:
   - Keep only: CLI orchestration, argument parsing, output tests
   - Remove: All extracted tests

5. Run tests:
   - pytest tests/llm/storage/ -v
   - pytest tests/llm/session/ -v
   - pytest tests/cli/commands/test_prompt.py -v
   - pytest tests/ -v

This completes the test reorganization to mirror code structure.
```

## Next Step
After this step completes successfully, proceed to **Step 11: Final Verification & Cleanup**.
