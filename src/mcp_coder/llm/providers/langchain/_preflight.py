"""Pre-flight checks for agent mode (e.g. Ollama tool-capability)."""

from __future__ import annotations

import os


def _ollama_preflight(config: dict[str, str | None]) -> None:
    """Raise if the Ollama backend cannot run agent mode.

    No-op when ``config["backend"] != "ollama"``. Otherwise verifies the
    ``ollama`` Python client is installed and the configured model
    advertises the ``tools`` capability. The capability-error wording
    matches the ``mcp-coder verify`` output so users see the same message
    regardless of how they hit the check.

    Args:
        config: LangChain configuration dict.

    Raises:
        ImportError: When the ``ollama`` Python client is not installed.
        ValueError: When the model does not advertise the ``tools``
            capability or the daemon is unreachable.
    """
    if config.get("backend") != "ollama":
        return
    try:
        import ollama  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import,import-error
    except ImportError as exc:
        raise ImportError(
            "ollama is required for the Ollama backend.\n"
            "Install with: pip install 'mcp-coder[langchain-ollama]'"
        ) from exc

    from ._models import check_ollama_tool_capability

    cap = check_ollama_tool_capability(
        model=config.get("model") or "",
        api_key=os.getenv("OLLAMA_API_KEY") or config.get("api_key"),
        endpoint=config.get("endpoint"),
    )
    if not cap["ok"]:
        raise ValueError(cap["value"])
