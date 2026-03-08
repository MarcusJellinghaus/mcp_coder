# Step 4: Interface Routing (TDD)

Wire the langchain provider into `prompt_llm()` with a single `elif` branch.
All previous steps (1–3) must be complete before this step.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for full context.
Steps 1–3 are already complete.

Implement Step 4 using TDD:
1. First read tests/llm/test_interface.py to understand the existing test style.
2. Append the new test class described below to that file.
3. Run the new tests — they will fail (the branch doesn't exist yet).
4. Add the `elif provider == "langchain":` branch to
   src/mcp_coder/llm/interface.py as described below.
5. Re-run the tests — all must pass.
6. Confirm existing tests are still green: pytest tests/llm/test_interface.py
```

---

## WHERE

| File | Action |
|---|---|
| `tests/llm/test_interface.py` | Edit — append new test class |
| `src/mcp_coder/llm/interface.py` | Edit — add `elif` branch + update error message |

---

## WHAT

### Changes to `interface.py`

**A. Add `elif` branch inside `prompt_llm()`, after the `elif method == "api":` block:**

```python
elif provider == "langchain":
    from .providers.langchain import ask_langchain  # lazy import
    return ask_langchain(
        question,
        session_id=session_id,
        timeout=timeout,
        env_vars=env_vars,
    )
```

**B. Update the `else` error message** (currently says `'claude'` only):

```python
# Before:
raise ValueError(
    f"Unsupported provider: {provider}. Currently supported: 'claude'"
)

# After:
raise ValueError(
    f"Unsupported provider: {provider}. Supported: 'claude', 'langchain'"
)
```

That is the complete change to `interface.py`.

---

## HOW

### Why lazy import

The `from .providers.langchain import ask_langchain` is **inside** the `elif`
branch. This means:

- LangChain is never imported when the provider is `"claude"` (the common case).
- If LangChain is not installed and the user requests it, the `ImportError` from
  the provider package propagates naturally with the install instructions added
  in Step 3.
- No change to any existing import at the top of `interface.py`.

### Parameters silently ignored for langchain

`execution_dir`, `mcp_config`, and `branch_name` are Claude-specific parameters
that have no meaning for LangChain. They are simply not passed to `ask_langchain`.
No warning or error is raised — consistent with the spec ("silently ignored").

`method` is also silently ignored (LangChain always uses direct API).
This is already handled because `ask_langchain` has no `method` parameter.

---

## ALGORITHM

No complex logic — pure dispatch:

```
if provider == "claude":
    existing claude routing unchanged
elif provider == "langchain":
    lazy import ask_langchain
    return ask_langchain(question, session_id, timeout, env_vars)
else:
    raise ValueError("Unsupported provider: ... Supported: 'claude', 'langchain'")
```

---

## DATA

`prompt_llm()` signature is **unchanged**. Return type `LLMResponseDict` is unchanged.
The new branch returns whatever `ask_langchain()` returns, which is a valid
`LLMResponseDict` with `provider="langchain"` and `method="api"`.

---

## Tests to Write

Append a new test class to `tests/llm/test_interface.py`.
Read the existing file first and follow its mocking style.

```python
class TestPromptLlmLangchainRouting:
    """Test that prompt_llm correctly routes to the langchain provider."""

    def _make_langchain_response(self, text="langchain reply"):
        from datetime import datetime
        return {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "session_id": "uuid-langchain-session",
            "method": "api",
            "provider": "langchain",
            "raw_response": {},
        }

    def test_routes_to_langchain_provider(self):
        """prompt_llm with provider='langchain' calls ask_langchain."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm
            result = prompt_llm("Hello", provider="langchain")

        mock_ask.assert_called_once()
        assert result["provider"] == "langchain"
        assert result["text"] == "langchain reply"

    def test_passes_question_session_timeout_env_vars(self):
        """prompt_llm passes question, session_id, timeout, env_vars to ask_langchain."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm
            prompt_llm(
                "test question",
                provider="langchain",
                session_id="my-sid",
                timeout=60,
                env_vars={"K": "V"},
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        # question, session_id, timeout, env_vars should be forwarded
        args, kwargs = call_kwargs
        all_args = {**dict(zip(["question","session_id","timeout","env_vars"], args)),
                    **kwargs}
        assert all_args.get("session_id") == "my-sid"
        assert all_args.get("timeout") == 60
        assert all_args.get("env_vars") == {"K": "V"}

    def test_method_param_is_silently_ignored(self):
        """prompt_llm with provider='langchain' ignores the method parameter."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm
            # method="cli" should not cause an error
            result = prompt_llm("Hello", provider="langchain", method="cli")
        assert result["provider"] == "langchain"
        mock_ask.assert_called_once()

    def test_unsupported_provider_error_mentions_langchain(self):
        """The ValueError for unsupported providers lists 'langchain' as supported."""
        from mcp_coder.llm.interface import prompt_llm
        with pytest.raises(ValueError) as exc_info:
            prompt_llm("Hello", provider="unsupported_xyz")
        assert "langchain" in str(exc_info.value)

    def test_ask_llm_delegates_to_prompt_llm_for_langchain(self):
        """ask_llm with provider='langchain' also routes correctly."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ):
            from mcp_coder.llm.interface import ask_llm
            result = ask_llm("Hello", provider="langchain")
        assert result == "langchain reply"
```

### Note on patching the lazy import

Because `ask_langchain` is imported **inside** the `elif` branch at call time,
patching `mcp_coder.llm.providers.langchain.ask_langchain` (the module attribute)
works correctly. Check how the existing claude tests mock their providers and
use the same approach.
