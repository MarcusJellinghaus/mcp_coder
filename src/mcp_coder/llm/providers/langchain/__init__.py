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
import queue
import threading
import time
import uuid
from collections.abc import Iterator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mcp_coder.llm.storage.session_storage import (
    load_langchain_history,
    store_langchain_history,
)
from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict, StreamEvent
from mcp_coder.utils.user_config import get_config_values

from ._exceptions import (
    ANTHROPIC_AUTH_ERRORS,
    CONNECTION_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    OPENAI_AUTH_ERRORS,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)
from ._ssl import ensure_truststore

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


logger = logging.getLogger(__name__)

# Agent streaming timeout constants (seconds)
_AGENT_NO_PROGRESS_TIMEOUT = 600  # 10 minutes
_AGENT_OVERALL_TIMEOUT = 3600  # 60 minutes

_BACKEND_ERROR_PARAMS: dict[str, tuple[str, str, str]] = {
    # (provider_label, env_var, endpoint_hint)
    "openai": (
        "OpenAI",
        "OPENAI_API_KEY",
        "endpoint/base_url if using a custom server",
    ),
    "gemini": ("Gemini", "GEMINI_API_KEY", ""),
    "anthropic": ("Anthropic", "ANTHROPIC_API_KEY", ""),
}


def _auth_errors_for_backend(backend: str | None) -> tuple[type[Exception], ...]:
    """Return the auth error tuple for the given backend.

    Args:
        backend: Backend name ("openai", "anthropic", "gemini", or None).

    Returns:
        Tuple of exception classes for auth errors on the given backend.
    """
    if backend == "openai":
        return OPENAI_AUTH_ERRORS
    if backend == "anthropic":
        return ANTHROPIC_AUTH_ERRORS
    if backend == "gemini":
        return GOOGLE_CLIENT_ERRORS  # needs is_google_auth_error() check at call site
    return ()


def _handle_provider_error(exc: Exception, backend: str | None) -> None:
    """Raise LLMAuthError or LLMConnectionError when *exc* matches, else return.

    Args:
        exc: The caught exception.
        backend: Backend name ("openai", "gemini", "anthropic", or None).
    """
    auth_errors = _auth_errors_for_backend(backend)
    provider, env_var, endpoint_hint = _BACKEND_ERROR_PARAMS.get(
        backend or "", (backend or "", "", "")
    )
    if auth_errors and isinstance(exc, auth_errors):
        if backend == "gemini" and not is_google_auth_error(exc):
            raise_connection_error(provider, env_var, exc, endpoint_hint)
        raise_auth_error(provider, env_var, exc)
    if isinstance(exc, CONNECTION_ERRORS):
        raise_connection_error(provider, env_var, exc, endpoint_hint)


def _load_langchain_config() -> dict[str, str | None]:
    """Read [llm] and [llm.langchain] from config.toml via get_config_values().

    Environment variables override config file values:
        MCP_CODER_LLM_LANGCHAIN_BACKEND   -> backend
        MCP_CODER_LLM_LANGCHAIN_MODEL     -> model
        MCP_CODER_LLM_LANGCHAIN_ENDPOINT  -> endpoint
        MCP_CODER_LLM_LANGCHAIN_API_VERSION -> api_version

    API keys are resolved by the vendor env var (OPENAI_API_KEY, GEMINI_API_KEY,
    ANTHROPIC_API_KEY) in each backend module, falling back to config.toml.

    Returns:
        Dict with keys: default_provider, backend, model, api_key, endpoint, api_version.
    """
    raw = get_config_values(
        [
            ("llm", "default_provider", None),
            ("llm.langchain", "backend", None),
            ("llm.langchain", "model", None),
            ("llm.langchain", "api_key", None),
            ("llm.langchain", "endpoint", None),
            ("llm.langchain", "api_version", None),
        ]
    )
    config = {
        "default_provider": raw[("llm", "default_provider")],
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


def _create_chat_model(
    config: dict[str, str | None],
    timeout: int = 30,
) -> BaseChatModel:
    """Dispatch to correct backend's create_*_model() based on config.

    Args:
        config: LangChain configuration dict with backend, model, api_key, etc.
        timeout: Request timeout in seconds.

    Returns:
        Configured BaseChatModel instance for the selected backend.

    Raises:
        ValueError: If the configured backend is not supported.
    """
    backend = config.get("backend")

    if backend == "openai":
        from .openai_backend import create_openai_model

        return create_openai_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
            endpoint=config.get("endpoint"),
            api_version=config.get("api_version"),
            timeout=timeout,
        )
    if backend == "gemini":
        from .gemini_backend import create_gemini_model

        return create_gemini_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
            timeout=timeout,
        )
    if backend == "anthropic":
        from .anthropic_backend import create_anthropic_model

        return create_anthropic_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
            timeout=timeout,
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

    Args:
        question: The user's prompt text.
        session_id: Optional session ID for conversation history.
        timeout: Request timeout in seconds.
        mcp_config: Optional path to .mcp.json for agent mode.
        execution_dir: Optional working directory for agent execution.
        env_vars: Optional environment variables for agent subprocesses.

    Returns:
        LLMResponseDict with the model's response.

    Raises:
        ValueError: If the langchain backend is not configured.
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
        # Agent mode needs a longer timeout than text mode — MCP tool calls
        # involve multiple subprocess round-trips.
        agent_timeout = max(timeout, 300)
        return _ask_agent(
            question=question,
            config=config,
            session_id=sid,
            mcp_config=mcp_config,
            execution_dir=execution_dir,
            env_vars=env_vars,
            timeout=agent_timeout,
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
    """Text-only backend dispatch using unified chat model factory.

    Args:
        question: The user's prompt text.
        config: LangChain configuration dict.
        backend: Backend name ("openai", "gemini", "anthropic").
        session_id: Session ID for conversation history.
        timeout: Request timeout in seconds.

    Returns:
        LLMResponseDict with the model's text response.

    Raises:
        ValueError: If the model is not found on the configured backend.
    """  # Also raises LLMAuthError / LLMConnectionError via _handle_provider_error.
    from langchain_core.messages import HumanMessage, messages_from_dict

    history = load_langchain_history(session_id)
    history_messages = messages_from_dict(history)
    lc_messages = history_messages + [HumanMessage(content=question)]

    ensure_truststore()
    chat_model = _create_chat_model(config, timeout=timeout)

    try:
        ai_msg = chat_model.invoke(lc_messages)
    except Exception as exc:
        _handle_provider_error(exc, backend)
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

    # Serialize history using model_dump() for messages_from_dict() compatibility
    serialized: list[dict[str, Any]] = []
    for msg in list(history_messages) + [HumanMessage(content=question), ai_msg]:
        if hasattr(msg, "model_dump"):
            dump = msg.model_dump()
        else:
            dump = msg.dict()
        msg_type = dump.pop("type", "unknown")
        serialized.append({"type": msg_type, "data": dump})
    store_langchain_history(session_id, serialized)

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=session_id,
        provider="langchain",
        raw_response=raw,
    )


def _get_model_suggestions(config: dict[str, str | None]) -> str:
    """Try to list available models for the configured backend.

    Args:
        config: LangChain configuration dict with backend and api_key.

    Returns:
        Formatted string of available models, or empty string if none found.
    """
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
    """Agent mode: route through LangGraph ReAct agent with MCP tools.

    Args:
        question: The user's prompt text.
        config: LangChain configuration dict.
        session_id: Session ID for conversation history.
        mcp_config: Path to .mcp.json configuration file.
        execution_dir: Optional working directory for agent execution.
        env_vars: Optional environment variables for agent subprocesses.
        timeout: Request timeout in seconds.

    Returns:
        LLMResponseDict with the agent's text response and tool usage stats.

    """  # Also raises LLMAuthError / LLMConnectionError via _handle_provider_error.
    from .agent import _check_agent_dependencies, run_agent

    _check_agent_dependencies()

    ensure_truststore()
    chat_model = _create_chat_model(config, timeout=timeout)
    history: list[dict[str, Any]] = load_langchain_history(session_id)

    agent_backend = config.get("backend")
    try:
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
    except Exception as exc:
        _handle_provider_error(exc, agent_backend)
        raise

    store_langchain_history(session_id, messages)

    raw_response: dict[str, Any] = {
        "messages": messages,
        "backend": config.get("backend", ""),
        "model": config.get("model", ""),
        **stats,
    }

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=session_id,
        provider="langchain",
        raw_response=raw_response,
    )


def _ask_agent_stream(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
) -> Iterator[StreamEvent]:
    """Stream agent events via thread+queue bridge from async to sync.

    Runs ``run_agent_stream()`` in a background thread with ``asyncio.run()``
    and bridges events through a ``queue.Queue``.

    Args:
        question: The user's prompt text.
        config: LangChain configuration dict.
        session_id: Session ID for conversation history.
        mcp_config: Path to .mcp.json configuration file.
        execution_dir: Optional working directory for agent execution.
        env_vars: Optional environment variables for agent subprocesses.
        timeout: Request timeout in seconds.

    Yields:
        StreamEvent dicts from the agent.

    Raises:
        TimeoutError: If no-progress or overall timeout is exceeded.
    """
    from .agent import _check_agent_dependencies, run_agent_stream

    _check_agent_dependencies()
    ensure_truststore()
    chat_model = _create_chat_model(config, timeout=timeout)
    history: list[dict[str, Any]] = load_langchain_history(session_id)

    q: queue.Queue[StreamEvent | None] = queue.Queue()
    error_holder: list[Exception] = []
    cancel = threading.Event()

    async def _run() -> None:
        try:
            async for event in run_agent_stream(
                question=question,
                chat_model=chat_model,
                messages=history,
                mcp_config_path=mcp_config,
                session_id=session_id,
                cancel_event=cancel,
                execution_dir=execution_dir,
                env_vars=env_vars,
            ):
                q.put(event)
        except Exception as exc:  # pylint: disable=broad-except
            error_holder.append(exc)
        finally:
            q.put(None)  # sentinel

    thread = threading.Thread(target=asyncio.run, args=(_run(),), daemon=True)
    thread.start()

    cancelled = False
    start = time.monotonic()

    try:
        while True:
            try:
                event = q.get(timeout=_AGENT_NO_PROGRESS_TIMEOUT)
            except queue.Empty as exc:
                cancel.set()
                raise TimeoutError(
                    f"Agent produced no output for {_AGENT_NO_PROGRESS_TIMEOUT}s"
                ) from exc
            if event is None:
                break
            if time.monotonic() - start > _AGENT_OVERALL_TIMEOUT:
                cancel.set()
                raise TimeoutError(
                    f"Agent execution exceeded {_AGENT_OVERALL_TIMEOUT}s overall timeout"
                )
            yield event
    except GeneratorExit:
        cancel.set()
        cancelled = True
    finally:
        thread.join(timeout=5)

    if error_holder and not cancelled:
        held_exc = error_holder[0]
        _handle_provider_error(held_exc, config.get("backend"))
        raise held_exc


def ask_langchain_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
) -> Iterator[StreamEvent]:
    """Stream LangChain responses as events.

    Same parameters as ask_langchain(). For text mode (no mcp_config),
    routes to _ask_text_stream() for real streaming. For agent mode
    (mcp_config present), routes to _ask_agent_stream() for real
    streaming via thread+queue bridge.

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result, done, error, raw_line

    Raises:
        ValueError: If the langchain backend is not configured.
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
        yield from _ask_agent_stream(
            question=question,
            config=config,
            session_id=sid,
            mcp_config=mcp_config,
            execution_dir=execution_dir,
            env_vars=env_vars,
            timeout=timeout,
        )
        return

    yield from _ask_text_stream(
        question=question,
        config=config,
        backend=backend,
        session_id=sid,
        timeout=timeout,
    )


def _ask_text_stream(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
) -> Iterator[StreamEvent]:
    """Stream text-only responses using chat_model.stream().

    Yields:
        raw_line events for each chunk (JSON serialization),
        text_delta events for each chunk, then done event.

    Raises:
        ValueError: If the model is not found (404/NOT_FOUND in error).
    """
    from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict

    history = load_langchain_history(session_id)
    history_messages = messages_from_dict(history)
    lc_messages = history_messages + [HumanMessage(content=question)]

    ensure_truststore()
    chat_model = _create_chat_model(config, timeout=timeout)

    try:
        all_text_parts: list[str] = []
        for chunk in chat_model.stream(lc_messages):
            chunk_dict = (
                chunk.model_dump() if hasattr(chunk, "model_dump") else chunk.dict()
            )
            yield {"type": "raw_line", "line": json.dumps(chunk_dict)}
            content = (
                chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            )
            yield {"type": "text_delta", "text": content}
            all_text_parts.append(content)

        # Store history with the complete AI response
        full_text = "".join(all_text_parts)
        ai_msg = AIMessage(content=full_text)
        serialized: list[dict[str, Any]] = []
        for msg in list(history_messages) + [
            HumanMessage(content=question),
            ai_msg,
        ]:
            if hasattr(msg, "model_dump"):
                dump = msg.model_dump()
            else:
                dump = msg.dict()
            msg_type = dump.pop("type", "unknown")
            serialized.append({"type": msg_type, "data": dump})
        store_langchain_history(session_id, serialized)

        yield {"type": "done", "session_id": session_id, "usage": {}}
    except Exception as exc:
        _handle_provider_error(exc, backend)
        # Handle 404/model-not-found errors (mirrors _ask_text() path)
        exc_str = str(exc)
        if "404" in exc_str or "not_found" in exc_str.lower() or "NOT_FOUND" in exc_str:
            model = config.get("model", "")
            hint = f"Model {model!r} not found."
            try:
                hint += _get_model_suggestions(config)
            except Exception:  # pylint: disable=broad-except
                pass
            yield {"type": "error", "message": hint}
            raise ValueError(hint) from exc
        yield {"type": "error", "message": str(exc)}
        raise
