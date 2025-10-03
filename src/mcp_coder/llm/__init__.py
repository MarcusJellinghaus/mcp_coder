"""LLM functionality - provider interfaces, formatting, and session management.

This package consolidates all LLM-related functionality including:
- Provider interfaces (Claude, future providers)
- Response formatting (text, verbose, raw)
- Session management (storage, finding, resolution)
- Type definitions and serialization
"""

from mcp_coder.llm.interface import ask_llm, prompt_llm
from mcp_coder.llm.serialization import (
    deserialize_llm_response,
    from_json_string,
    serialize_llm_response,
    to_json_string,
)
from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict

__all__ = [
    "ask_llm",
    "prompt_llm",
    "serialize_llm_response",
    "deserialize_llm_response",
    "to_json_string",
    "from_json_string",
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
]
