#!/usr/bin/env python3
"""Quick test to verify Claude executable can be found."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_coder.llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
    verify_claude_installation,
    _get_claude_search_paths
)

print("=" * 80)
print("TESTING CLAUDE EXECUTABLE FINDER")
print("=" * 80)

print("\n1. Search paths being checked:")
print("-" * 80)
for i, path in enumerate(_get_claude_search_paths(), 1):
    exists = os.path.exists(path) if path else False
    print(f"  {i}. {path} {'✓ EXISTS' if exists else ''}")

print("\n2. Attempting to find Claude executable:")
print("-" * 80)
try:
    claude_path = find_claude_executable(return_none_if_not_found=True, fast_mode=True)
    if claude_path:
        print(f"✓ Found Claude at: {claude_path}")
        print(f"  File exists: {os.path.exists(claude_path)}")
        print(f"  Is file: {os.path.isfile(claude_path)}")
    else:
        print("✗ Claude not found")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n3. Verification result:")
print("-" * 80)
result = verify_claude_installation()
for key, value in result.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 80)
