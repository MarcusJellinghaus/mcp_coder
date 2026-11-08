"""Read the LangChain config from mcp-coder's config.toml (outside the model layer)."""

from __future__ import annotations

import logging
from typing import Any

from mcp_coder.utils.user_config import get_config_values

logger = logging.getLogger(__name__)


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
