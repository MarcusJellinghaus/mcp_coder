# Step 3: Add `verify_langchain()` Domain Function

> **Context:** Read `pr_info/steps/summary.md` first.
> See `pr_info/steps/Decisions.md` — Decisions 6, 8.

## Goal

Create `verify_langchain()` in the langchain provider package. It checks
config, packages, API key, and sends a test prompt. Returns a structured dict.

## Tests First

### WHERE: `tests/llm/providers/langchain/test_langchain_verification.py` (new)

```python
class TestVerifyLangchain:
    """Tests for verify_langchain() domain function."""

    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_no_backend_configured(self, mock_config) -> None:
        mock_config.return_value = {"provider": "langchain", "backend": None, "model": None, "api_key": None, "endpoint": None, "api_version": None}
        result = verify_langchain()
        assert result["backend"]["ok"] is False

    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_openai_backend_configured(self, mock_config) -> None:
        mock_config.return_value = {"provider": "langchain", "backend": "openai", "model": "gpt-4o", "api_key": "sk-abcd1234wxyz5678", ...}
        result = verify_langchain()
        assert result["backend"]["ok"] is True
        assert result["backend"]["value"] == "openai"
        assert result["model"]["value"] == "gpt-4o"

    def test_api_key_masking_normal(self) -> None:
        assert _mask_api_key("sk-abcd1234wxyz5678") == "sk-a...5678"

    def test_api_key_masking_short(self) -> None:
        assert _mask_api_key("short") == "****"

    def test_api_key_masking_none(self) -> None:
        assert _mask_api_key(None) is None

    @patch("mcp_coder.llm.providers.langchain.verification.ask_langchain")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_test_prompt_success(self, mock_config, mock_ask) -> None:
        mock_config.return_value = {... "backend": "openai", "api_key": "sk-test1234test5678", ...}
        mock_ask.return_value = {"text": "OK", ...}
        result = verify_langchain()
        assert result["test_prompt"]["ok"] is True

    @patch("mcp_coder.llm.providers.langchain.verification.ask_langchain")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_test_prompt_failure(self, mock_config, mock_ask) -> None:
        mock_config.return_value = {... "backend": "openai", "api_key": "sk-test1234test5678", ...}
        mock_ask.side_effect = Exception("404 model not found")
        result = verify_langchain()
        assert result["test_prompt"]["ok"] is False
        assert "404" in result["test_prompt"]["error"]

    def test_test_prompt_skipped_no_api_key(self, ...) -> None:
        ...  # No API key → test_prompt.ok=None (skipped)

    def test_langchain_core_not_installed(self, ...) -> None:
        ...  # importlib check fails → langchain_core.ok=False

    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_check_models_flag(self, mock_config, ...) -> None:
        ...  # check_models=True → available_models key present


class TestMaskApiKey:
    """Focused tests for _mask_api_key helper."""
    ...
```

### WHERE: `tests/llm/providers/langchain/test_langchain_list_models.py` (new — coverage for existing functions)

The `list_*_models()` functions already exist in `_models.py` (Decision 8).
This test file adds coverage for them.

```python
class TestListModels:
    """Tests for existing list_*_models() functions in _models.py."""

    @patch("mcp_coder.llm.providers.langchain._models.openai")
    def test_list_openai_models(self, ...) -> None:
        ...

    @patch("mcp_coder.llm.providers.langchain._models.genai")
    def test_list_gemini_models(self, ...) -> None:
        ...

    @patch("mcp_coder.llm.providers.langchain._models.anthropic")
    def test_list_anthropic_models(self, ...) -> None:
        ...

    def test_list_models_returns_list_of_strings(self, ...) -> None:
        ...

    def test_list_models_handles_api_error(self, ...) -> None:
        ...

    def test_list_models_import_error(self, ...) -> None:
        ...  # Raises ImportError when SDK not installed
```

## Implementation

### WHERE: `src/mcp_coder/llm/providers/langchain/verification.py` (new file)

**WHAT:**
```python
def verify_langchain(check_models: bool = False) -> dict[str, Any]:
def _mask_api_key(key: str | None) -> str | None:
def _resolve_api_key(backend: str | None, config_key: str | None) -> tuple[str | None, str | None]:
def _check_package_installed(package_name: str) -> bool:
```

**ALGORITHM for `verify_langchain()`:**
```
1. Load config via _load_langchain_config()
2. Check backend, model, API key — populate result dict entries
3. Check langchain-core installed (importlib.util.find_spec)
4. Check backend package installed (e.g. langchain-openai)
5. If API key present: call ask_langchain("Reply with OK", timeout=15), measure time
6. If check_models: import and call list_*_models() from _models.py for the configured backend
7. Return result dict
```

**DATA — Return structure:**
```python
{
    "backend":          {"ok": bool, "value": str|None},
    "model":            {"ok": bool, "value": str|None},
    "api_key":          {"ok": bool, "value": str|None, "source": str|None},
                        # value is masked: "sk-ab...7x2f"
                        # source: "OPENAI_API_KEY env var" or "config.toml"
    "langchain_core":   {"ok": bool, "value": "installed"/"not installed"},
    "backend_package":  {"ok": bool, "value": "langchain-openai installed"/"not installed"},
    "test_prompt":      {"ok": bool|None, "value": str|None, "error": str|None},
                        # ok=None when skipped (no API key)
                        # value: "responded in 1.2s"
    "available_models": {"ok": bool, "value": list[str]},  # only if check_models=True
    "overall_ok":       bool,
}
```

**HOW — API key resolution:**
```python
_BACKEND_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

def _resolve_api_key(backend, config_key):
    env_var = _BACKEND_ENV_VARS.get(backend)
    if env_var and os.environ.get(env_var):
        return os.environ[env_var], f"{env_var} env var"
    if config_key:
        return config_key, "config.toml"
    return None, None
```

**HOW — API key masking:**
```python
def _mask_api_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"
```

**HOW — Package check:**
```python
_BACKEND_PACKAGES = {
    "openai": "langchain_openai",
    "gemini": "langchain_google_genai",
    "anthropic": "langchain_anthropic",
}

def _check_package_installed(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None
```

**HOW — Test prompt (reuses existing `ask_langchain`):**
```python
import time
from . import ask_langchain

start = time.monotonic()
try:
    ask_langchain("Reply with OK", timeout=15)
    elapsed = time.monotonic() - start
    result["test_prompt"] = {"ok": True, "value": f"responded in {elapsed:.1f}s"}
except Exception as e:
    result["test_prompt"] = {"ok": False, "error": str(e)}
```

**HOW — `overall_ok` logic:**
```python
# overall_ok is True when: backend configured AND backend package installed AND
# (test_prompt succeeded OR test_prompt was skipped due to no API key)
```

## Checklist

- [ ] `verify_langchain()` returns structured dict
- [ ] `_mask_api_key()` masks first 4 + last 4 chars
- [ ] API key source detection (env var name or config.toml)
- [ ] Package checks via `importlib.util.find_spec`
- [ ] Test prompt calls `ask_langchain()` with 15s timeout
- [ ] `--check-models` imports and calls existing `list_*_models()` from `_models.py`
- [ ] Tests for existing `list_*_models()` functions (coverage)
- [ ] Graceful when langchain not installed (import check, not crash)
- [ ] All tests pass with mocked config and imports
