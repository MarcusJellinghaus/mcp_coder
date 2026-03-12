"""LangChain provider package.

Entry point for the LangChain provider. Supports OpenAI, Gemini, and Anthropic backends.
All LangChain library imports are deferred to the backend modules so that
importing this package does not fail when langchain is not installed.
"""

import os
import uuid
from datetime import datetime

from mcp_coder.llm.storage.session_storage import (
    load_langchain_history,
    store_langchain_history,
)
from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict
from mcp_coder.utils.user_config import get_config_values


def _load_langchain_config() -> dict[str, str | None]:
    """Read [llm] and [llm.langchain] from config.toml via get_config_values().

    Environment variables override config file values:
        MCP_CODER_LLM_LANGCHAIN_BACKEND   -> backend
        MCP_CODER_LLM_LANGCHAIN_MODEL     -> model
        MCP_CODER_LLM_LANGCHAIN_ENDPOINT  -> endpoint
        MCP_CODER_LLM_LANGCHAIN_API_VERSION -> api_version

    API keys are resolved by the vendor env var (OPENAI_API_KEY, GEMINI_API_KEY,
    ANTHROPIC_API_KEY) in each backend module, falling back to config.toml.

    Returns keys: provider, backend, model, api_key, endpoint, api_version.
    """
    raw = get_config_values(
        [
            ("llm", "provider", None),
            ("llm.langchain", "backend", None),
            ("llm.langchain", "model", None),
            ("llm.langchain", "api_key", None),
            ("llm.langchain", "endpoint", None),
            ("llm.langchain", "api_version", None),
        ]
    )
    config = {
        "provider": raw[("llm", "provider")],
        "backend": raw[("llm.langchain", "backend")],
        "model": raw[("llm.langchain", "model")],
        "api_key": raw[("llm.langchain", "api_key")],
        "endpoint": raw[("llm.langchain", "endpoint")],
        "api_version": raw[("llm.langchain", "api_version")],
    }
    # Env vars override config file values
    env_overrides = {
        "backend": "MCP_CODER_LLM_LANGCHAIN_BACKEND",
        "model": "MCP_CODER_LLM_LANGCHAIN_MODEL",
        "endpoint": "MCP_CODER_LLM_LANGCHAIN_ENDPOINT",
        "api_version": "MCP_CODER_LLM_LANGCHAIN_API_VERSION",
    }
    for key, env_var in env_overrides.items():
        value = os.environ.get(env_var)
        if value:
            config[key] = value
    return config


def _create_chat_model(config: dict[str, str]) -> object:
    """Dispatch to correct backend's create_*_model() based on config."""
    backend = config.get("backend")

    if backend == "openai":
        from .openai_backend import create_openai_model

        return create_openai_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
            endpoint=config.get("endpoint"),
            api_version=config.get("api_version"),
        )
    if backend == "gemini":
        from .gemini_backend import create_gemini_model

        return create_gemini_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
        )
    if backend == "anthropic":
        from .anthropic_backend import create_anthropic_model

        return create_anthropic_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
        )
    raise ValueError(
        f"Unsupported langchain backend: {backend!r}. "
        "Supported backends: 'openai', 'gemini', 'anthropic'."
    )


def ask_langchain(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
) -> LLMResponseDict:
    """Entry point called by interface.prompt_llm() for provider='langchain'."""
    config = _load_langchain_config()
    backend = config["backend"]

    if not backend:
        raise ValueError(
            "llm.langchain.backend not configured. "
            "Set [llm.langchain] backend in config.toml "
            "or MCP_CODER_LLM_LANGCHAIN_BACKEND env var."
        )

    history = load_langchain_history(session_id) if session_id else []
    sid = session_id or str(uuid.uuid4())

    if backend == "openai":
        from . import openai_backend

        text, raw = openai_backend.ask_openai(
            question=question,
            model=config["model"] or "",
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            api_version=config["api_version"],
            messages=history,
            timeout=timeout,
        )
    elif backend == "gemini":
        from . import gemini_backend

        text, raw = gemini_backend.ask_gemini(
            question=question,
            model=config["model"] or "",
            api_key=config["api_key"],
            messages=history,
            timeout=timeout,
        )
    elif backend == "anthropic":
        from . import anthropic_backend

        text, raw = anthropic_backend.ask_anthropic(
            question=question,
            model=config["model"] or "",
            api_key=config["api_key"],
            messages=history,
            timeout=timeout,
        )
    else:
        raise ValueError(
            f"Unsupported langchain backend: {backend!r}. "
            "Supported backends: 'openai', 'gemini', 'anthropic'."
        )

    updated_history = history + [
        {"role": "human", "content": question},
        {"role": "ai", "content": text},
    ]
    store_langchain_history(sid, updated_history)

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=sid,
        method="api",
        provider="langchain",
        raw_response=raw,
    )
