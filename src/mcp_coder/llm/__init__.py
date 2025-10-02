"""LLM functionality - provider interfaces, formatting, and session management.

This package consolidates all LLM-related functionality including:
- Provider interfaces (Claude, future providers)
- Response formatting (text, verbose, raw)
- Session management (storage, finding, resolution)
- Type definitions and serialization
"""

from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict

__all__ = [
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
]
