"""Pre-flight checks for agent mode (e.g. Ollama tool-capability)."""

from __future__ import annotations

import os


def _ollama_preflight(config: dict[str, str | None]) -> None:
    """Raise ValueError if the configured Ollama model lacks tool support.

    No-op when ``config["backend"] != "ollama"``. The error wording matches
    the ``mcp-coder verify`` output so users see the same message regardless
    of how they hit the check.

    Args:
        config: LangChain configuration dict.

    Raises:
        ValueError: When the model does not advertise the ``tools`` capability.
    """
    if config.get("backend") != "ollama":
        return
    from ._models import check_ollama_tool_capability

    cap = check_ollama_tool_capability(
        model=config.get("model") or "",
        api_key=os.getenv("OLLAMA_API_KEY") or config.get("api_key"),
        endpoint=config.get("endpoint"),
    )
    if not cap["ok"]:
        raise ValueError(cap["value"])
