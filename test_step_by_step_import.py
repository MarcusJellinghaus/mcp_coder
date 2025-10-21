"""Test imports step by step."""

def test_import_mcp_coder():
    """Test importing mcp_coder package."""
    import mcp_coder
    assert mcp_coder is not None
    print("✓ mcp_coder imported")

def test_import_cli():
    """Test importing cli module."""
    import mcp_coder.cli
    assert mcp_coder.cli is not None
    print("✓ mcp_coder.cli imported")

def test_import_commands():
    """Test importing commands module."""
    import mcp_coder.cli.commands
    assert mcp_coder.cli.commands is not None
    print("✓ mcp_coder.cli.commands imported")

def test_import_implement():
    """Test importing implement (existing module)."""
    import mcp_coder.cli.commands.implement
    assert mcp_coder.cli.commands.implement is not None
    print("✓ mcp_coder.cli.commands.implement imported")

def test_import_create_pr():
    """Test importing create_pr (new module)."""
    try:
        import mcp_coder.cli.commands.create_pr
        assert mcp_coder.cli.commands.create_pr is not None
        print("✓ mcp_coder.cli.commands.create_pr imported")
    except ImportError as e:
        print(f"✗ create_pr import failed: {e}")
        # Try to find the module file
        import os
        from pathlib import Path
        src_path = Path("src/mcp_coder/cli/commands/create_pr.py")
        print(f"File exists in src/: {src_path.exists()}")
        raise
