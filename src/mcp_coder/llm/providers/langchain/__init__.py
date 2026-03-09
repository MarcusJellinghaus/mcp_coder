"""LangChain provider package.

Entry point for the LangChain provider. Supports OpenAI and Gemini backends.
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
    return {
        "provider": raw[("llm", "provider")],
        "backend": raw[("llm.langchain", "backend")],
        "model": raw[("llm.langchain", "model")],
        "api_key": raw[("llm.langchain", "api_key")],
        "endpoint": raw[("llm.langchain", "endpoint")],
        "api_version": raw[("llm.langchain", "api_version")],
    }


def ask_langchain(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
) -> LLMResponseDict:
    """Entry point called by interface.prompt_llm() for provider='langchain'."""
    config = _load_langchain_config()
    backend = config["backend"]

    if not backend:
        raise ValueError("llm.langchain.backend not configured in config.toml")

    if env_vars:
        os.environ.update(env_vars)

    history = load_langchain_history(session_id) if session_id else []
    sid = session_id or str(uuid.uuid4())

    if backend == "openai":
        from . import openai

        text, raw = openai.ask_openai(
            question=question,
            model=config["model"] or "",
            api_key=config["api_key"],
            endpoint=config["endpoint"],
            api_version=config["api_version"],
            messages=history,
            timeout=timeout,
        )
    elif backend == "gemini":
        from . import gemini

        text, raw = gemini.ask_gemini(
            question=question,
            model=config["model"] or "",
            api_key=config["api_key"],
            messages=history,
            timeout=timeout,
        )
    elif backend == "anthropic":
        from . import anthropic

        text, raw = anthropic.ask_anthropic(
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
