#!/usr/bin/env python
"""Test if create_pr module can be imported."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from mcp_coder.cli.commands.create_pr import execute_create_pr
    print("✓ Import successful!")
    print(f"execute_create_pr function: {execute_create_pr}")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
