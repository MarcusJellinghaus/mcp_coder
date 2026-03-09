# Step 3: LangChain Provider Package (TDD)

Create the three-file provider package and its unit tests.
All LangChain imports are confined to this package (enforced by the
import-linter contract added in Step 1).

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.
Step 1 (project config) and Step 2 (session storage) are already complete.

Implement Step 3 using TDD:
1. Create the test files listed below with all mocked tests.
2. Create the three provider source files.
3. Run pytest tests/llm/providers/langchain/ -x to confirm all tests pass.
4. Also update tests/llm/providers/test_provider_structure.py to assert
   that the langchain package exists (read the file first to follow its pattern).

Do NOT install langchain packages — all tests must run without them (mocked).
```

---

## WHERE

### Files to create

| File | Purpose |
|---|---|
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Entry point, config, dispatch |
| `src/mcp_coder/llm/providers/langchain/openai.py` | OpenAI backend |
| `src/mcp_coder/llm/providers/langchain/gemini.py` | Gemini backend |
| `src/mcp_coder/llm/providers/langchain/_utils.py` | Shared message conversion helpers |
| `tests/llm/providers/langchain/__init__.py` | Empty — package marker |
| `tests/llm/providers/langchain/conftest.py` | `sys.modules` mocks — unit tests run without langchain installed |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Tests for `__init__.py` |
| `tests/llm/providers/langchain/test_langchain_openai.py` | Tests for `openai.py` |
| `tests/llm/providers/langchain/test_langchain_gemini.py` | Tests for `gemini.py` |

### Files to modify

| File | Change |
|---|---|
| `tests/llm/providers/test_provider_structure.py` | Assert `langchain` package is present |

---

## WHAT

### `langchain/__init__.py`

```python
def ask_langchain(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
) -> LLMResponseDict:
    """Entry point called by interface.prompt_llm() for provider='langchain'."""

def _load_langchain_config() -> dict[str, str | None]:
    """Read [llm] and [llm.langchain] from config.toml via get_config_values().
    Returns keys: provider, backend, model, api_key, endpoint, api_version.
    """
```

### `langchain/openai.py`

```python
def ask_openai(
    question: str,
    model: str,
    api_key: str | None,
    endpoint: str | None,
    api_version: str | None,
    messages: list[dict[str, str]],
    timeout: int = 30,
) -> tuple[str, dict[str, object]]:
    """Call ChatOpenAI, or AzureChatOpenAI when api_version is set.
    Returns (response_text, raw_response_dict).
    Raises ImportError with install instructions if langchain_openai missing.
    """
```

### `langchain/gemini.py`

```python
def ask_gemini(
    question: str,
    model: str,
    api_key: str | None,
    messages: list[dict[str, str]],
    timeout: int = 30,
) -> tuple[str, dict[str, object]]:
    """Call ChatGoogleGenerativeAI. Returns (response_text, raw_response_dict).
    Raises ImportError with install instructions if langchain_google_genai missing.
    """
```

---

## HOW

### Config loading (`__init__.py`)

```python
from mcp_coder.utils.user_config import get_config_values

def _load_langchain_config() -> dict[str, str | None]:
    raw = get_config_values([
        ("llm",          "provider",    None),
        ("llm.langchain","backend",     None),
        ("llm.langchain","model",       None),
        ("llm.langchain","api_key",     None),   # env var checked in backend
        ("llm.langchain","endpoint",    None),
        ("llm.langchain","api_version", None),   # Azure OpenAI only
    ])
    return {
        "provider":    raw[("llm", "provider")],
        "backend":     raw[("llm.langchain", "backend")],
        "model":       raw[("llm.langchain", "model")],
        "api_key":     raw[("llm.langchain", "api_key")],
        "endpoint":    raw[("llm.langchain", "endpoint")],
        "api_version": raw[("llm.langchain", "api_version")],
    }
```

### Env var priority for api_key (in each backend module)

```python
import os

# Env var takes priority over config file value
effective_api_key = os.getenv("OPENAI_API_KEY") or api_key   # openai.py
effective_api_key = os.getenv("GEMINI_API_KEY") or api_key   # gemini.py
```

### Graceful ImportError (each backend module, at top level)

```python
# openai.py
try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError as exc:
    raise ImportError(
        "LangChain OpenAI backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc
```

### Message conversion helpers (`_utils.py`)

Defined **once** in `_utils.py`; both `openai.py` and `gemini.py` import from it:

```python
# _utils.py
from langchain_core.messages import AIMessage, HumanMessage

def _to_lc_messages(messages: list[dict[str, str]]) -> list:
    """Convert plain role/content dicts to LangChain message objects."""
    return [
        HumanMessage(content=m["content"]) if m["role"] == "human"
        else AIMessage(content=m["content"])
        for m in messages
    ]

def _ai_message_to_dict(msg: AIMessage) -> dict[str, object]:
    """Convert AIMessage to a serialisable dict (no pydantic dependency)."""
    return {
        "content": msg.content,
        "response_metadata": getattr(msg, "response_metadata", {}),
        "usage_metadata": getattr(msg, "usage_metadata", None),
        "id": getattr(msg, "id", None),
    }
```

Backends import from `_utils.py` — **neither `openai.py` nor `gemini.py` imports from `langchain_core.messages` directly**:

```python
# openai.py / gemini.py
from ._utils import _ai_message_to_dict, _to_lc_messages
```

### Session storage import in `__init__.py`

```python
from mcp_coder.llm.storage.session_storage import (
    load_langchain_history,
    store_langchain_history,
)
```

---

## ALGORITHM

### `ask_langchain()` (in `__init__.py`)

```
config  = _load_langchain_config()
backend = config["backend"] or raise ValueError("llm.langchain.backend not set")
if env_vars:
    os.environ.update(env_vars)          # applied before any LangChain call
history = load_langchain_history(session_id) if session_id else []
sid     = session_id or str(uuid.uuid4())
text, raw = dispatch to ask_openai or ask_gemini
            (question, config, history, timeout)
updated_history = history + [{"role":"human","content":question}, {"role":"ai","content":text}]
store_langchain_history(sid, updated_history)
return LLMResponseDict(version, timestamp, text, session_id=sid,
                       method="api", provider="langchain", raw_response=raw)
```

### `ask_openai()` — Azure when `api_version` is set

```
effective_api_key = os.getenv("OPENAI_API_KEY") or api_key
lc_messages = _to_lc_messages(history + [{"role": "human", "content": question}])
if api_version:   # Azure OpenAI path
    client = AzureChatOpenAI(azure_deployment=model, azure_endpoint=endpoint,
                             api_key=effective_api_key,
                             openai_api_version=api_version, timeout=timeout)
else:             # Standard OpenAI / custom endpoint (Ollama, etc.)
    client = ChatOpenAI(model=model, api_key=effective_api_key,
                        base_url=endpoint, timeout=timeout)
ai_msg = client.invoke(lc_messages)
raw    = _ai_message_to_dict(ai_msg)
return (str(ai_msg.content), raw)
```

### `ask_gemini()`

```
effective_api_key = os.getenv("GEMINI_API_KEY") or api_key
lc_messages = _to_lc_messages(history + [{"role": "human", "content": question}])
client = ChatGoogleGenerativeAI(model=model, google_api_key=effective_api_key,
                                timeout=timeout)
ai_msg = client.invoke(lc_messages)
raw    = _ai_message_to_dict(ai_msg)
return (str(ai_msg.content), raw)
```

---

## DATA

### `ask_langchain()` return value

```python
LLMResponseDict = {
    "version":      "1.0",
    "timestamp":    "2026-03-08T10:00:00.000000",
    "text":         "Your favourite colour is blue.",
    "session_id":   "550e8400-e29b-41d4-a716-446655440000",  # generated UUID
    "method":       "api",           # always "api" for langchain
    "provider":     "langchain",
    "raw_response": {
        "content":           "Your favourite colour is blue.",
        "response_metadata": {"model_name": "gpt-4o", "finish_reason": "stop"},
        "usage_metadata":    {"input_tokens": 12, "output_tokens": 8},
        "id":                "chatcmpl-abc123",
    }
}
```

---

## Tests to Write

### `test_langchain_provider.py` (tests for `__init__.py`)

All tests mock the backend modules and session storage — no real API calls.

```python
import uuid
from unittest.mock import MagicMock, patch
import pytest

# --- _load_langchain_config ---

class TestLoadLangchainConfig:
    def test_returns_expected_keys(self):
        """_load_langchain_config returns a dict with all expected keys."""
        with patch("mcp_coder.llm.providers.langchain.get_config_values",
                   return_value={
                       ("llm", "provider"):              "langchain",
                       ("llm.langchain", "backend"):     "openai",
                       ("llm.langchain", "model"):       "gpt-4o",
                       ("llm.langchain", "api_key"):     None,
                       ("llm.langchain", "endpoint"):    None,
                       ("llm.langchain", "api_version"): None,
                   }):
            from mcp_coder.llm.providers.langchain import _load_langchain_config
            cfg = _load_langchain_config()
        assert set(cfg.keys()) == {"provider", "backend", "model", "api_key", "endpoint", "api_version"}

# --- ask_langchain ---

class TestAskLangchain:
    def _make_config(self, backend="openai"):
        return {"provider":"langchain","backend":backend,
                "model":"gpt-4o","api_key":None,"endpoint":None,"api_version":None}

    def test_returns_llm_response_dict(self):
        """ask_langchain returns a complete LLMResponseDict."""
        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value=self._make_config()), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[]), \
             patch("mcp_coder.llm.providers.langchain.store_langchain_history"), \
             patch("mcp_coder.llm.providers.langchain.openai.ask_openai",
                   return_value=("Hello!", {"content":"Hello!"})):
            from mcp_coder.llm.providers.langchain import ask_langchain
            result = ask_langchain("Hi")
        assert result["text"] == "Hello!"
        assert result["provider"] == "langchain"
        assert result["method"] == "api"
        assert result["session_id"] is not None

    def test_generates_session_id_when_none_given(self):
        """A UUID session_id is generated when none is provided."""
        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value=self._make_config()), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[]), \
             patch("mcp_coder.llm.providers.langchain.store_langchain_history"), \
             patch("mcp_coder.llm.providers.langchain.openai.ask_openai",
                   return_value=("ok", {})):
            from mcp_coder.llm.providers.langchain import ask_langchain
            result = ask_langchain("question")
        # Must be a valid UUID
        uuid.UUID(result["session_id"])

    def test_preserves_provided_session_id(self):
        """When session_id is passed, it is preserved in the response."""
        sid = "my-session-123"
        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value=self._make_config()), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[]), \
             patch("mcp_coder.llm.providers.langchain.store_langchain_history"), \
             patch("mcp_coder.llm.providers.langchain.openai.ask_openai",
                   return_value=("ok", {})):
            from mcp_coder.llm.providers.langchain import ask_langchain
            result = ask_langchain("question", session_id=sid)
        assert result["session_id"] == sid

    def test_raises_value_error_for_unknown_backend(self):
        """Unsupported backend raises ValueError with a clear message."""
        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value={**self._make_config(), "backend": "unknown_llm"}), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[]), \
             patch("mcp_coder.llm.providers.langchain.store_langchain_history"):
            from mcp_coder.llm.providers.langchain import ask_langchain
            with pytest.raises(ValueError, match="unknown_llm"):
                ask_langchain("question")

    def test_raises_value_error_when_backend_not_configured(self):
        """Missing backend config raises ValueError."""
        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value={**self._make_config(), "backend": None}), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[]):
            from mcp_coder.llm.providers.langchain import ask_langchain
            with pytest.raises(ValueError, match="backend"):
                ask_langchain("question")

    def test_history_is_updated_and_stored(self):
        """After a call, both human and AI messages are appended to history."""
        store_mock = MagicMock()
        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value=self._make_config()), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[{"role":"human","content":"prev"}]), \
             patch("mcp_coder.llm.providers.langchain.store_langchain_history",
                   store_mock), \
             patch("mcp_coder.llm.providers.langchain.openai.ask_openai",
                   return_value=("answer", {})):
            from mcp_coder.llm.providers.langchain import ask_langchain
            ask_langchain("new question", session_id="sid")
        stored_messages = store_mock.call_args[0][1]  # second positional arg
        assert {"role":"human","content":"prev"}   in stored_messages
        assert {"role":"human","content":"new question"} in stored_messages
        assert {"role":"ai",   "content":"answer"} in stored_messages

    def test_env_vars_are_applied_to_environ(self):
        """Non-empty env_vars are merged into os.environ before the backend call."""
        updates = []
        def capture_update(d):
            updates.append(dict(d))

        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value=self._make_config()), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[]), \
             patch("mcp_coder.llm.providers.langchain.store_langchain_history"), \
             patch("mcp_coder.llm.providers.langchain.openai.ask_openai",
                   return_value=("ok", {})), \
             patch("mcp_coder.llm.providers.langchain.os.environ.update",
                   side_effect=capture_update):
            from mcp_coder.llm.providers.langchain import ask_langchain
            ask_langchain("q", env_vars={"INJECTED": "value"})
        assert updates == [{"INJECTED": "value"}]

    def test_no_env_vars_skips_environ_update(self):
        """When env_vars is None, os.environ.update is not called."""
        with patch("mcp_coder.llm.providers.langchain._load_langchain_config",
                   return_value=self._make_config()), \
             patch("mcp_coder.llm.providers.langchain.load_langchain_history",
                   return_value=[]), \
             patch("mcp_coder.llm.providers.langchain.store_langchain_history"), \
             patch("mcp_coder.llm.providers.langchain.openai.ask_openai",
                   return_value=("ok", {})), \
             patch("mcp_coder.llm.providers.langchain.os.environ.update") as mock_update:
            from mcp_coder.llm.providers.langchain import ask_langchain
            ask_langchain("q", env_vars=None)
        mock_update.assert_not_called()
```

### `test_langchain_openai.py` (tests for `openai.py`)

```python
import os
import pytest
from unittest.mock import MagicMock, patch


class TestAskOpenai:
    def _fake_ai_message(self, text="response text"):
        msg = MagicMock()
        msg.content = text
        msg.response_metadata = {"model_name": "gpt-4o"}
        msg.usage_metadata = {"input_tokens": 5, "output_tokens": 3}
        msg.id = "chatcmpl-abc"
        return msg

    def test_returns_text_and_raw_dict(self):
        """ask_openai returns (text, dict) on success."""
        ai_msg = self._fake_ai_message("Hello!")
        # No need to patch HumanMessage/AIMessage — conftest injects sys.modules mocks.
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai
            text, raw = ask_openai("Hi", model="gpt-4o", api_key=None,
                                   endpoint=None, api_version=None, messages=[])
        assert text == "Hello!"
        assert isinstance(raw, dict)
        assert raw["content"] == "Hello!"

    def test_env_var_takes_priority_over_config_api_key(self, monkeypatch):
        """OPENAI_API_KEY env var overrides api_key from config."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai
            ask_openai("Hi", model="gpt-4o", api_key="config-key",
                       endpoint=None, api_version=None, messages=[])
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == "env-key"

    def test_uses_config_api_key_when_env_not_set(self, monkeypatch):
        """Config api_key is used when OPENAI_API_KEY is not in the environment."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai
            ask_openai("Hi", model="gpt-4o", api_key="config-key",
                       endpoint=None, api_version=None, messages=[])
            _, kwargs = MockChat.call_args
            assert kwargs.get("api_key") == "config-key"

    def test_passes_endpoint_as_base_url(self):
        """endpoint is passed to ChatOpenAI as base_url."""
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai
            ask_openai("Hi", model="gpt-4o", api_key=None,
                       endpoint="https://custom.example.com/v1",
                       api_version=None, messages=[])
            _, kwargs = MockChat.call_args
            assert kwargs.get("base_url") == "https://custom.example.com/v1"

    def test_timeout_is_forwarded_to_client(self):
        """timeout is passed to ChatOpenAI constructor."""
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockChat.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai
            ask_openai("Hi", model="gpt-4o", api_key=None, endpoint=None,
                       api_version=None, messages=[], timeout=60)
            _, kwargs = MockChat.call_args
            assert kwargs.get("timeout") == 60

    def test_api_version_triggers_azure_chat_openai(self):
        """When api_version is set, AzureChatOpenAI is used instead of ChatOpenAI."""
        ai_msg = self._fake_ai_message()
        with patch("mcp_coder.llm.providers.langchain.openai.AzureChatOpenAI") as MockAzure, \
             patch("mcp_coder.llm.providers.langchain.openai.ChatOpenAI") as MockChat:
            MockAzure.return_value.invoke.return_value = ai_msg
            from mcp_coder.llm.providers.langchain.openai import ask_openai
            ask_openai("Hi", model="gpt-4o", api_key="k",
                       endpoint="https://my.openai.azure.com/",
                       api_version="2024-02-01", messages=[])
            MockAzure.assert_called_once()
            MockChat.assert_not_called()
            _, kwargs = MockAzure.call_args
            assert kwargs.get("azure_deployment") == "gpt-4o"
            assert kwargs.get("openai_api_version") == "2024-02-01"
```

### `test_langchain_gemini.py` (tests for `gemini.py`)

Four tests — mirror the openai pattern but for the Gemini backend.
Patch `ChatGoogleGenerativeAI`; env var is `GEMINI_API_KEY`; no `endpoint` or `api_version`.
No `HumanMessage`/`AIMessage` patches needed (conftest handles `langchain_core.messages`).

```python
# patch target for all tests:
# patch("mcp_coder.llm.providers.langchain.gemini.ChatGoogleGenerativeAI")

class TestAskGemini:
    def test_returns_text_and_raw_dict(self): ...
    def test_env_var_takes_priority_over_config_api_key(self, monkeypatch): ...
    def test_uses_config_api_key_when_env_not_set(self, monkeypatch): ...
    def test_timeout_is_forwarded_to_client(self): ...
```

---

## Provider Structure Test

Read `tests/llm/providers/test_provider_structure.py` first, then add an
assertion that the `langchain` sub-package exists alongside `claude`:

```python
# Example — adapt to the actual pattern in the file
def test_langchain_package_exists():
    from mcp_coder.llm.providers import langchain  # noqa: F401
    assert hasattr(langchain, "ask_langchain")
```
