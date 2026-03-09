# Step 3b: LangChain Integration Tests

Real API integration tests for the LangChain provider.
These tests send actual requests to the configured backend.
They skip automatically when no credentials are configured.

**Prerequisite:** Step 3 must be complete (Step 4 not required).

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3b.md for full context.
Steps 1–3 are already complete.

Implement Step 3b: create the LangChain integration test file.
Read tests/llm/providers/langchain/ first to follow the existing test style.
Run with: pytest tests/llm/providers/langchain/test_langchain_integration.py \
          -m langchain_integration -v -s
(Tests will skip unless [llm.langchain] is configured in config.toml.)
```

---

## WHERE

| File | Action |
|---|---|
| `tests/llm/providers/langchain/test_langchain_integration.py` | Create |

---

## WHAT

A test module marked `langchain_integration` that:

1. Reads `[llm.langchain]` config to check if credentials are present
2. Skips all tests when no backend, model, or API key is configured
3. Sends real API calls to the configured backend

---

## HOW

### Skip helper

```python
import os
import pytest
from mcp_coder.llm.providers.langchain import _load_langchain_config

def _require_langchain_config() -> None:
    """Skip the test if LangChain is not configured with valid credentials."""
    try:
        cfg = _load_langchain_config()
    except Exception as exc:
        pytest.skip(f"Could not load langchain config: {exc}")

    if not cfg.get("backend"):
        pytest.skip("llm.langchain.backend not set in config.toml")
    if not cfg.get("model"):
        pytest.skip("llm.langchain.model not set in config.toml")

    backend = cfg["backend"]
    if backend == "openai":
        if not os.getenv("OPENAI_API_KEY") and not cfg.get("api_key"):
            pytest.skip("No OpenAI credentials: set OPENAI_API_KEY or [llm.langchain] api_key")
    elif backend == "gemini":
        if not os.getenv("GEMINI_API_KEY") and not cfg.get("api_key"):
            pytest.skip("No Gemini credentials: set GEMINI_API_KEY or [llm.langchain] api_key")
```

### Config source

```toml
# config.toml — example for OpenAI
[llm]
provider = "langchain"

[llm.langchain]
backend  = "openai"
model    = "gpt-4o-mini"
api_key  = "sk-..."       # or set OPENAI_API_KEY env var
```

`MCP_CODER_LLM_PROVIDER` env var (implemented in Step 4) overrides
`[llm] provider` — useful for switching providers in CI without editing config.

---

## ALGORITHM

No complex logic. Call `ask_langchain()` directly and assert the response shape.
The skip helper gates each test before any API call is attempted.

---

## Tests to Write

```python
import os
import pytest
from mcp_coder.llm.providers.langchain import _load_langchain_config

pytestmark = pytest.mark.langchain_integration


def _require_langchain_config() -> None:
    """Skip the test if LangChain is not configured with valid credentials."""
    try:
        cfg = _load_langchain_config()
    except Exception as exc:
        pytest.skip(f"Could not load langchain config: {exc}")

    if not cfg.get("backend"):
        pytest.skip("llm.langchain.backend not set in config.toml")
    if not cfg.get("model"):
        pytest.skip("llm.langchain.model not set in config.toml")

    backend = cfg["backend"]
    if backend == "openai":
        if not os.getenv("OPENAI_API_KEY") and not cfg.get("api_key"):
            pytest.skip("No OpenAI credentials: set OPENAI_API_KEY or [llm.langchain] api_key")
    elif backend == "gemini":
        if not os.getenv("GEMINI_API_KEY") and not cfg.get("api_key"):
            pytest.skip("No Gemini credentials: set GEMINI_API_KEY or [llm.langchain] api_key")


class TestLangchainIntegration:
    """Real API integration tests. Skipped unless [llm.langchain] is configured."""

    def test_ask_langchain_returns_valid_response(self):
        """ask_langchain sends a real question and returns a valid LLMResponseDict."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        result = ask_langchain("Reply with exactly the word: hello")

        assert result["provider"] == "langchain"
        assert result["method"] == "api"
        assert isinstance(result["text"], str)
        assert len(result["text"].strip()) > 0
        assert result["session_id"] is not None
        assert "raw_response" in result

    def test_session_continuity(self):
        """Second call with session_id remembers context from the first call."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        result1 = ask_langchain("My favourite colour is purple. Acknowledge with OK.")
        session_id = result1["session_id"]

        result2 = ask_langchain(
            "What colour did I just mention?", session_id=session_id
        )
        assert "purple" in result2["text"].lower()
        assert result2["session_id"] == session_id
```

---

## Verification

```bash
# Should skip (no config):
pytest tests/llm/providers/langchain/test_langchain_integration.py -m langchain_integration -v

# Should pass (with config + credentials):
pytest tests/llm/providers/langchain/test_langchain_integration.py -m langchain_integration -v -s
```
