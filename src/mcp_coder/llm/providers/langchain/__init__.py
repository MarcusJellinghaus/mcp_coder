"""LangChain provider package.

Entry point for the LangChain provider. Supports OpenAI, Gemini, and Anthropic backends.
All LangChain library imports are deferred to the backend modules so that
importing this package does not fail when langchain is not installed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
import time
import uuid
from collections.abc import Iterator, Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mcp_coder.llm.storage.session_storage import (
    langchain_history_exists,
    load_langchain_history,
    require_langchain_history,
    store_langchain_history,
)
from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict, StreamEvent
from mcp_coder.utils.user_config import get_config_values

from ._config_diagnostics import dialed_url, validate
from ._errors_404 import _format_404_hint
from ._errors_404 import _is_404_error as _is_404_error  # re-exported for tests
from ._exceptions import (
    ANTHROPIC_AUTH_ERRORS,
    CONNECTION_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    OPENAI_AUTH_ERRORS,
    LLMMCPLaunchError,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)
from ._messages import assemble_messages, serialize_messages
from ._preflight import _ollama_preflight
from ._usage import _extract_usage

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


logger = logging.getLogger(__name__)


def _build_system_messages(
    system_prompt: str | None, project_prompt: str | None
) -> list[Any]:
    r"""Merge optional prompt strings into a single SystemMessage.

    Both prompts are joined with a blank line ("\n\n") so that providers
    accepting only one system message still receive the full instructions.

    Args:
        system_prompt: Optional system-level prompt text.
        project_prompt: Optional project-level prompt text.

    Returns:
        List with at most one merged SystemMessage (may be empty).
    """
    from langchain_core.messages import SystemMessage

    parts = [p for p in (system_prompt, project_prompt) if p]
    if not parts:
        return []
    return [SystemMessage(content="\n\n".join(parts))]


# Agent streaming timeout constants (seconds)
_AGENT_OVERALL_TIMEOUT = 3600  # 60 minutes

_BACKEND_ERROR_PARAMS: dict[str, tuple[str, str, str]] = {
    # (provider_label, env_var, base_url_hint)
    "openai": (
        "OpenAI",
        "OPENAI_API_KEY",
        "base_url if using a custom server",
    ),
    "gemini": ("Gemini", "GEMINI_API_KEY", ""),
    "anthropic": ("Anthropic", "ANTHROPIC_API_KEY", ""),
    "ollama": (
        "Ollama",
        "OLLAMA_API_KEY",
        "base_url/OLLAMA_HOST if not localhost",
    ),
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


def _handle_provider_error(
    exc: Exception, backend: str | None, dialed: str | None = None
) -> None:
    """Raise LLMAuthError or LLMConnectionError when *exc* matches, else return.

    Args:
        exc: The caught exception.
        backend: Backend name ("openai", "gemini", "anthropic", or None).
        dialed: The URL the constructed client actually dials, when known.
            Callers read it off the client with :func:`dialed_url`, never from
            config — a config-derived value is wrong the moment OPENAI_BASE_URL
            or OLLAMA_HOST redirects the request, which is exactly the case a
            connection error needs to expose. It is reported *alongside* the
            static per-backend hint, never instead of it: the hint names the
            key and env var to change, which the dialed URL cannot. Left at
            None the message is byte-identical to before.
    """
    auth_errors = _auth_errors_for_backend(backend)
    provider, env_var, base_url_hint = _BACKEND_ERROR_PARAMS.get(
        backend or "", (backend or "", "", "")
    )
    if auth_errors and isinstance(exc, auth_errors):
        if backend == "gemini" and not is_google_auth_error(exc):
            raise_connection_error(provider, env_var, exc, base_url_hint, dialed)
        raise_auth_error(provider, env_var, exc)
    if isinstance(exc, CONNECTION_ERRORS):
        raise_connection_error(provider, env_var, exc, base_url_hint, dialed)


def _load_langchain_config() -> dict[str, str | None]:
    """Read [llm] and [llm.langchain] from config.toml. Never raises.

    Environment variable overrides (e.g. MCP_CODER_LLM_LANGCHAIN_BACKEND) are
    handled automatically by get_config_values() through the config schema.

    API keys are resolved by the vendor env var (OPENAI_API_KEY, GEMINI_API_KEY,
    ANTHROPIC_API_KEY) in each backend module, falling back to config.toml.

    A schema type mismatch (e.g. ``model = 123``) makes get_config_values()
    raise ValueError. This loader runs on *every* ``mcp-coder verify``, including
    for claude users who never configured langchain, so it degrades every value
    to None instead — verify_config() already reports the mismatch as a CONFIG
    error one section earlier, so re-reporting here would only duplicate it.
    Validation of the resulting values happens at the point of use, not here.

    Returns:
        Dict with keys: default_provider, backend, model, api_key, base_url, api_version.
        Every value is None when the config could not be read.
    """
    raw: dict[tuple[str, str], str | bool | int | list[Any] | None]
    try:
        raw = get_config_values(
            [
                ("llm", "default_provider", None),
                ("llm.langchain", "backend", None),
                ("llm.langchain", "model", None),
                ("llm.langchain", "api_key", None),
                ("llm.langchain", "base_url", None),
                ("llm.langchain", "api_version", None),
            ]
        )
    except ValueError:
        logger.warning(
            "Ignoring [llm.langchain] config: schema type mismatch "
            "(see the CONFIG section of `mcp-coder verify`)."
        )
        raw = {}

    # All langchain fields are str type in schema — narrow from the wider union
    def _str_or_none(val: str | bool | int | list[Any] | None) -> str | None:
        return val if isinstance(val, str) else None

    return {
        "default_provider": _str_or_none(raw.get(("llm", "default_provider"))),
        "backend": _str_or_none(raw.get(("llm.langchain", "backend"))),
        "model": _str_or_none(raw.get(("llm.langchain", "model"))),
        "api_key": _str_or_none(raw.get(("llm.langchain", "api_key"))),
        "base_url": _str_or_none(raw.get(("llm.langchain", "base_url"))),
        "api_version": _str_or_none(raw.get(("llm.langchain", "api_version"))),
    }


def _create_chat_model(
    config: Mapping[str, str | None],
    timeout: int = 30,
) -> BaseChatModel:
    """Dispatch to correct backend's create_*_model() based on config.

    The per-backend contract is checked here, before the dispatch, so that all
    four provider paths (text, text-stream, agent, agent-stream) are covered by
    a single site and the user gets an actionable message instead of the SDK's
    opaque one.

    Args:
        config: LangChain configuration dict with backend, model, api_key, etc.
        timeout: Request timeout in seconds.

    Returns:
        Configured BaseChatModel instance for the selected backend.

    Raises:
        ValueError: If the config violates the per-backend contract, including
            an unsupported or unset backend.
    """
    for finding in validate(config):
        if finding["ok"] is False:
            raise ValueError(finding["value"])

    backend = config.get("backend")

    if backend == "openai":
        from .openai_backend import create_openai_model

        return create_openai_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
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
    if backend == "ollama":
        from .ollama_backend import create_ollama_model

        return create_ollama_model(
            model=config.get("model") or "",
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
            timeout=timeout,
        )
    raise ValueError(
        f"Unsupported langchain backend: {backend!r}. "
        "Supported backends: 'openai', 'gemini', 'anthropic', 'ollama'."
    )


def _resolve_session_id(session_id: str | None) -> str:
    """Return the session id to use, validating an explicitly requested one.

    Args:
        session_id: Id the caller asked to resume, or None for a new session.

    Returns:
        The requested id, or a freshly minted UUID when none was requested.
    """  # Also raises ValueError via require_langchain_history for an unknown id.
    if not session_id:
        return str(uuid.uuid4())
    require_langchain_history(session_id)
    return session_id


def ask_langchain(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    system_prompt: str | None = None,
    project_prompt: str | None = None,
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
        system_prompt: Optional system-level prompt text.
        project_prompt: Optional project-level prompt text.

    Returns:
        LLMResponseDict with the model's response.

    Raises:
        ValueError: If the langchain backend is not configured, or if
            *session_id* was supplied but has no history file.
    """
    config = _load_langchain_config()
    backend = config["backend"]

    if not backend:
        raise ValueError(
            "llm.langchain.backend not configured. "
            "Set [llm.langchain] backend in config.toml "
            "or MCP_CODER_LLM_LANGCHAIN_BACKEND env var."
        )

    sid = _resolve_session_id(session_id)
    sys_msgs = _build_system_messages(system_prompt, project_prompt)

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
            system_messages=sys_msgs,
        )

    return _ask_text(
        question=question,
        config=config,
        backend=backend,
        session_id=sid,
        timeout=timeout,
        system_messages=sys_msgs,
    )


def _ask_text(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
    system_messages: list[Any] | None = None,
) -> LLMResponseDict:
    """Text-only backend dispatch using unified chat model factory.

    Args:
        question: The user's prompt text.
        config: LangChain configuration dict.
        backend: Backend name ("openai", "gemini", "anthropic").
        session_id: Session ID for conversation history.
        timeout: Request timeout in seconds.
        system_messages: Optional list of system messages to prepend.

    Returns:
        LLMResponseDict with the model's text response.

    Raises:
        ValueError: If the model is not found on the configured backend.
    """  # Also raises LLMAuthError / LLMConnectionError via _handle_provider_error.
    history = load_langchain_history(session_id)
    lc_messages = assemble_messages(system_messages, history, question)

    chat_model = _create_chat_model(config, timeout=timeout)

    try:
        ai_msg = chat_model.invoke(lc_messages)
    except Exception as exc:
        _handle_provider_error(exc, backend, dialed_url(chat_model))
        if _is_404_error(exc):
            raise ValueError(_format_404_hint(config)) from exc
        raise

    text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    raw: dict[str, object] = {
        "backend": backend,
        "model": config.get("model", ""),
        "response_content": text,
        "usage": _extract_usage(ai_msg),
    }

    store_langchain_history(session_id, serialize_messages(lc_messages + [ai_msg]))

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=session_id,
        provider="langchain",
        raw_response=raw,
    )


def _ask_agent(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
    system_messages: list[Any] | None = None,
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
        system_messages: Optional list of system messages to prepend.

    Returns:
        LLMResponseDict with the agent's text response and tool usage stats.
        ``session_id`` is None when the turn stored nothing: an id no history
        was written under is not resumable and would fail the next turn.
    """  # Also raises LLMAuthError / LLMConnectionError via _handle_provider_error.
    from .agent import _check_agent_dependencies, run_agent

    _check_agent_dependencies()
    _ollama_preflight(config)

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
                session_id=session_id,
                execution_dir=execution_dir,
                env_vars=env_vars,
                timeout=timeout,
                system_messages=system_messages,
            )
        )
    except Exception as exc:
        _handle_provider_error(exc, agent_backend, dialed_url(chat_model))
        raise

    # No storage here: run_agent drains run_agent_stream, which is the single
    # persistence site for the agent path.
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
        session_id=session_id if langchain_history_exists(session_id) else None,
        provider="langchain",
        raw_response=raw_response,
    )


#: ``done`` keys that exist only for the in-process drainer of
#: ``run_agent_stream`` and must not cross the provider boundary.
_INTERNAL_DONE_KEYS = ("messages", "stats")


def _strip_internal_done_keys(event: StreamEvent) -> StreamEvent:
    """Return *event* without the drainer-only ``done`` keys.

    ``done["messages"]`` is the whole serialized conversation and
    ``done["stats"]["tool_trace"]`` repeats every tool call's name/args/result.
    Both are consumed only by the in-process drainer, which reads
    ``run_agent_stream`` directly; every consumer above this boundary instead
    *persists* the event — into ``raw_response["events"]`` via
    ``ResponseAssembler`` and into the icoder JSONL event log via
    ``AppCore.stream_llm`` — so leaving ``messages`` on would grow both sinks
    quadratically with turn count. Stripping both here, once, is what keeps
    those consumers free of their own filters.

    ``result`` is deliberately *not* stripped: ``ResponseAssembler`` uses it as
    the response text when no ``text_delta`` was seen.

    Args:
        event: A stream event from ``run_agent_stream``.

    Returns:
        Non-``done`` events unchanged; ``done`` events as a shallow copy
        without the internal keys.
    """
    if event.get("type") != "done":
        return event
    return {k: v for k, v in event.items() if k not in _INTERNAL_DONE_KEYS}


def _ask_agent_stream(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
    tools: list[Any] | None = None,
    system_messages: list[Any] | None = None,
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
        tools: Optional pre-built LangChain tools (e.g. from MCPManager).
            When provided, skips MultiServerMCPClient creation.
        system_messages: Optional list of system messages to prepend.

    Yields:
        StreamEvent dicts from the agent.

    Raises:
        TimeoutError: If no-progress or overall timeout is exceeded.
    """
    from .agent import _check_agent_dependencies, run_agent_stream

    _check_agent_dependencies()
    _ollama_preflight(config)
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
                tools=tools,
                system_messages=system_messages,
            ):
                q.put(_strip_internal_done_keys(event))
        except Exception as exc:  # pylint: disable=broad-except
            error_holder.append(exc)
        finally:
            q.put(None)  # sentinel

    def _thread_main() -> None:
        asyncio.run(_run())

    thread = threading.Thread(target=_thread_main, daemon=True)
    thread.start()

    cancelled = False
    start = time.monotonic()

    try:
        while True:
            try:
                event = q.get(timeout=timeout)
            except queue.Empty as exc:
                cancel.set()
                raise TimeoutError(
                    f"LLM inactivity timeout (langchain): no response for {timeout}s. "
                    "Connection closed. You can retry, or use --timeout to increase the limit."
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

    # If the async thread raised an exception but the consumer exited
    # normally (sentinel received), re-raise that error. Skipped when
    # cancelled (GeneratorExit) to avoid masking the exit.
    if error_holder and not cancelled:
        held_exc = error_holder[0]
        _handle_provider_error(held_exc, config.get("backend"), dialed_url(chat_model))
        raise held_exc


def ask_langchain_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 600,
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    tools: list[Any] | None = None,
    system_prompt: str | None = None,
    project_prompt: str | None = None,
) -> Iterator[StreamEvent]:
    """Stream LangChain responses as events.

    Same parameters as ask_langchain(). For text mode (no mcp_config),
    routes to _ask_text_stream() for real streaming. For agent mode
    (mcp_config present), routes to _ask_agent_stream() for real
    streaming via thread+queue bridge.

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result, done, error, raw_line

    Raises:
        ValueError: If the langchain backend is not configured, or if
            *session_id* was supplied but has no history file.
    """
    config = _load_langchain_config()
    backend = config["backend"]

    if not backend:
        raise ValueError(
            "llm.langchain.backend not configured. "
            "Set [llm.langchain] backend in config.toml "
            "or MCP_CODER_LLM_LANGCHAIN_BACKEND env var."
        )

    sid = _resolve_session_id(session_id)
    sys_msgs = _build_system_messages(system_prompt, project_prompt)

    if mcp_config:
        yield from _ask_agent_stream(
            question=question,
            config=config,
            session_id=sid,
            mcp_config=mcp_config,
            execution_dir=execution_dir,
            env_vars=env_vars,
            timeout=timeout,
            tools=tools,
            system_messages=sys_msgs,
        )
        return

    yield from _ask_text_stream(
        question=question,
        config=config,
        backend=backend,
        session_id=sid,
        timeout=timeout,
        system_messages=sys_msgs,
    )


def _ask_text_stream(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
    system_messages: list[Any] | None = None,
) -> Iterator[StreamEvent]:
    """Stream text-only responses using chat_model.stream().

    Yields:
        raw_line events for each chunk (JSON serialization),
        text_delta events for each chunk, then done event.

    Raises:
        ValueError: If the model is not found (404/NOT_FOUND in error).
        TimeoutError: If no LLM output is received within the timeout period.
    """
    from langchain_core.messages import AIMessage

    history = load_langchain_history(session_id)
    lc_messages = assemble_messages(system_messages, history, question)

    chat_model = _create_chat_model(config, timeout=timeout)

    try:
        all_text_parts: list[str] = []
        last_chunk_with_usage: Any = None
        last_activity = time.time()
        for chunk in chat_model.stream(lc_messages):
            if time.time() - last_activity > timeout:
                raise TimeoutError(
                    f"LLM inactivity timeout (langchain): no output for {timeout}s. "
                    "Stream stalled. You can retry, or use --timeout to increase the limit."
                )
            last_activity = time.time()
            if getattr(chunk, "usage_metadata", None):
                last_chunk_with_usage = chunk
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
        store_langchain_history(session_id, serialize_messages(lc_messages + [ai_msg]))

        usage = _extract_usage(last_chunk_with_usage) if last_chunk_with_usage else {}
        yield {"type": "done", "session_id": session_id, "usage": usage}
    except TimeoutError:
        raise
    except Exception as exc:
        _handle_provider_error(exc, backend, dialed_url(chat_model))
        # Handle 404/model-not-found errors (mirrors _ask_text() path)
        if _is_404_error(exc):
            hint = _format_404_hint(config)
            yield {"type": "error", "message": hint}
            raise ValueError(hint) from exc
        yield {"type": "error", "message": str(exc)}
        raise
