#!/usr/bin/env python3
"""
Test script to verify issue_stats.bat works correctly from different directories.

This test verifies that the batch launcher:
1. Works when called from the project root
2. Works when called from a subdirectory
3. Works when called from the parent directory
4. Uses %~dp0 correctly to find the Python script regardless of cwd

FIX APPLIED:
--------------
Changed: python workflows\\issue_stats.py %*
To:      python "%~dp0issue_stats.py" %*

This ensures the batch file can find the Python script regardless of the
current working directory, because %~dp0 always resolves to the directory
containing the batch file itself.

The same fix was applied to workflows/define_labels.bat for consistency.
"""

import subprocess
import sys
from pathlib import Path

def run_batch_from_dir(batch_path: Path, working_dir: Path, description: str) -> bool:
    """
    Run the batch file from a specific working directory.
    
    Args:
        batch_path: Absolute path to the batch file
        working_dir: Directory to run the command from
        description: Description of the test
    
    Returns:
        True if the command succeeded (exit code 0), False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Test: {description}")
    print(f"Working directory: {working_dir}")
    print(f"Batch file: {batch_path}")
    print(f"{'='*70}")
    
    try:
        # Run batch file with --help flag to test basic functionality
        result = subprocess.run(
            [str(batch_path), "--help"],
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout[:500]}")  # First 500 chars
        if result.stderr:
            print(f"STDERR:\n{result.stderr[:500]}")  # First 500 chars
        
        if result.returncode == 0:
            print("✓ Test PASSED")
            return True
        else:
            print("✗ Test FAILED")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Test FAILED - Timeout")
        return False
    except Exception as e:
        print(f"✗ Test FAILED - Exception: {e}")
        return False

def main():
    """Run all batch launcher tests from different directories."""
    print("Testing issue_stats.bat from different directories")
    print("="*70)
    
    # Get absolute paths
    project_root = Path(__file__).parent.absolute()
    batch_file = project_root / "workflows" / "issue_stats.bat"
    
    if not batch_file.exists():
        print(f"ERROR: Batch file not found: {batch_file}")
        return 1
    
    # Track test results
    tests = []
    
    # Test 1: Run from project root
    tests.append(run_batch_from_dir(
        batch_file,
        project_root,
        "Run from project root directory"
    ))
    
    # Test 2: Run from src subdirectory
    src_dir = project_root / "src"
    if src_dir.exists():
        tests.append(run_batch_from_dir(
            batch_file,
            src_dir,
            "Run from src subdirectory"
        ))
    
    # Test 3: Run from workflows directory
    workflows_dir = project_root / "workflows"
    if workflows_dir.exists():
        tests.append(run_batch_from_dir(
            batch_file,
            workflows_dir,
            "Run from workflows directory"
        ))
    
    # Test 4: Run from tests directory
    tests_dir = project_root / "tests"
    if tests_dir.exists():
        tests.append(run_batch_from_dir(
            batch_file,
            tests_dir,
            "Run from tests directory"
        ))
    
    # Test 5: Run from parent directory (if accessible)
    parent_dir = project_root.parent
    try:
        # Try to access parent directory
        if parent_dir.exists() and parent_dir != project_root:
            tests.append(run_batch_from_dir(
                batch_file,
                parent_dir,
                "Run from parent directory"
            ))
    except Exception as e:
        print(f"\nSkipping parent directory test: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {sum(tests)}")
    print(f"Failed: {len(tests) - sum(tests)}")
    
    if all(tests):
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
