# Step 1 — Backend factory + dispatch wiring + conftest mocks

This step lands the minimum needed for `_create_chat_model()` to be
able to construct a `ChatOllama` instance when
`config["backend"] == "ollama"`. Subsequent steps build on top.

## WHERE

**Create:**
- `src/mcp_coder/llm/providers/langchain/ollama_backend.py`
- `tests/llm/providers/langchain/test_langchain_ollama.py`

**Modify:**
- `src/mcp_coder/llm/providers/langchain/_models.py` — add
  `_resolve_ollama_host()` helper at module scope.
- `src/mcp_coder/llm/providers/langchain/__init__.py` — add the
  `"ollama"` branch to `_create_chat_model()`, add the
  `_BACKEND_ERROR_PARAMS["ollama"]` entry, and extend the
  unsupported-backend error message to include `"ollama"`.
- `tests/llm/providers/langchain/conftest.py` — mock `langchain_ollama`
  and `ollama` in `_mock_langchain_modules` so unit tests run without
  the optional packages installed.

## WHAT

```python
# _models.py
def _resolve_ollama_host(endpoint: str | None) -> str | None:
    """Resolve OLLAMA_HOST env > endpoint config > None, normalize to URL."""
```

```python
# ollama_backend.py
def create_ollama_model(
    model: str,
    api_key: str | None,
    endpoint: str | None = None,
    timeout: int = 30,
) -> ChatOllama:
    """Create a ChatOllama chat model without invoking it."""
```

## HOW

- `ollama_backend.py` follows the exact import pattern of
  `anthropic_backend.py`: `try: from langchain_ollama import ChatOllama
  except ImportError: raise ImportError("...mcp-coder[langchain]...")`.
- `_create_chat_model()` in `__init__.py` adds:
  ```python
  if backend == "ollama":
      from .ollama_backend import create_ollama_model
      return create_ollama_model(
          model=config.get("model") or "",
          api_key=config.get("api_key"),
          endpoint=config.get("endpoint"),
          timeout=timeout,
      )
  ```
- `_BACKEND_ERROR_PARAMS["ollama"] = ("Ollama", "OLLAMA_API_KEY",
  "endpoint/OLLAMA_HOST if not localhost")`.
- Update the `raise ValueError(f"Unsupported langchain backend: ...")`
  message to include `'ollama'` in the supported list.
- `conftest.py` follows the existing pattern:
  ```python
  if "langchain_ollama" not in sys.modules:
      mocks["langchain_ollama"] = MagicMock()
  if "ollama" not in sys.modules:
      mocks["ollama"] = MagicMock()
  ```

## ALGORITHM

```
def _resolve_ollama_host(endpoint):
    host = os.getenv("OLLAMA_HOST") or endpoint
    if host and "://" not in host:
        host = f"http://{host}"
    return host

def create_ollama_model(model, api_key, endpoint=None, timeout=30):
    effective_key = os.getenv("OLLAMA_API_KEY") or api_key
    kwargs = {"model": model, "timeout": float(timeout)}
    base_url = _resolve_ollama_host(endpoint)
    if base_url:
        kwargs["base_url"] = base_url
    if effective_key:
        kwargs["client_kwargs"] = {"headers":
            {"Authorization": f"Bearer {effective_key}"}}
    return ChatOllama(**kwargs)
```

**Note on `client_kwargs`:** verify the exact `ChatOllama` kwarg for
forwarding HTTP headers (likely `client_kwargs={"headers": {...}}`).
If the underlying `httpx.Client(headers=...)` shape differs in the
installed `langchain-ollama` version, adjust the kwarg name only —
keep the resolution logic the same. The `api_key` codepath is for
proxy-auth setups; localhost setups will pass through with
`effective_key` being `None`.

## DATA

**`_resolve_ollama_host` returns:**
- `None` when neither `OLLAMA_HOST` nor `endpoint` is set
- A normalized URL string like `"http://127.0.0.1:11434"` otherwise

**`create_ollama_model` returns:**
- A `ChatOllama` instance configured with `model`, optional `base_url`,
  optional auth-header `client_kwargs`, and `timeout` as float.

## Tests (write FIRST, TDD)

`tests/llm/providers/langchain/test_langchain_ollama.py`, mirroring
`test_langchain_anthropic.py`:

- `test_ollama_host_env_overrides_config_endpoint` — sets
  `OLLAMA_HOST=foo:1234`, passes `endpoint="bar:5678"`, asserts
  `base_url="http://foo:1234"`.
- `test_ollama_host_normalization_adds_http_scheme` — `OLLAMA_HOST=
  127.0.0.1:11434` → `base_url="http://127.0.0.1:11434"`.
- `test_ollama_host_with_scheme_passes_through` — `OLLAMA_HOST=
  https://ollama.example.com` is NOT modified.
- `test_no_endpoint_no_env_omits_base_url` — neither set → `base_url`
  kwarg is NOT passed (let `ChatOllama` default apply).
- `test_api_key_env_overrides_config` — `OLLAMA_API_KEY=env-key`
  beats `api_key="config-key"`; asserts header value.
- `test_no_api_key_omits_client_kwargs` — neither key set → no
  `client_kwargs` passed.
- `test_timeout_is_forwarded_as_float` — `timeout=45` →
  `kwargs["timeout"] == 45.0`.
- `test_returns_chat_ollama_instance` — return value is the mock
  instance.

Add one test in `test_langchain_provider.py` (or extend an existing
dispatch test) verifying that `_create_chat_model({"backend":
"ollama", ...})` calls `create_ollama_model` with the expected
arguments. Look at how the openai/gemini/anthropic branches are tested
and follow that pattern.

## Definition of done

- All eight new `test_langchain_ollama.py` tests pass.
- The dispatch test asserts the ollama branch is taken.
- `mcp__tools-py__run_pylint_check`, `run_pytest_check`, and
  `run_mypy_check` all pass for the unit-test layer.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1 only. Follow TDD: write the tests in
tests/llm/providers/langchain/test_langchain_ollama.py FIRST (and
extend tests/llm/providers/langchain/conftest.py with mocks for
langchain_ollama and ollama), then implement
src/mcp_coder/llm/providers/langchain/ollama_backend.py and add the
helper + dispatch wiring described in the step.

Mirror the existing anthropic_backend.py / openai_backend.py /
gemini_backend.py shape exactly. Do not invent new patterns.

Do not touch any other module — model listing, daemon probe,
capability check, agent wiring, and docs are landed in subsequent
steps.

After the edits, run all three MCP code-quality checks
(mcp__tools-py__run_pylint_check, run_pytest_check with
extra_args=["-n", "auto", "-m", "not git_integration and not
claude_cli_integration and not claude_api_integration and not
formatter_integration and not github_integration and not
langchain_integration"], run_mypy_check) and confirm zero issues
before reporting the step complete.
```
