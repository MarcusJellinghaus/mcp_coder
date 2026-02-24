"""Advanced metrics and analytics for MLflow conversation logging.

This module provides enhanced metrics beyond basic duration and cost tracking,
including conversation complexity scoring, topic classification, and trend analysis.
"""

import json
import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

__all__ = [
    "ConversationMetrics",
    "calculate_complexity_score",
    "classify_conversation_topic",
    "extract_performance_metrics",
    "get_error_metrics",
]


class ConversationMetrics:
    """Calculates advanced metrics for conversation analysis."""

    # Common programming keywords for topic classification
    PROGRAMMING_KEYWORDS = {
        "code",
        "function",
        "class",
        "variable",
        "method",
        "api",
        "database",
        "algorithm",
        "debug",
        "test",
        "bug",
        "error",
        "exception",
        "import",
        "library",
        "framework",
        "syntax",
        "compile",
        "deploy",
        "git",
        "commit",
        "merge",
        "branch",
        "repository",
        "docker",
        "kubernetes",
        "aws",
        "cloud",
    }

    # File operation keywords
    FILE_KEYWORDS = {
        "file",
        "directory",
        "folder",
        "path",
        "read",
        "write",
        "save",
        "load",
        "copy",
        "move",
        "delete",
        "create",
        "edit",
        "modify",
        "search",
        "find",
    }

    # Configuration and setup keywords
    CONFIG_KEYWORDS = {
        "config",
        "configuration",
        "setup",
        "install",
        "dependency",
        "package",
        "environment",
        "settings",
        "properties",
        "yaml",
        "json",
        "toml",
        "xml",
    }

    # Documentation and help keywords
    DOCS_KEYWORDS = {
        "documentation",
        "docs",
        "readme",
        "guide",
        "tutorial",
        "help",
        "explain",
        "how to",
        "what is",
        "example",
        "usage",
        "manual",
        "reference",
    }

    def __init__(self) -> None:
        self.complexity_factors = {
            "prompt_length": 0.2,
            "code_blocks": 0.3,
            "file_operations": 0.2,
            "tool_calls": 0.15,
            "error_handling": 0.1,
            "multi_step": 0.05,
        }

    def calculate_complexity_score(
        self, prompt: str, response_data: Dict[str, Any]
    ) -> float:
        """Calculate conversation complexity score (0-100).

        Args:
            prompt: User prompt text
            response_data: LLM response data

        Returns:
            Complexity score from 0 (simple) to 100 (very complex)
        """
        try:
            score = 0.0

            # Prompt length factor (0-20 points)
            prompt_length = len(prompt)
            if prompt_length > 1000:
                score += 20
            elif prompt_length > 500:
                score += 15
            elif prompt_length > 200:
                score += 10
            elif prompt_length > 100:
                score += 5

            # Code block detection (0-30 points)
            code_blocks = self._count_code_blocks(prompt)
            if code_blocks > 3:
                score += 30
            elif code_blocks > 1:
                score += 20
            elif code_blocks > 0:
                score += 10

            # File operation complexity (0-20 points)
            file_ops = self._count_file_operations(prompt)
            if file_ops > 5:
                score += 20
            elif file_ops > 2:
                score += 15
            elif file_ops > 0:
                score += 10

            # Tool usage complexity (0-15 points)
            raw_response = response_data.get("raw_response", {})
            if isinstance(raw_response, dict):
                session_info = raw_response.get("session_info", {})
                if isinstance(session_info, dict):
                    usage = session_info.get("usage", {})
                    if isinstance(usage, dict):
                        tool_calls = usage.get(
                            "cache_read_input_tokens", 0
                        ) + usage.get("tool_use_tokens", 0)
                        if tool_calls > 1000:
                            score += 15
                        elif tool_calls > 500:
                            score += 10
                        elif tool_calls > 100:
                            score += 5

            # Error handling complexity (0-10 points)
            if self._has_error_handling(prompt):
                score += 10

            # Multi-step task detection (0-5 points)
            if self._is_multi_step_task(prompt):
                score += 5

            return min(score, 100.0)  # Cap at 100

        except Exception as e:
            logger.warning(f"Failed to calculate complexity score: {e}")
            return 50.0  # Default medium complexity

    def classify_conversation_topic(self, prompt: str) -> str:
        """Classify conversation topic based on content analysis.

        Args:
            prompt: User prompt text

        Returns:
            Topic category string
        """
        try:
            prompt_lower = prompt.lower()

            # Count keyword matches for each category
            programming_score = sum(
                1 for kw in self.PROGRAMMING_KEYWORDS if kw in prompt_lower
            )
            file_score = sum(1 for kw in self.FILE_KEYWORDS if kw in prompt_lower)
            config_score = sum(1 for kw in self.CONFIG_KEYWORDS if kw in prompt_lower)
            docs_score = sum(1 for kw in self.DOCS_KEYWORDS if kw in prompt_lower)

            # Determine primary topic
            scores = {
                "programming": programming_score,
                "file_operations": file_score,
                "configuration": config_score,
                "documentation": docs_score,
            }

            primary_topic = max(scores, key=scores.get)

            # Additional specific classifications
            if (
                "error" in prompt_lower
                or "bug" in prompt_lower
                or "fix" in prompt_lower
            ):
                return "debugging"
            elif "test" in prompt_lower and programming_score > 0:
                return "testing"
            elif "deploy" in prompt_lower or "build" in prompt_lower:
                return "deployment"
            elif "git" in prompt_lower or "commit" in prompt_lower:
                return "version_control"
            elif any(
                word in prompt_lower for word in ["help", "how", "what", "explain"]
            ):
                return "support"

            # Return primary topic if score is significant
            if scores[primary_topic] >= 2:
                return primary_topic

            # Default classification
            if len(prompt) > 200:
                return "complex_query"
            else:
                return "general"

        except Exception as e:
            logger.warning(f"Failed to classify conversation topic: {e}")
            return "unknown"

    def extract_performance_metrics(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract performance-related metrics from response data.

        Args:
            response_data: LLM response data

        Returns:
            Dictionary of performance metrics
        """
        metrics = {}

        try:
            # Basic timing metrics
            if "duration_ms" in response_data:
                duration = float(response_data["duration_ms"])
                metrics["duration_seconds"] = duration / 1000
                metrics["duration_minutes"] = duration / 60000

                # Performance categories
                if duration < 5000:  # < 5 seconds
                    metrics["performance_category"] = 1.0  # Fast
                elif duration < 30000:  # < 30 seconds
                    metrics["performance_category"] = 2.0  # Medium
                elif duration < 120000:  # < 2 minutes
                    metrics["performance_category"] = 3.0  # Slow
                else:
                    metrics["performance_category"] = 4.0  # Very slow

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
    ) -> Dict[str, Any]:
        """Extract error-related metrics.

        Args:
            error: Exception that occurred (if any)
            duration_ms: Duration before error occurred

        Returns:
            Dictionary of error metrics
        """
        metrics = {}

        try:
            if error is not None:
                metrics["has_error"] = 1.0
                metrics["error_type"] = type(error).__name__

                # Error severity classification
                error_name = type(error).__name__.lower()
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

    def _count_code_blocks(self, text: str) -> int:
        """Count code blocks in text (markdown format)."""
        return len(re.findall(r"```[\s\S]*?```", text))

    def _count_file_operations(self, text: str) -> int:
        """Count file operation keywords in text."""
        text_lower = text.lower()
        return sum(1 for keyword in self.FILE_KEYWORDS if keyword in text_lower)

    def _has_error_handling(self, text: str) -> bool:
        """Check if text mentions error handling concepts."""
        error_keywords = [
            "try",
            "catch",
            "exception",
            "error",
            "handle",
            "fix",
            "debug",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in error_keywords)

    def _is_multi_step_task(self, text: str) -> bool:
        """Check if text describes a multi-step task."""
        step_indicators = [
            "step",
            "first",
            "then",
            "next",
            "finally",
            "after",
            "before",
        ]
        text_lower = text.lower()
        step_count = sum(1 for indicator in step_indicators if indicator in text_lower)
        return step_count >= 2 or len(text.split(".")) > 3


# Convenience functions for direct use
def calculate_complexity_score(prompt: str, response_data: Dict[str, Any]) -> float:
    """Calculate conversation complexity score."""
    metrics = ConversationMetrics()
    return metrics.calculate_complexity_score(prompt, response_data)


def classify_conversation_topic(prompt: str) -> str:
    """Classify conversation topic."""
    metrics = ConversationMetrics()
    return metrics.classify_conversation_topic(prompt)


def extract_performance_metrics(response_data: Dict[str, Any]) -> Dict[str, float]:
    """Extract performance metrics."""
    metrics = ConversationMetrics()
    return metrics.extract_performance_metrics(response_data)


def get_error_metrics(
    error: Optional[Exception], duration_ms: Optional[int]
) -> Dict[str, Any]:
    """Get error metrics."""
    metrics = ConversationMetrics()
    return metrics.get_error_metrics(error, duration_ms)
