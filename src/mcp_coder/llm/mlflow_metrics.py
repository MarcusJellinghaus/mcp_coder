"""Performance metrics for MLflow conversation logging.

This module provides objective performance metrics for LLM conversations,
focusing on measurable, actionable data like duration, cost, and token usage.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

__all__ = [
    "ConversationMetrics",
    "extract_performance_metrics",
    "get_error_metrics",
]


class ConversationMetrics:
    """Calculates objective performance metrics for conversation analysis."""

    def extract_performance_metrics(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract performance-related metrics from response data.

        Args:
            response_data: LLM response data

        Returns:
            Dictionary of performance metrics including:
            - Duration (seconds, minutes)
            - Cost (USD)
            - Token usage (input, output, total)
            - Cost efficiency (tokens per dollar, cost per thousand tokens)
            - Cache hit ratio
        """
        metrics = {}

        try:
            # Basic timing metrics
            if "duration_ms" in response_data:
                duration = float(response_data["duration_ms"])
                metrics["duration_seconds"] = duration / 1000
                metrics["duration_minutes"] = duration / 60000

            # Cost metrics
            if "cost_usd" in response_data:
                cost = float(response_data["cost_usd"])
                metrics["cost_usd"] = cost

                # Cost efficiency (tokens per dollar, if available)
                raw_response = response_data.get("raw_response", {})
                if isinstance(raw_response, dict):
                    session_info = raw_response.get("session_info", {})
                    if isinstance(session_info, dict):
                        usage = session_info.get("usage", {})
                        if isinstance(usage, dict):
                            total_tokens = usage.get("input_tokens", 0) + usage.get(
                                "output_tokens", 0
                            )
                            if cost > 0 and total_tokens > 0:
                                metrics["tokens_per_dollar"] = total_tokens / cost
                                metrics["cost_per_thousand_tokens"] = (
                                    cost / total_tokens
                                ) * 1000

            # Token usage metrics
            raw_response = response_data.get("raw_response", {})
            if isinstance(raw_response, dict):
                session_info = raw_response.get("session_info", {})
                if isinstance(session_info, dict):
                    usage = session_info.get("usage", {})
                    if isinstance(usage, dict):
                        metrics["input_tokens"] = float(usage.get("input_tokens", 0))
                        metrics["output_tokens"] = float(usage.get("output_tokens", 0))
                        metrics["total_tokens"] = (
                            metrics["input_tokens"] + metrics["output_tokens"]
                        )

                        # Token efficiency
                        if metrics["input_tokens"] > 0:
                            metrics["output_input_ratio"] = (
                                metrics["output_tokens"] / metrics["input_tokens"]
                            )

                        # Cache usage
                        cache_tokens = usage.get("cache_read_input_tokens", 0)
                        if cache_tokens > 0:
                            metrics["cache_tokens"] = float(cache_tokens)
                            metrics["cache_hit_ratio"] = (
                                cache_tokens / metrics["input_tokens"]
                                if metrics["input_tokens"] > 0
                                else 0
                            )

        except Exception as e:
            logger.warning(f"Failed to extract performance metrics: {e}")

        return metrics

    def get_error_metrics(
        self, error: Optional[Exception], duration_ms: Optional[int]
    ) -> Dict[str, float]:
        """Extract error-related metrics.

        Args:
            error: Exception that occurred (if any)
            duration_ms: Duration before error occurred

        Returns:
            Dictionary of error metrics including:
            - has_error (0.0 or 1.0)
            - error_type_code (numeric classification)
            - error_severity (1.0=low, 2.0=medium, 3.0=high)
            - time_to_error_ms, time_to_error_seconds
            - failure_speed (1.0=fast, 2.0=slow)
        """
        metrics: Dict[str, float] = {}

        try:
            if error is not None:
                metrics["has_error"] = 1.0

                # Numeric error type classification
                error_name = type(error).__name__.lower()
                if "timeout" in error_name or "connection" in error_name:
                    metrics["error_type_code"] = 1.0  # Network/timeout errors
                elif "permission" in error_name or "auth" in error_name:
                    metrics["error_type_code"] = 2.0  # Permission errors
                elif "value" in error_name or "type" in error_name:
                    metrics["error_type_code"] = 3.0  # Data/type errors
                else:
                    metrics["error_type_code"] = 0.0  # Unknown/other errors

                # Error severity classification
                if any(
                    word in error_name for word in ["timeout", "connection", "network"]
                ):
                    metrics["error_severity"] = 2.0  # Medium - infrastructure
                elif any(
                    word in error_name for word in ["permission", "auth", "access"]
                ):
                    metrics["error_severity"] = 2.0  # Medium - auth/permission
                elif any(
                    word in error_name for word in ["value", "type", "attribute", "key"]
                ):
                    metrics["error_severity"] = 1.0  # Low - data/code issues
                else:
                    metrics["error_severity"] = 3.0  # High - unknown/critical

                # Time to error
                if duration_ms is not None:
                    metrics["time_to_error_ms"] = float(duration_ms)
                    metrics["time_to_error_seconds"] = float(duration_ms) / 1000

                    # Quick failure vs slow failure
                    if duration_ms < 5000:  # < 5 seconds
                        metrics["failure_speed"] = 1.0  # Fast failure
                    else:
                        metrics["failure_speed"] = 2.0  # Slow failure
            else:
                metrics["has_error"] = 0.0

        except Exception as e:
            logger.warning(f"Failed to extract error metrics: {e}")
            metrics["has_error"] = 0.0

        return metrics


# Convenience functions for direct use
def extract_performance_metrics(response_data: Dict[str, Any]) -> Dict[str, float]:
    """Extract performance metrics.

    Returns:
        Dictionary of performance metrics.
    """
    metrics = ConversationMetrics()
    return metrics.extract_performance_metrics(response_data)


def get_error_metrics(
    error: Optional[Exception], duration_ms: Optional[int]
) -> Dict[str, float]:
    """Get error metrics.

    Returns:
        Dictionary of error metrics.
    """
    metrics = ConversationMetrics()
    return metrics.get_error_metrics(error, duration_ms)
