#!/usr/bin/env python3
"""Manual test to verify create_pr import works."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print("Attempting to import...")
try:
    from mcp_coder.cli.commands.create_pr import execute_create_pr
    print("✅ SUCCESS: Import worked!")
    print(f"   Function: {execute_create_pr}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nDone.")
