#!/usr/bin/env python3
"""
Verification script to test all import patterns for coordinator module.
This script tests both backward compatibility and new specific imports.
"""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))

def test_package_level_import():
    """Test importing the coordinator package."""
    try:
        from mcp_coder.cli.commands import coordinator
        print("✓ Package import: from mcp_coder.cli.commands import coordinator")
        return True
    except ImportError as e:
        print(f"✗ Package import failed: {e}")
        return False

def test_backward_compatible_function_imports():
    """Test backward-compatible function imports from package level."""
    tests = [
        ("execute_coordinator_test", "from mcp_coder.cli.commands.coordinator import execute_coordinator_test"),
        ("execute_coordinator_run", "from mcp_coder.cli.commands.coordinator import execute_coordinator_run"),
        ("format_job_output", "from mcp_coder.cli.commands.coordinator import format_job_output"),
        ("dispatch_workflow", "from mcp_coder.cli.commands.coordinator import dispatch_workflow"),
        ("CacheData", "from mcp_coder.cli.commands.coordinator import CacheData"),
    ]
    
    success = True
    for func_name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {import_stmt}")
        except ImportError as e:
            print(f"✗ {import_stmt} failed: {e}")
            success = False
    
    return success

def test_new_specific_imports():
    """Test new specific imports from submodules."""
    tests = [
        ("commands module", "from mcp_coder.cli.commands.coordinator.commands import format_job_output"),
        ("commands module CLI", "from mcp_coder.cli.commands.coordinator.commands import execute_coordinator_test"),
        ("core module", "from mcp_coder.cli.commands.coordinator.core import dispatch_workflow"),
        ("core module CacheData", "from mcp_coder.cli.commands.coordinator.core import CacheData"),
        ("core module private function", "from mcp_coder.cli.commands.coordinator.core import _filter_eligible_issues"),
    ]
    
    success = True
    for desc, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ New specific import ({desc}): {import_stmt}")
        except ImportError as e:
            print(f"✗ New specific import ({desc}) failed: {e}")
            success = False
    
    return success

def test_bulk_imports():
    """Test importing multiple functions at once."""
    try:
        from mcp_coder.cli.commands.coordinator import (
            execute_coordinator_test,
            execute_coordinator_run,
            dispatch_workflow,
            CacheData,
            format_job_output,
        )
        print("✓ Bulk import from package level successful")
        return True
    except ImportError as e:
        print(f"✗ Bulk import from package level failed: {e}")
        return False

def main():
    """Run all import verification tests."""
    print("Testing coordinator module import patterns...")
    print("=" * 60)
    
    tests = [
        ("Package level import", test_package_level_import),
        ("Backward compatible function imports", test_backward_compatible_function_imports),
        ("New specific imports", test_new_specific_imports),
        ("Bulk imports", test_bulk_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name) + ":")
        success = test_func()
        results.append(success)
        
    print("\n" + "=" * 60)
    print("SUMMARY:")
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "PASS" if results[i] else "FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} test categories passed")
    
    if passed == total:
        print("🎉 All import patterns work correctly!")
        return 0
    else:
        print("❌ Some import patterns failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())