"""Minimal test to verify import works."""

import pytest


def test_import_create_pr():
    """Test that create_pr module can be imported."""
    try:
        from mcp_coder.cli.commands.create_pr import execute_create_pr
        assert execute_create_pr is not None
        print("✅ Import successful")
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")
