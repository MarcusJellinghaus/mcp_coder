#!/usr/bin/env python3
"""Test script to verify all coordinator import patterns work correctly."""

def test_import_patterns():
    """Test all import patterns for the coordinator module."""
    import_results = []
    
    try:
        # Test package-level import (backward compatible)
        from mcp_coder.cli.commands import coordinator
        import_results.append("✓ Package import: from mcp_coder.cli.commands import coordinator")
    except ImportError as e:
        import_results.append(f"✗ Package import failed: {e}")

    try:
        # Test function import (backward compatible) 
        from mcp_coder.cli.commands.coordinator import execute_coordinator_test
        import_results.append("✓ Function import: from mcp_coder.cli.commands.coordinator import execute_coordinator_test")
    except ImportError as e:
        import_results.append(f"✗ Function import failed: {e}")

    try:
        # Test function import (backward compatible)
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run  
        import_results.append("✓ Function import: from mcp_coder.cli.commands.coordinator import execute_coordinator_run")
    except ImportError as e:
        import_results.append(f"✗ Function import failed: {e}")

    try:
        # Test new specific import from commands module
        from mcp_coder.cli.commands.coordinator.commands import format_job_output
        import_results.append("✓ New specific import: from mcp_coder.cli.commands.coordinator.commands import format_job_output")
    except ImportError as e:
        import_results.append(f"✗ New specific commands import failed: {e}")

    try:
        # Test new specific import from core module
        from mcp_coder.cli.commands.coordinator.core import dispatch_workflow
        import_results.append("✓ New specific import: from mcp_coder.cli.commands.coordinator.core import dispatch_workflow")
    except ImportError as e:
        import_results.append(f"✗ New specific core import failed: {e}")

    try:
        # Test import of all public functions from package level
        from mcp_coder.cli.commands.coordinator import (
            execute_coordinator_test,
            execute_coordinator_run,
            load_coordinator_config,
            dispatch_workflow,
            get_issues_from_github,
            filter_issues_for_action,
            format_job_output,
            get_cache_filename
        )
        import_results.append("✓ All public functions importable from package level")
    except ImportError as e:
        import_results.append(f"✗ Public functions import failed: {e}")

    # Print all results
    for result in import_results:
        print(result)
    
    # Return success status
    failed_imports = [r for r in import_results if r.startswith("✗")]
    if failed_imports:
        print(f"\n{len(failed_imports)} import(s) failed!")
        return False
    else:
        print(f"\nAll {len(import_results)} imports successful!")
        return True

if __name__ == "__main__":
    success = test_import_patterns()
    exit(0 if success else 1)