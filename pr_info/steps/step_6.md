# Step 6: Extract Storage Functions

## Objective
Extract session storage functions from `prompt.py` to `llm/storage/` module. This includes both session storage and session ID extraction functionality.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 5 extracted formatters, all tests passing
- **Current State**: Storage functions are private functions in `prompt.py`
- **Target State**: Storage functions are public in `llm/storage/` modules

## Files to Create

```
src/mcp_coder/llm/storage/session_storage.py  (NEW)
src/mcp_coder/llm/storage/session_finder.py   (NEW)
```

## Files to Modify

```
src/mcp_coder/cli/commands/prompt.py           (Extract functions, update imports)
src/mcp_coder/llm/storage/__init__.py          (Export functions)
```

## Implementation

### WHERE
- Extract from: `src/mcp_coder/cli/commands/prompt.py`
- Create: `src/mcp_coder/llm/storage/session_storage.py`
- Create: `src/mcp_coder/llm/storage/session_finder.py`
- Update: `src/mcp_coder/llm/storage/__init__.py`

### WHAT

**Functions to Extract:**

**From `session_storage.py` (2 functions):**
1. `_store_response(response_data, prompt, store_path) -> str` → `store_session(response_data, prompt, store_path) -> str`
2. `_extract_session_id_from_file(file_path) -> Optional[str]` → `extract_session_id(file_path) -> Optional[str]`

**From `session_finder.py` (1 function):**
1. `_find_latest_response_file(responses_dir) -> Optional[str]` → `find_latest_session(responses_dir) -> Optional[str]`

**Signature Changes:**
- Remove leading underscore (make public)
- Rename for clarity
- Keep all parameters and return types identical

### HOW

**Step 6.1: Create `session_storage.py`**

```python
"""Session storage and retrieval functionality.

This module provides functions for storing and loading LLM session data
to/from the filesystem for conversation continuity.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

__all__ = [
    "store_session",
    "extract_session_id",
]


def store_session(
    response_data: Dict[str, Any], 
    prompt: str, 
    store_path: Optional[str] = None
) -> str:
    """Store complete session data to .mcp-coder/responses/ directory.
    
    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync
        prompt: Original user prompt
        store_path: Optional custom path for storage directory
    
    Returns:
        File path of stored session for potential user reference
    
    Example:
        >>> data = {"text": "Hello", "session_info": {"session_id": "abc"}}
        >>> path = store_session(data, "What is Python?")
        >>> print(path)
        .mcp-coder/responses/response_2025-10-02T14-30-00.json
    """
    # Determine storage directory
    if store_path is None:
        storage_dir = ".mcp-coder/responses"
    else:
        storage_dir = store_path
    
    # Create storage directory if it doesn't exist
    os.makedirs(storage_dir, exist_ok=True)
    
    # Generate timestamp-based filename
    timestamp = datetime.now().isoformat().replace(":", "-").split(".")[0]
    filename = f"response_{timestamp}.json"
    file_path = os.path.join(storage_dir, filename)
    
    # Create complete session JSON structure
    session_data = {
        "prompt": prompt,
        "response_data": response_data,
        "metadata": {
            "timestamp": datetime.now().isoformat() + "Z",
            "working_directory": os.getcwd(),
            "model": response_data.get("session_info", {}).get(
                "model", "claude-3-5-sonnet"
            ),
        },
    }
    
    # Write JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, default=str)
    
    return file_path


def extract_session_id(file_path: str) -> Optional[str]:
    """Extract session_id from a stored response file.
    
    Args:
        file_path: Path to the stored session JSON file
    
    Returns:
        Session ID string if found, None otherwise
    
    Example:
        >>> session_id = extract_session_id(".mcp-coder/responses/response_123.json")
        >>> print(session_id)
        '550e8400-e29b-41d4-a716-446655440000'
    """
    logger.info("Extracting session_id from: %s", file_path)
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning("Response file not found: %s", file_path)
            return None
        
        # Read and parse JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        
        # Try multiple paths to find session_id
        # Path 1: response_data.session_info.session_id (detailed API response)
        session_id: Optional[str] = (
            session_data.get("response_data", {})
            .get("session_info", {})
            .get("session_id")
        )
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id in response_data.session_info: %s", session_id)
            return session_id
        
        # Path 2: Direct session_id field (simple response format)
        session_id = session_data.get("session_id")
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id at root level: %s", session_id)
            return session_id
        
        # Path 3: metadata.session_id (alternative storage location)
        session_id = session_data.get("metadata", {}).get("session_id")
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id in metadata: %s", session_id)
            return session_id
        
        logger.warning("No session_id found in file: %s", file_path)
        return None
    
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in file %s: %s", file_path, e)
        return None
    except Exception as e:
        logger.error("Error reading session file %s: %s", file_path, e)
        return None
```

**Step 6.2: Create `session_finder.py`**

```python
"""Session file discovery and retrieval functionality.

This module provides functions for finding session files on the filesystem,
particularly for identifying the most recent session for continuation.
"""

import glob
import logging
import os
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "find_latest_session",
]


def find_latest_session(
    responses_dir: str = ".mcp-coder/responses",
) -> Optional[str]:
    """Find the most recent response file by filename timestamp with strict validation.
    
    Args:
        responses_dir: Directory containing response files
    
    Returns:
        Path to latest response file, or None if none found
    
    Example:
        >>> path = find_latest_session()
        >>> print(path)
        .mcp-coder/responses/response_2025-10-02T14-30-00.json
    """
    logger.debug("Searching for response files in: %s", responses_dir)
    
    # Check if responses directory exists
    if not os.path.exists(responses_dir):
        logger.debug("Responses directory does not exist: %s", responses_dir)
        return None
    
    try:
        # Use glob to find response files with the expected pattern
        pattern = os.path.join(responses_dir, "response_*.json")
        response_files = glob.glob(pattern)
        
        if not response_files:
            logger.debug("No response files found in: %s", responses_dir)
            return None
        
        # ISO timestamp pattern: response_YYYY-MM-DDTHH-MM-SS.json
        timestamp_pattern = r"^response_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})\.json$"
        
        # Validate each file matches strict ISO timestamp pattern
        valid_files = []
        for file_path in response_files:
            filename = os.path.basename(file_path)
            match = re.match(timestamp_pattern, filename)
            if match:
                timestamp_str = match.group(1)  # Extract the timestamp part
                try:
                    # Use datetime.strptime for robust validation
                    datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
                    valid_files.append(file_path)
                except ValueError:
                    logger.debug("Invalid timestamp in filename: %s", filename)
            else:
                logger.debug("Skipping invalid filename format: %s", filename)
        
        if not valid_files:
            logger.debug("No valid response files found with ISO timestamp format")
            return None
        
        # Sort validated filenames by timestamp (lexicographic sort works for ISO format)
        valid_files.sort()
        latest_file = valid_files[-1]  # Last file after sorting is the latest
        
        # Provide user feedback showing count and selected file
        num_sessions = len(valid_files)
        selected_filename = os.path.basename(latest_file)
        print(
            f"Found {num_sessions} previous sessions, continuing from: {selected_filename}"
        )
        
        logger.debug("Selected latest response file: %s", latest_file)
        return latest_file
    
    except (OSError, IOError) as e:
        logger.debug("Error accessing response directory %s: %s", responses_dir, e)
        return None
    except Exception as e:
        logger.debug("Unexpected error finding response files: %s", e)
        return None
```

**Step 6.3: Update `llm/storage/__init__.py`**

```python
"""Session storage and retrieval functionality."""

from .session_finder import find_latest_session
from .session_storage import extract_session_id, store_session

__all__ = [
    "store_session",
    "extract_session_id",
    "find_latest_session",
]
```

**Step 6.4: Update `prompt.py`**

```python
# Remove the 3 private functions
# Add import at top of file:
from ...llm.storage import (
    extract_session_id,
    find_latest_session,
    store_session,
)

# Update function calls in execute_prompt():
# _store_response() → store_session()
# _extract_session_id_from_file() → extract_session_id()
# _find_latest_response_file() → find_latest_session()
```

### ALGORITHM
```
1. Create llm/storage/session_storage.py with 2 functions
2. Create llm/storage/session_finder.py with 1 function
3. Copy implementations from prompt.py (rename, remove underscores)
4. Update llm/storage/__init__.py exports
5. Update prompt.py: add import, remove functions
6. Update function calls in execute_prompt()
7. Run tests to verify storage behavior unchanged
```

### DATA

**Functions Mapping:**
```python
{
    "_store_response": "store_session",
    "_extract_session_id_from_file": "extract_session_id",
    "_find_latest_response_file": "find_latest_session",
}
```

**Storage File Format (unchanged):**
```json
{
    "prompt": "User question",
    "response_data": {
        "text": "Response text",
        "session_info": {"session_id": "abc-123"},
        "result_info": {}
    },
    "metadata": {
        "timestamp": "2025-10-02T14:30:00Z",
        "working_directory": "/path/to/project",
        "model": "claude-sonnet-4"
    }
}
```

## Testing

### Test Strategy (TDD)

**Test 6.1: Storage Tests**

Tests exist in `test_prompt.py` but will be moved in Step 10.
For now, verify they pass:

```bash
pytest tests/cli/commands/test_prompt.py::TestExecutePrompt::test_store_response -v
pytest tests/cli/commands/test_prompt.py::TestExecutePrompt::test_continue_from_success -v
```

**Test 6.2: Finder Tests**

```bash
pytest tests/cli/commands/test_prompt.py -k "find_latest" -v
```

**Test 6.3: Verify Imports**

```python
def test_storage_imports():
    """Verify storage functions importable from new location."""
    from mcp_coder.llm.storage import (
        store_session,
        extract_session_id,
        find_latest_session,
    )
    
    assert callable(store_session)
    assert callable(extract_session_id)
    assert callable(find_latest_session)
```

**Test 6.4: Run Full Test Suite**

```bash
pytest tests/cli/commands/test_prompt.py -v
pytest tests/ -v
```

### Expected Results
- Storage functions work in new location
- Session storage/retrieval behavior unchanged
- File finding logic unchanged
- All existing tests pass

## Verification Checklist
- [ ] `session_storage.py` created with 2 functions
- [ ] `session_finder.py` created with 1 function
- [ ] Functions made public and renamed
- [ ] All docstrings preserved/enhanced
- [ ] `llm/storage/__init__.py` exports functions
- [ ] `prompt.py` imports from new location
- [ ] All function calls updated
- [ ] Private storage functions removed from `prompt.py`
- [ ] Storage tests pass
- [ ] Finder tests pass
- [ ] Full test suite passes
- [ ] Line count of `prompt.py` reduced further

## LLM Prompt for Implementation

```
I'm implementing Step 6 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Extract storage functions from prompt.py to llm/storage/ modules.

Please:
1. Create llm/storage/session_storage.py with 2 functions:
   - _store_response → store_session
   - _extract_session_id_from_file → extract_session_id

2. Create llm/storage/session_finder.py with 1 function:
   - _find_latest_response_file → find_latest_session

3. Copy complete implementations from prompt.py (no logic changes)

4. Update llm/storage/__init__.py to export all 3 functions

5. Update prompt.py:
   - Add import from llm.storage
   - Remove the 3 private storage functions
   - Update all function calls

6. Run tests:
   - pytest tests/cli/commands/test_prompt.py -k "store_response or continue_from or find_latest" -v
   - pytest tests/ -v

This extracts storage logic - behavior must be identical.
```

## Next Step
After this step completes successfully, proceed to **Step 7: Extract Session Logic**.
