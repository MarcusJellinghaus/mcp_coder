@echo off
REM Performance Test Analysis - Gather Slow Tests
REM This script runs pytest with duration reporting to identify slow tests

echo ============================================
echo   Gathering Slow Test Performance Data
echo ============================================
echo.

echo [%time%] Starting pytest performance analysis...
echo.

REM Create output directory if it doesn't exist
if not exist "tests\performance_management\output" mkdir "tests\performance_management\output"

REM Set output file with timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%
set output_file=tests\performance_management\output\slow_tests_%timestamp%.txt

echo Output will be saved to: %output_file%
echo.

REM Run pytest with duration reporting
echo Running: pytest --durations=20 --tb=no -v tests/
echo.
pytest --durations=20 --tb=no -v tests/ > "%output_file%" 2>&1

if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: pytest completed with errors or failures
    echo Check the output file for details: %output_file%
) else (
    echo.
    echo SUCCESS: Performance analysis completed successfully
)

echo.
echo ============================================
echo Analysis complete. Next steps:
echo 1. COPY this output file path to your LLM: %output_file%
echo 2. Tell your LLM: "Please read and analyze the output file"
echo 3. Use Step 2 from tests\performance_management\complete_workflow.md
echo 4. LLM will provide analysis and update TASK_TRACKER.md
echo 5. Continue with next steps as guided by LLM
echo ============================================
echo.

REM Keep window open to review results
pause
