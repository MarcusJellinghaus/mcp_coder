"""Setup helpers for the LangChain provider.

Turns user config into a ready ``BaseChatModel``, a session id and system
messages, and maps backend exceptions to ``LLMAuthError`` /
``LLMConnectionError``. Every call site lives in the package ``__init__``,
which re-exports these names.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from mcp_coder.llm.storage.session_storage import require_langchain_history
from mcp_coder.utils.user_config import get_config_values

from ._config_diagnostics import validate
from ._exceptions import (
    ANTHROPIC_AUTH_ERRORS,
    CONNECTION_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    OPENAI_AUTH_ERRORS,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)

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
