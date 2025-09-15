"""Tests for the LLM providers module initialization."""

import importlib

import pytest


class TestLLMProvidersInit:
    """Test the LLM providers module initialization."""

    def test_module_can_be_imported(self) -> None:
        """Test that the llm_providers module can be imported successfully."""
        try:
            import mcp_coder.llm_providers
            assert mcp_coder.llm_providers is not None
        except ImportError as e:
            pytest.fail(f"Failed to import llm_providers module: {e}")

    def test_module_reload(self) -> None:
        """Test that the module can be reloaded without issues."""
        import mcp_coder.llm_providers
        try:
            importlib.reload(mcp_coder.llm_providers)
        except Exception as e:
            pytest.fail(f"Failed to reload llm_providers module: {e}")

    def test_module_attributes(self) -> None:
        """Test that the module has expected attributes."""
        import mcp_coder.llm_providers
        
        # The module should be importable and have the __name__ attribute
        assert hasattr(mcp_coder.llm_providers, "__name__")
        assert mcp_coder.llm_providers.__name__ == "mcp_coder.llm_providers"
