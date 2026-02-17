# Step 1 – Extend `store_session()` and `extract_session_id()`

## Context
See `pr_info/steps/summary.md` for the full picture.

`store_session()` currently accepts a manually-constructed dict with `session_info`/`result_info` keys.
The goal is to accept an `LLMResponseDict` directly (same top-level wrapper structure, just different `response_data` content), add `step_name` and `branch_name` optional params, and update the filename format when `step_name` is provided.
`extract_session_id()` needs a new lookup path to find `session_id` in the new `LLMResponseDict` shape.

This step is purely additive — no callers are changed yet. Existing callers keep working because the stored outer structure (`{ prompt, response_data, metadata }`) is unchanged.

---

## WHERE

- **Modify**: `src/mcp_coder/llm/storage/session_storage.py`
- **Modify**: `tests/llm/storage/test_session_storage.py`

---

## WHAT

### `store_session()` — updated signature

```python
def store_session(
    response_data: LLMResponseDict,
    prompt: str,
    store_path: Optional[str] = None,
    step_name: Optional[str] = None,    # NEW
    branch_name: Optional[str] = None,  # NEW
) -> str:
```

**Filename logic:**
- `step_name` provided → `2025-10-02T14-30-00_step_1.json`  (datetime first, then step name)
- `step_name` absent  → `response_2025-10-02T14-30-00.json` (existing format — create_plan sessions unaffected)

**Model name extraction** for `metadata.model`:
```python
model = response_data["raw_response"].get("session_info", {}).get("model") or response_data["provider"]
```
This tries the specific model string first (API calls), falls back to provider name (e.g. `"claude"`) for CLI calls.

**Metadata block additions:**
```json
{
  "metadata": {
    "timestamp": "...",
    "working_directory": "...",
    "model": "claude-sonnet-4",
    "branch_name": "342-improve-logging",
    "step_name": "step_1"
  }
}
```
`branch_name` and `step_name` keys are only added when their values are not `None`.

### `extract_session_id()` — new lookup path

Add **Path 4** after the existing three lookup paths:
```python
# Path 4: response_data.session_id (LLMResponseDict format)
session_id = session_data.get("response_data", {}).get("session_id")
```

---

## HOW

**Imports to add** in `session_storage.py`:
```python
from ..types import LLMResponseDict
```

---

## ALGORITHM

```
store_session(response_data, prompt, store_path, step_name, branch_name):
    storage_dir = store_path or ".mcp-coder/responses"
    os.makedirs(storage_dir, exist_ok=True)
    timestamp = now().isoformat().replace(":", "-").split(".")[0]
    filename = f"{timestamp}_{step_name}.json" if step_name else f"response_{timestamp}.json"
    model = response_data["raw_response"].get("session_info", {}).get("model") or response_data["provider"]
    metadata = {"timestamp": ..., "working_directory": ..., "model": model}
    if branch_name: metadata["branch_name"] = branch_name
    if step_name: metadata["step_name"] = step_name
    write { "prompt": prompt, "response_data": response_data, "metadata": metadata } to file
    return file_path
```

---

## DATA

**Input** `response_data`: `LLMResponseDict` with keys: `version`, `timestamp`, `text`, `session_id`, `method`, `provider`, `raw_response`

**Output**: `str` — absolute or relative path to the written JSON file

**Stored JSON structure** (outer wrapper unchanged):
```json
{
  "prompt": "...",
  "response_data": {
    "version": "1.0",
    "timestamp": "...",
    "text": "...",
    "session_id": "abc123",
    "method": "cli",
    "provider": "claude",
    "raw_response": { ... }
  },
  "metadata": {
    "timestamp": "...",
    "working_directory": "...",
    "model": "claude-sonnet-4",
    "branch_name": "342-improve-logging",
    "step_name": "step_1"
  }
}
```

---

## TESTS

**File**: `tests/llm/storage/test_session_storage.py`

New test cases to add (TDD — write tests first):

### `TestStoreSession` additions
- `test_store_session_with_llm_response_dict` — pass a proper `LLMResponseDict`, verify outer structure and that `response_data` is stored as-is
- `test_store_session_step_name_filename_format` — with `step_name="step_1"`, verify filename matches `*_step_1.json` pattern
- `test_store_session_no_step_name_legacy_format` — without `step_name`, verify filename matches `response_*.json` pattern
- `test_store_session_branch_name_in_metadata` — verify `branch_name` appears in `metadata`
- `test_store_session_step_name_in_metadata` — verify `step_name` appears in `metadata`
- `test_store_session_model_from_raw_response` — `raw_response` contains `session_info.model` → used in metadata
- `test_store_session_model_fallback_to_provider` — no `session_info.model` → falls back to `provider` field
- `test_store_session_no_branch_name_not_in_metadata` — when `branch_name=None`, key absent from metadata
- `test_store_session_no_step_name_not_in_metadata` — when `step_name=None`, key absent from metadata

### `TestExtractSessionId` additions
- `test_extract_session_id_from_llm_response_dict_format` — file has `response_data.session_id` (new format), verify extracted correctly

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Your task is to implement Step 1: extend `store_session()` and `extract_session_id()` in
`src/mcp_coder/llm/storage/session_storage.py`.

Follow TDD: write the new tests in `tests/llm/storage/test_session_storage.py` FIRST,
then implement the changes.

Key changes:
1. Add `step_name: Optional[str] = None` and `branch_name: Optional[str] = None` params to `store_session()`
2. Change filename: if step_name provided → `{timestamp}_{step_name}.json`; else keep `response_{timestamp}.json`
3. Add branch_name and step_name to metadata (only when not None)
4. Extract model from `response_data["raw_response"].get("session_info", {}).get("model") or response_data["provider"]`
5. Add import `from ..types import LLMResponseDict` and update type annotation of `response_data` param
6. In `extract_session_id()`, add a new lookup path: `session_data.get("response_data", {}).get("session_id")`

Do NOT change the outer JSON structure ({ prompt, response_data, metadata }).
Do NOT change any callers in this step — that is done in later steps.
Run the tests to confirm they pass before finishing.
```
