"""Quick test to check if create_pr module can be imported."""

try:
    from mcp_coder.cli.commands.create_pr import execute_create_pr
    print("SUCCESS: create_pr module imported successfully")
    print(f"execute_create_pr function: {execute_create_pr}")
except ImportError as e:
    print(f"FAIL: Import error: {e}")
except Exception as e:
    print(f"FAIL: Unexpected error: {e}")
