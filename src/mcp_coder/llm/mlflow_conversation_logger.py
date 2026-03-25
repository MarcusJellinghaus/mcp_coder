"""Two-phase MLflow conversation logging context manager.

Provides a context manager that wraps LLM calls with automatic MLflow logging:
- Phase 1 (before yield): starts run, logs prompt artifact (survives timeout/kill)
- Phase 2 (finally): logs response, metrics, artifacts, ends run
"""

import json
import logging
from contextlib import contextmanager
from typing import Any, Generator

from .mlflow_logger import get_mlflow_logger

logger = logging.getLogger(__name__)

__all__ = ["mlflow_conversation"]


@contextmanager
def mlflow_conversation(
    prompt: str,
    provider: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Context manager for two-phase MLflow conversation logging.

    Args:
        prompt: The user prompt text.
        provider: LLM provider name (e.g. "claude", "langchain").
        session_id: Optional session ID for run reuse.
        metadata: Optional metadata dict to log with the conversation.

    Yields:
        Mutable dict with keys ``response_data`` and ``error``.
        Caller should set ``result["response_data"]`` after the LLM call.
    """
    mlflow_logger = get_mlflow_logger()

    if not mlflow_logger._is_enabled():  # noqa: SLF001
        yield {"response_data": None, "error": None}
        return

    # Phase 1: persist prompt immediately (survives timeout/kill)
    is_resuming = session_id is not None and mlflow_logger.has_session(session_id)
    run_name = f"{provider}_{'resuming' if is_resuming else 'new'}"
    mlflow_logger.start_run(
        session_id=session_id, run_name=run_name, tags={"provider": provider}
    )
    mlflow_logger.log_artifact(prompt, "prompt.txt")

    result: dict[str, Any] = {"response_data": None, "error": None}
    try:
        yield result
    except Exception as exc:
        result["error"] = exc
        raise
    finally:
        # Phase 2: log response or error, end run
        try:
            if result["response_data"]:
                mlflow_logger.log_conversation(
                    prompt, result["response_data"], metadata or {}
                )
                # Log tool trace artifact if present (LangChain agent mode)
                tool_trace = (
                    result["response_data"].get("raw_response", {}).get("tool_trace")
                )
                if tool_trace:
                    mlflow_logger.log_artifact(
                        json.dumps(tool_trace, indent=2, default=str),
                        "tool_trace.json",
                    )
                response_sid = result["response_data"].get("session_id")
                mlflow_logger.end_run("FINISHED", session_id=response_sid)
            elif result["error"]:
                mlflow_logger.log_error_metrics(result["error"])
                mlflow_logger.end_run("FAILED", session_id=session_id)
            else:
                mlflow_logger.end_run("KILLED", session_id=session_id)
        except Exception:
            logger.warning("Phase 2 MLflow logging failed", exc_info=True)
