"""
Pytest plugin for profiling individual tests.

This plugin hooks into pytest's test execution to profile each test individually
using Python's cProfile. It saves .prof files for all tests and tracks their durations.
"""

import cProfile
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import pytest

# Configuration
DURATION_THRESHOLD_SECONDS = 1.0  # Threshold for "slow" tests in reports
PROF_OUTPUT_DIR = Path("docs/tests/performance_data/prof")


class TestProfiler:
    """Manages profiling of individual tests."""

    def __init__(self):
        self.durations: Dict[str, float] = {}
        self.test_count = 0
        self.total_tests = 0

    def sanitize_test_name(self, nodeid: str) -> str:
        """
        Convert pytest node ID to a safe filename.
        
        Example: tests/test_file.py::TestClass::test_method
        Becomes: tests_test_file__TestClass__test_method
        """
        # Replace path separators and :: with underscores
        safe_name = nodeid.replace("::", "__").replace("/", "_").replace("\\", "_")
        # Remove .py extension
        safe_name = safe_name.replace(".py", "")
        return safe_name

    def get_prof_path(self, nodeid: str) -> Path:
        """Get the path for the .prof file for a given test."""
        safe_name = self.sanitize_test_name(nodeid)
        return PROF_OUTPUT_DIR / f"{safe_name}.prof"


# Global profiler instance
_profiler = TestProfiler()


def pytest_configure(config):
    """Called after command line options have been parsed."""
    # Ensure output directory exists
    PROF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get total number of tests (if available)
    # This will be updated in pytest_collection_modifyitems
    pass


def pytest_collection_modifyitems(session, config, items):
    """Called after test collection is complete."""
    _profiler.total_tests = len(items)
    print(f"\nCollected {_profiler.total_tests} tests for profiling")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """
    Hook that wraps the entire test execution (setup, call, teardown).
    We profile the entire test execution here.
    """
    _profiler.test_count += 1
    nodeid = item.nodeid
    prof_path = _profiler.get_prof_path(nodeid)
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Start profiling and timing
    start_time = time.time()
    profiler.enable()
    
    # Run the test (setup, call, teardown)
    outcome = yield
    
    # Stop profiling
    profiler.disable()
    duration = time.time() - start_time
    
    # Save profile data
    profiler.dump_stats(str(prof_path))
    
    # Store duration
    _profiler.durations[nodeid] = duration
    
    # Print progress
    slow_marker = " SLOW" if duration >= DURATION_THRESHOLD_SECONDS else ""
    progress = f"[{_profiler.test_count}/{_profiler.total_tests}]"
    print(f"Profiling {progress}: {nodeid} ... {duration:.2f}s ✓{slow_marker}")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished, right before returning exit status."""
    
    # Save durations to JSON
    durations_path = PROF_OUTPUT_DIR / "durations.json"
    
    # Sort by duration (slowest first)
    sorted_durations = dict(sorted(
        _profiler.durations.items(),
        key=lambda x: x[1],
        reverse=True
    ))
    
    durations_data = {
        "total_tests": _profiler.total_tests,
        "threshold_seconds": DURATION_THRESHOLD_SECONDS,
        "slow_tests_count": sum(1 for d in _profiler.durations.values() if d >= DURATION_THRESHOLD_SECONDS),
        "durations": sorted_durations
    }
    
    with open(durations_path, 'w') as f:
        json.dump(durations_data, f, indent=2)
    
    print(f"\n✓ Saved {len(_profiler.durations)} test durations to {durations_path}")
    print(f"✓ Found {durations_data['slow_tests_count']} slow tests (>{DURATION_THRESHOLD_SECONDS}s)")
