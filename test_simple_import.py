"""Simple import test."""
import sys
import os

def test_can_import():
    """Test that the create_pr module can be imported."""
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Looking for: mcp_coder.cli.commands.create_pr")
    
    # Check if the file exists
    import pathlib
    expected_path = pathlib.Path("src/mcp_coder/cli/commands/create_pr.py")
    print(f"File exists: {expected_path.exists()}")
    
    try:
        from mcp_coder.cli.commands.create_pr import execute_create_pr
        assert execute_create_pr is not None
        print("Import successful!")
    except ImportError as e:
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        raise
