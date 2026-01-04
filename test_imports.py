#!/usr/bin/env python3
"""Test script to verify all import patterns work correctly after refactoring."""

def test_package_import():
    """Test importing the coordinator package."""
    try:
        from mcp_coder.cli.commands import coordinator
        print("✓ Package import: from mcp_coder.cli.commands import coordinator")
        return True
    except ImportError as e:
        print(f"✗ Package import failed: {e}")
        return False

def test_function_imports():
    """Test importing specific functions from the coordinator package."""
    imports_to_test = [
        ("mcp_coder.cli.commands.coordinator", "execute_coordinator_test"),
        ("mcp_coder.cli.commands.coordinator", "execute_coordinator_run"),
    ]
    
    all_passed = True
    for module_path, func_name in imports_to_test:
        try:
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            if callable(func):
                print(f"✓ Function import: from {module_path} import {func_name}")
            else:
                print(f"✗ {func_name} is not callable")
                all_passed = False
        except (ImportError, AttributeError) as e:
            print(f"✗ Function import failed: {module_path}.{func_name} - {e}")
            all_passed = False
    
    return all_passed

def test_modular_imports():
    """Test importing from specific modules within coordinator package."""
    modular_imports = [
        ("mcp_coder.cli.commands.coordinator.commands", "format_job_output"),
        ("mcp_coder.cli.commands.coordinator.commands", "DEFAULT_TEST_COMMAND"),
        ("mcp_coder.cli.commands.coordinator.core", "dispatch_workflow"),
        ("mcp_coder.cli.commands.coordinator.core", "CacheData"),
        ("mcp_coder.cli.commands.coordinator.core", "get_eligible_issues"),
    ]
    
    all_passed = True
    for module_path, item_name in modular_imports:
        try:
            module = __import__(module_path, fromlist=[item_name])
            item = getattr(module, item_name)
            print(f"✓ Modular import: from {module_path} import {item_name}")
        except (ImportError, AttributeError) as e:
            print(f"✗ Modular import failed: {module_path}.{item_name} - {e}")
            all_passed = False
    
    return all_passed

def test_backward_compatibility():
    """Test that original import patterns still work."""
    try:
        # This should still work after refactoring
        from mcp_coder.cli.commands.coordinator import execute_coordinator_test, execute_coordinator_run
        print("✓ Backward compatibility: multiple function import works")
        return True
    except ImportError as e:
        print(f"✗ Backward compatibility failed: {e}")
        return False

def main():
    """Run all import tests."""
    print("=== Coordinator Module Import Tests ===\n")
    
    tests = [
        ("Package Import", test_package_import),
        ("Function Imports", test_function_imports),
        ("Modular Imports", test_modular_imports),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
        print(f"Result: {'PASS' if result else 'FAIL'}")
    
    print("\n=== Test Summary ===")
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())