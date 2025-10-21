"""Test if create_pr module can be imported."""

try:
    from mcp_coder.cli.commands.create_pr import execute_create_pr
    print("SUCCESS: Module imported successfully")
    print(f"execute_create_pr function: {execute_create_pr}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
