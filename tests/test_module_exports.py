"""Tests for module-level exports."""

import pytest


def test_ask_llm_exported_from_main_module() -> None:
    """Test that ask_llm can be imported from main module."""
    from mcp_coder import ask_llm

    assert callable(ask_llm)


def test_prompt_llm_exported_from_main_module() -> None:
    """Test that prompt_llm can be imported from main module."""
    from mcp_coder import prompt_llm

    assert callable(prompt_llm)


def test_serialization_functions_exported() -> None:
    """Test that serialization functions are exported."""
    from mcp_coder import deserialize_llm_response, serialize_llm_response

    assert callable(serialize_llm_response)
    assert callable(deserialize_llm_response)


def test_llm_types_exported() -> None:
    """Test that LLM types are exported."""
    from mcp_coder import LLM_RESPONSE_VERSION, LLMResponseDict

    assert LLMResponseDict is not None
    assert isinstance(LLM_RESPONSE_VERSION, str)


def test_all_contains_new_exports() -> None:
    """Test that __all__ includes new exports."""
    import mcp_coder

    required_exports = [
        "ask_llm",
        "prompt_llm",
        "serialize_llm_response",
        "deserialize_llm_response",
        "LLMResponseDict",
        "LLM_RESPONSE_VERSION",
    ]

    for export in required_exports:
        assert export in mcp_coder.__all__, f"{export} not in __all__"


def test_llm_interface_all_is_correct() -> None:
    """Test that llm.interface module exports correct items."""
    from mcp_coder.llm import interface

    expected = [
        "ask_llm",
        "prompt_llm",
    ]

    assert set(interface.__all__) == set(expected)


def test_llm_types_all_is_correct() -> None:
    """Test that llm.types module exports correct items."""
    from mcp_coder.llm import types

    expected = [
        "LLMResponseDict",
        "LLM_RESPONSE_VERSION",
    ]

    assert set(types.__all__) == set(expected)


def test_llm_serialization_all_is_correct() -> None:
    """Test that llm.serialization module exports correct items."""
    from mcp_coder.llm import serialization

    expected = [
        "to_json_string",
        "from_json_string",
        "serialize_llm_response",
        "deserialize_llm_response",
    ]

    assert set(serialization.__all__) == set(expected)


def test_import_all_from_mcp_coder() -> None:
    """Test that star import works correctly."""
    # Note: This is mainly for documentation, not recommended in practice
    import mcp_coder

    # Check that new functions are accessible
    assert hasattr(mcp_coder, "prompt_llm")
    assert hasattr(mcp_coder, "serialize_llm_response")
    assert hasattr(mcp_coder, "LLMResponseDict")


def test_no_import_errors() -> None:
    """Test that importing mcp_coder doesn't raise errors."""
    try:
        import mcp_coder
        from mcp_coder import (
            LLM_RESPONSE_VERSION,
            LLMResponseDict,
            ask_llm,
            deserialize_llm_response,
            prompt_llm,
            serialize_llm_response,
        )
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")
