# Test Profiler Tool

## Overview

The `test_profiler.bat` script profiles all pytest tests in a single run and generates detailed performance reports for slow tests (those taking more than 1 second).

## What It Does

### 1. Clean Performance Data Directory
- Deletes all existing content in `docs\tests\performance_data\prof`
- Creates a fresh directory for new profiling data
- Ensures no stale data from previous runs

### 2. Run Pytest with Profiling (Single Pass)
- Runs pytest **once** with profiling enabled for all tests
- Uses `-n0` to override any parallel execution settings (forces serial execution)
- Loads the custom `test_profiler_plugin` that:
  - Profiles each test individually using Python's `cProfile`
  - Saves a `.prof` file for **every** test
  - Tracks duration of each test
  - Saves all durations to `durations.json`
- Provides progress output for each test as it runs
- **Continues to report generation even if some tests fail**

### 3. Generate Text Reports
- Processes the `durations.json` file
- For each test that took **>1 second**:
  - Generates a human-readable text report from the `.prof` file
  - Saves as `{test_name}_report.txt`
- Skips report generation for fast tests (keeps only `.prof` files)

### 4. Create Summary
- Generates a `summary.txt` file with:
  - Total number of tests run
  - Number of slow tests found (>1s)
  - List of all slow tests with their durations
  - Directory structure overview

## File Structure

```
tools\
├── __init__.py                       # Required for Python package
├── test_profiler.bat                 # Main script - full profiling
├── test_profiler_generate_only.bat   # Report generation only
├── test_profiler.md                  # This documentation
└── test_profiler_plugin\             # Python package
    ├── __init__.py                   # Pytest plugin for profiling
    └── generate_report.py            # Report generator script
```

## Usage

### Full Profiling (Clean Run)

```batch
cd <project_root>
tools\test_profiler.bat
```

This will:
1. Delete existing profile data
2. Run all tests with profiling
3. Generate reports for slow tests
4. Continue even if some tests fail

### Generate Reports Only (From Existing Data)

If pytest already ran but you want to regenerate reports:

```batch
tools\test_profiler_generate_only.bat
```

This is useful when:
- Report generation failed or was interrupted
- You want to adjust the threshold and regenerate reports
- You manually ran pytest with profiling

**Requirements:**
- Python with pytest installed
- The custom pytest plugin in `tools\test_profiler_plugin\`

## Output Files

After running, the `docs\tests\performance_data\prof\` directory contains:

```
docs\tests\performance_data\prof\
├── test_module__test_function1.prof          # Profile data for every test
├── test_module__test_function2.prof
├── test_module__test_slow_operation.prof
├── test_module__test_slow_operation_report.txt  # Text report (only for >1s tests)
├── durations.json                             # JSON with all test durations
└── summary.txt                                # Overview of profiling results
```

### File Types

- **`.prof` files**: Binary cProfile data for all tests (can be analyzed later)
- **`_report.txt` files**: Human-readable performance reports (only for tests >1s)
- **`durations.json`**: Machine-readable test timing data
- **`summary.txt`**: Quick overview of slow tests

## Configuration

### Threshold for "Slow" Tests

The threshold is defined in `tools\test_profiler_plugin\__init__.py`:

```python
DURATION_THRESHOLD_SECONDS = 1.0  # Generate reports for tests taking >1s
```

To change the threshold, edit this constant in the plugin file, then run `test_profiler_generate_only.bat` to regenerate reports.

## Why Single-Pass Profiling?

The tool uses a **single pytest run** instead of running tests multiple times because:
- **Much faster**: No overhead of starting pytest multiple times
- **More accurate**: Tests run in normal sequence, not isolated
- **Efficient**: Profile data is captured in one go

The custom pytest plugin hooks into pytest's test execution to profile each test individually during the single run.

## Behavior with Test Failures

The tool is designed to **continue profiling and generate reports even if some tests fail**:

- ✅ If tests fail, profiling continues for remaining tests
- ✅ Reports are generated for all completed tests
- ✅ You get a warning but the script completes
- ✅ The script exits with pytest's exit code (so CI/CD knows tests failed)

This is intentional because you often want to see performance data even when tests fail.

## Example Output

```
=== Test Profiler Starting ===

[1/4] Cleaning performance data directory...
Done.

[2/4] Running pytest with profiling (this may take a while)...
This will profile ALL tests individually in a single run.

Profiling [1/50]: tests/test_auth.py::test_login ... 0.3s ✓
Profiling [2/50]: tests/test_compute.py::test_heavy ... 3.5s ✓ SLOW
...
Profiling [25/50]: tests/test_api.py::test_broken ... 0.5s ✗ FAILED
...

WARNING: Some tests failed (exit code: 1)
Continuing to generate reports for completed tests...

[3/4] Generating reports for slow tests...
Found 5 slow tests (>1s)

Generating reports for 5 slow tests...
[1/5] test_compute.py::test_heavy (3.5s) ... Done
...

[4/4] Profiling complete!

=== Test Profiler Complete ===
Output directory: docs\tests\performance_data\prof

Files generated:
  - *.prof files for ALL tests
  - *_report.txt for tests taking >1 second
  - summary.txt with overview
  - durations.json with all test timings

Note: Script completed but some tests failed.
```

## Troubleshooting

### Pytest fails to run
- Ensure the plugin package exists: `tools\test_profiler_plugin\`
- Check that pytest is installed: `pip install pytest`
- Verify `tools\__init__.py` exists

### No reports generated
- Check if any tests took >1 second
- Verify `durations.json` was created in `docs\tests\performance_data\prof\`
- Look for errors in the console output

### Want to regenerate reports without re-running tests
- Use `tools\test_profiler_generate_only.bat`
- This reuses existing `.prof` files and `durations.json`

### Memory issues with large test suites
- The tool profiles all tests, which uses memory
- Consider profiling subsets of tests manually if needed

## Related Files

- `tools\test_profiler.bat` - Main orchestrator script (full run)
- `tools\test_profiler_generate_only.bat` - Report generation only
- `tools\test_profiler_plugin\__init__.py` - Pytest plugin for per-test profiling
- `tools\test_profiler_plugin\generate_report.py` - Report generator
- `tools\test_profiler.md` - This documentation
