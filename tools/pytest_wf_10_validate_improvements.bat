@echo off
REM Performance Test Analysis - Validate Improvements
REM This script runs performance analysis after optimizations to measure improvements

echo ============================================
echo   Validating Performance Improvements
echo ============================================
echo.

echo [%time%] Starting validation analysis...
echo.

REM Create output directory if it doesn't exist
if not exist "tests\performance_management\output" mkdir "tests\performance_management\output"

REM Set output file with timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%
set validation_output=tests\performance_management\output\validation_%timestamp%.txt

echo Output will be saved to: %validation_output%
echo.

echo ============================================ > "%validation_output%"
echo PERFORMANCE VALIDATION - %date% %time% >> "%validation_output%"
echo ============================================ >> "%validation_output%"
echo. >> "%validation_output%"

echo Running full test suite with duration reporting... >> "%validation_output%"
echo. >> "%validation_output%"

REM Run full test suite with timing
echo Command: pytest --durations=30 --tb=short tests/ >> "%validation_output%"
echo. >> "%validation_output%"
pytest --durations=30 --tb=short tests/ >> "%validation_output%" 2>&1

echo. >> "%validation_output%"
echo ============================================ >> "%validation_output%"
echo MARKER-BASED PERFORMANCE TEST >> "%validation_output%"
echo ============================================ >> "%validation_output%"
echo. >> "%validation_output%"

echo Testing integration test exclusion (from pyproject.toml)... >> "%validation_output%"
echo Command: pytest -m "not git_integration and not claude_integration" --durations=10 tests/ >> "%validation_output%"
echo. >> "%validation_output%"
pytest -m "not git_integration and not claude_integration" --durations=10 tests/ >> "%validation_output%" 2>&1

echo. >> "%validation_output%"
echo ============================================ >> "%validation_output%"
echo INTEGRATION TESTS ONLY >> "%validation_output%"
echo ============================================ >> "%validation_output%"
echo. >> "%validation_output%"

echo Testing integration tests only... >> "%validation_output%"
echo Command: pytest -m "git_integration or claude_integration" --durations=0 tests/ >> "%validation_output%"
echo. >> "%validation_output%"
pytest -m "git_integration or claude_integration" --durations=0 tests/ >> "%validation_output%" 2>&1

if %ERRORLEVEL% neq 0 (
    echo.
    echo Note: Some test runs may have failed - check output for details
    echo This might be expected if optimizations are still in progress
)

echo.
echo SUCCESS: Validation analysis completed

echo.
echo ============================================
echo Validation complete. Next steps:
echo 1. Compare results with baseline measurements
echo 2. Update performance_analysis.md with improvements
echo 3. Document successful optimizations
echo 4. Plan next optimization phase
echo ============================================
echo.

REM Keep window open to review results
pause
