"""LangChain provider package.

Entry point for the LangChain provider. Supports OpenAI, Gemini, and Anthropic backends.
All LangChain library imports are deferred to the backend modules so that
importing this package does not fail when langchain is not installed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mcp_coder.llm.mlflow_logger import get_mlflow_logger
from mcp_coder.llm.storage.session_storage import (
    load_langchain_history,
    store_langchain_history,
)
from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict
from mcp_coder.utils.user_config import get_config_values

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


logger = logging.getLogger(__name__)


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


def _create_chat_model(config: dict[str, str | None]) -> BaseChatModel:
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
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
) -> LLMResponseDict:
    """Entry point called by interface.prompt_llm() for provider='langchain'.

    When *mcp_config* is provided the request is routed through the LangGraph
    ReAct agent (agent mode).  Otherwise the existing text-only backend
    dispatch is used.
    """
    config = _load_langchain_config()
    backend = config["backend"]

    if not backend:
        raise ValueError(
            "llm.langchain.backend not configured. "
            "Set [llm.langchain] backend in config.toml "
            "or MCP_CODER_LLM_LANGCHAIN_BACKEND env var."
        )

    sid = session_id or str(uuid.uuid4())

    if mcp_config:
        return _ask_agent(
            question=question,
            config=config,
            session_id=sid,
            mcp_config=mcp_config,
            execution_dir=execution_dir,
            env_vars=env_vars,
            timeout=timeout,
        )

    return _ask_text(
        question=question,
        config=config,
        backend=backend,
        session_id=sid,
        timeout=timeout,
    )


def _ask_text(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
) -> LLMResponseDict:
    """Text-only backend dispatch using unified chat model factory."""
    from ._utils import _to_lc_messages

    history = load_langchain_history(session_id)
    lc_messages = _to_lc_messages(history + [{"role": "human", "content": question}])

    chat_model = _create_chat_model(config)

    try:
        ai_msg = chat_model.invoke(lc_messages)
    except Exception as exc:
        exc_str = str(exc)
        if "404" in exc_str or "not_found" in exc_str.lower() or "NOT_FOUND" in exc_str:
            model = config.get("model", "")
            hint = f"Model {model!r} not found."
            try:
                hint += _get_model_suggestions(config)
            except Exception:  # pylint: disable=broad-except
                pass
            raise ValueError(hint) from exc
        raise

    text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    raw: dict[str, object] = {
        "backend": backend,
        "model": config.get("model", ""),
        "response_content": text,
    }

    updated_history = history + [
        {"role": "human", "content": question},
        {"role": "ai", "content": text},
    ]
    store_langchain_history(session_id, updated_history)

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=sid,
        method="api",
        provider="langchain",
        raw_response=raw,
    )


def _get_model_suggestions(config: dict[str, str | None]) -> str:
    """Try to list available models for the configured backend."""
    backend = config.get("backend")
    api_key = config.get("api_key")
    endpoint = config.get("endpoint")

    from ._models import list_anthropic_models, list_gemini_models, list_openai_models

    models: list[str] = []
    if backend == "openai":
        models = list_openai_models(os.getenv("OPENAI_API_KEY") or api_key, endpoint)
    elif backend == "gemini":
        models = list_gemini_models(os.getenv("GEMINI_API_KEY") or api_key)
    elif backend == "anthropic":
        models = list_anthropic_models(os.getenv("ANTHROPIC_API_KEY") or api_key)

    if models:
        return "\n\nAvailable models:\n" + "\n".join(f"  - {m}" for m in models)
    return ""


def _ask_agent(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
) -> LLMResponseDict:
    """Agent mode: route through LangGraph ReAct agent with MCP tools."""
    from .agent import _check_agent_dependencies, run_agent

    _check_agent_dependencies()

    chat_model = _create_chat_model(config)
    history: list[dict[str, Any]] = load_langchain_history(session_id)

    text, messages, stats = asyncio.run(
        run_agent(
            question=question,
            chat_model=chat_model,
            messages=history,
            mcp_config_path=mcp_config,
            execution_dir=execution_dir,
            env_vars=env_vars,
            timeout=timeout,
        )
    )

    store_langchain_history(session_id, messages)

    raw_response: dict[str, Any] = {
        "messages": messages,
        "backend": config.get("backend", ""),
        "model": config.get("model", ""),
        **stats,
    }

    # MLflow logging for agent mode
    _log_agent_mlflow(config, stats, session_id)

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=session_id,
        method="api",
        provider="langchain",
        raw_response=raw_response,
    )


def _log_agent_mlflow(
    config: dict[str, str | None],
    stats: dict[str, Any],
    session_id: str,
) -> None:
    """Log agent mode params, metrics, and tool_trace artifact to MLflow."""
    try:
        mlflow_logger = get_mlflow_logger()
        mlflow_logger.start_run(session_id=session_id)

        try:
            mlflow_logger.log_params(
                {
                    "backend": config.get("backend", ""),
                    "model": config.get("model", ""),
                    "tool_call_count": stats.get("total_tool_calls", 0),
                }
            )

            mlflow_logger.log_metrics(
                {
                    "agent_steps": float(stats.get("agent_steps", 0)),
                    "total_tool_calls": float(stats.get("total_tool_calls", 0)),
                }
            )

            tool_trace = stats.get("tool_trace", [])
            if tool_trace:
                mlflow_logger.log_artifact(
                    json.dumps(tool_trace, indent=2, default=str),
                    "tool_trace.json",
                )
        finally:
            mlflow_logger.end_run(session_id=session_id)
    except Exception:
        logger.debug("MLflow logging failed for agent mode", exc_info=True)
