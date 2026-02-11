#!/usr/bin/env python3
"""Run pylint on modified files for Step 3."""

import subprocess
import sys

# Modified files for this PR
files = [
    "src/mcp_coder/utils/github_operations/issues/cache.py",
    "src/mcp_coder/workflows/vscodeclaude/orchestrator.py",
    "tests/utils/github_operations/test_issue_cache.py",
    "tests/workflows/vscodeclaude/test_orchestrator_cache.py",
    "tests/workflows/vscodeclaude/test_closed_issues_integration.py",
]

print("Running pylint on modified files...")
print("=" * 80)

all_passed = True
for file_path in files:
    print(f"\n\nChecking {file_path}...")
    print("-" * 80)
    result = subprocess.run(
        ["python", "-m", "pylint", file_path],
        capture_output=False,
        text=True,
    )
    if result.returncode != 0:
        all_passed = False
        print(f"FAILED: {file_path} has pylint issues (exit code: {result.returncode})")

print("\n" + "=" * 80)
if all_passed:
    print("✓ All files passed pylint check!")
    sys.exit(0)
else:
    print("✗ Some files have pylint issues")
    sys.exit(1)
