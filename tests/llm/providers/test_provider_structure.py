"""Tests for LLM provider package structure."""

import pytest


def test_providers_package_structure() -> None:
    """Verify providers package structure and imports."""
    import mcp_coder.llm.providers
    import mcp_coder.llm.providers.claude
    
    # Verify claude provider modules importable
    from mcp_coder.llm.providers.claude import (
        claude_code_interface,
        claude_code_cli,
        claude_code_api,
    )
    
    assert hasattr(claude_code_interface, 'ask_claude_code')
    assert hasattr(claude_code_cli, 'ask_claude_code_cli')
    assert hasattr(claude_code_api, 'ask_claude_code_api')


def test_public_api_provider_exports() -> None:
    """Verify provider functions accessible via public API."""
    from mcp_coder import ask_claude_code
    
    assert callable(ask_claude_code)


def test_provider_modules_exist() -> None:
    """Test that all expected provider modules exist and are importable."""
    # Test claude provider modules
    try:
        from mcp_coder.llm.providers.claude import claude_code_interface
        from mcp_coder.llm.providers.claude import claude_code_cli
        from mcp_coder.llm.providers.claude import claude_code_api
        from mcp_coder.llm.providers.claude import claude_executable_finder
        from mcp_coder.llm.providers.claude import claude_cli_verification
    except ImportError as e:
        pytest.fail(f"Failed to import claude provider modules: {e}")


def test_claude_provider_functions() -> None:
    """Test that claude provider functions are accessible."""
    from mcp_coder.llm.providers.claude.claude_code_interface import ask_claude_code
    from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
    from mcp_coder.llm.providers.claude.claude_code_api import ask_claude_code_api
    from mcp_coder.llm.providers.claude.claude_executable_finder import (
        find_claude_executable,
        verify_claude_installation,
    )
    
    # Verify functions are callable
    assert callable(ask_claude_code)
    assert callable(ask_claude_code_cli)
    assert callable(ask_claude_code_api)
    assert callable(find_claude_executable)
    assert callable(verify_claude_installation)


def test_provider_package_init() -> None:
    """Test that provider package __init__.py files exist and are loadable."""
    # These should not raise ImportError
    import mcp_coder.llm.providers
    import mcp_coder.llm.providers.claude
    
    # Verify they are actually packages (have __path__ attribute)
    assert hasattr(mcp_coder.llm.providers, '__path__')
    assert hasattr(mcp_coder.llm.providers.claude, '__path__')