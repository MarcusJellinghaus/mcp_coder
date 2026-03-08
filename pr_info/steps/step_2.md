# Step 2: Session History Storage (TDD)

LangChain does not store conversation history server-side.
Two helper functions are added to the **existing** `session_storage.py` so
message history survives process restarts. `session_storage.py` must not
import any LangChain types — only plain Python dicts.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement Step 2 using TDD:
1. First write the tests (marked section below) in
   tests/llm/storage/test_session_storage.py (append to the existing file).
2. Then implement the three new functions in
   src/mcp_coder/llm/storage/session_storage.py (append to the existing file).
3. Run pytest tests/llm/storage/test_session_storage.py to confirm all new
   tests pass. Do not break any existing tests in that file.
```

---

## WHERE

| File | Action |
|---|---|
| `tests/llm/storage/test_session_storage.py` | Edit — append new test class |
| `src/mcp_coder/llm/storage/session_storage.py` | Edit — append three new functions |

---

## WHAT

### New functions in `session_storage.py`

```python
def _langchain_session_path(
    session_id: str,
    base_dir: str | None = None,
) -> Path:
    """Return Path for a session's history JSON file.
    Default: ~/.mcp_coder/sessions/langchain/{session_id}.json
    """

def store_langchain_history(
    session_id: str,
    messages: list[dict[str, str]],
    base_dir: str | None = None,
) -> str:
    """Persist message history to disk. Returns the file path written."""

def load_langchain_history(
    session_id: str,
    base_dir: str | None = None,
) -> list[dict[str, str]]:
    """Load message history from disk. Returns [] if no file exists."""
```

Add to `__all__`:

```python
"store_langchain_history",
"load_langchain_history",
```

(`_langchain_session_path` is private — not exported.)

---

## HOW

### Imports to add to `session_storage.py`

```python
from pathlib import Path
```

(`pathlib` is stdlib — no new dependency.)

### Integration

- `store_langchain_history` and `load_langchain_history` are called exclusively
  by `src/mcp_coder/llm/providers/langchain/__init__.py` (Step 3).
- `session_storage.py` has **no import of langchain** — isolation preserved.

---

## ALGORITHM

```
_langchain_session_path(session_id, base_dir):
    root = Path(base_dir) if base_dir else Path.home() / ".mcp_coder" / "sessions" / "langchain"
    return root / f"{session_id}.json"

store_langchain_history(session_id, messages, base_dir):
    path = _langchain_session_path(session_id, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(messages, indent=2), encoding="utf-8")
    return str(path)

load_langchain_history(session_id, base_dir):
    path = _langchain_session_path(session_id, base_dir)
    if not path.exists(): return []
    return json.loads(path.read_text(encoding="utf-8"))
```

---

## DATA

### Message format (plain dicts — no LangChain types)

```python
messages: list[dict[str, str]] = [
    {"role": "human", "content": "My favourite colour is blue."},
    {"role": "ai",    "content": "Got it — your favourite colour is blue."},
]
```

`role` values: `"human"` | `"ai"` (matching LangChain's internal convention).

### Storage path

```
~/.mcp_coder/sessions/langchain/{session_id}.json
```

On Windows this resolves to:
```
%USERPROFILE%\.mcp_coder\sessions\langchain\{session_id}.json
```

---

## Tests to Write

Append a new test class to `tests/llm/storage/test_session_storage.py`.
Use `tmp_path` (pytest built-in fixture) to avoid touching the real home directory.

```python
class TestLangchainSessionStorage:
    """Tests for store_langchain_history / load_langchain_history."""

    def test_store_and_load_roundtrip(self, tmp_path):
        """Stored messages can be loaded back unchanged."""
        messages = [
            {"role": "human", "content": "Hello"},
            {"role": "ai", "content": "Hi there"},
        ]
        session_id = "test-session-abc"
        store_langchain_history(session_id, messages, base_dir=str(tmp_path))
        loaded = load_langchain_history(session_id, base_dir=str(tmp_path))
        assert loaded == messages

    def test_load_returns_empty_list_when_no_file(self, tmp_path):
        """Loading a non-existent session returns an empty list."""
        result = load_langchain_history("nonexistent-id", base_dir=str(tmp_path))
        assert result == []

    def test_store_creates_parent_directory(self, tmp_path):
        """store_langchain_history creates nested directories automatically."""
        base = tmp_path / "deep" / "nested"
        store_langchain_history("sid", [], base_dir=str(base))
        assert (base / "sid.json").exists()

    def test_store_returns_file_path_string(self, tmp_path):
        """store_langchain_history returns the path it wrote to."""
        path = store_langchain_history("sid", [], base_dir=str(tmp_path))
        assert path.endswith("sid.json")
        assert os.path.isfile(path)

    def test_store_overwrites_existing_session(self, tmp_path):
        """A second store call replaces the previous history."""
        session_id = "overwrite-test"
        store_langchain_history(session_id, [{"role": "human", "content": "v1"}],
                                base_dir=str(tmp_path))
        store_langchain_history(session_id, [{"role": "human", "content": "v2"}],
                                base_dir=str(tmp_path))
        loaded = load_langchain_history(session_id, base_dir=str(tmp_path))
        assert loaded == [{"role": "human", "content": "v2"}]

    def test_empty_messages_list_roundtrip(self, tmp_path):
        """An empty message list is stored and loaded correctly."""
        store_langchain_history("empty-sid", [], base_dir=str(tmp_path))
        assert load_langchain_history("empty-sid", base_dir=str(tmp_path)) == []

    def test_default_path_uses_home_directory(self, monkeypatch, tmp_path):
        """Without base_dir, files go under ~/.mcp_coder/sessions/langchain/."""
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        session_id = "home-test"
        store_langchain_history(session_id, [])
        expected = tmp_path / ".mcp_coder" / "sessions" / "langchain" / f"{session_id}.json"
        assert expected.exists()
```

### Imports to add at the top of the test file (if not already present)

```python
import os
from pathlib import Path
from mcp_coder.llm.storage.session_storage import (
    store_langchain_history,
    load_langchain_history,
)
```
