"""Test llm package structure and imports."""

import pytest


def test_llm_package_structure() -> None:
    """Verify llm package structure and imports."""
    import mcp_coder.llm
    import mcp_coder.llm.interface
    import mcp_coder.llm.serialization
    import mcp_coder.llm.types

    # Verify public API available
    assert hasattr(mcp_coder.llm, "ask_llm")
    assert hasattr(mcp_coder.llm, "prompt_llm")
    assert hasattr(mcp_coder.llm, "LLMResponseDict")


def test_public_api_exports() -> None:
    """Verify public API exports work."""
    from mcp_coder.llm import (
        LLMResponseDict,
        ask_llm,
        prompt_llm,
        serialize_llm_response,
    )

    assert callable(ask_llm)
    assert callable(prompt_llm)
    assert callable(serialize_llm_response)


def test_type_imports() -> None:
    """Verify type imports from llm.types."""
    from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict

    assert LLM_RESPONSE_VERSION is not None
    assert LLMResponseDict is not None


def test_interface_imports() -> None:
    """Verify interface imports from llm.interface."""
    from mcp_coder.llm.interface import ask_llm, prompt_llm

    assert callable(ask_llm)
    assert callable(prompt_llm)


def test_serialization_imports() -> None:
    """Verify serialization imports from llm.serialization."""
    from mcp_coder.llm.serialization import (
        deserialize_llm_response,
        from_json_string,
        serialize_llm_response,
        to_json_string,
    )

    assert callable(serialize_llm_response)
    assert callable(deserialize_llm_response)
    assert callable(to_json_string)
    assert callable(from_json_string)


def test_all_exports_present() -> None:
    """Verify __all__ exports are complete."""
    import mcp_coder.llm

    expected_exports = [
        "ask_llm",
        "prompt_llm",
        "serialize_llm_response",
        "deserialize_llm_response",
        "to_json_string",
        "from_json_string",
        "LLMResponseDict",
        "LLM_RESPONSE_VERSION",
    ]

    for export in expected_exports:
        assert hasattr(mcp_coder.llm, export), f"Missing export: {export}"
