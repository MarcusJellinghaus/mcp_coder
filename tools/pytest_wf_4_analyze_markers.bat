@echo off
REM Performance Test Analysis - Analyze Test Markers
REM This script analyzes pytest markers in test files to understand current marking strategy

echo ============================================
echo   Analyzing Test Markers for Performance
echo ============================================
echo.

echo [%time%] Starting marker analysis...
echo.

REM Create output directory if it doesn't exist
if not exist "tests\performance_management\output" mkdir "tests\performance_management\output"

REM Set output file with timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%
set marker_output=tests\performance_management\output\marker_analysis_%timestamp%.txt

echo Output will be saved to: %marker_output%
echo.

REM Analyze markers in test files
echo ============================================ > "%marker_output%"
echo PYTEST MARKER ANALYSIS - %date% %time% >> "%marker_output%"
echo ============================================ >> "%marker_output%"
echo. >> "%marker_output%"

echo Collecting pytest markers... >> "%marker_output%"
echo. >> "%marker_output%"

REM Run pytest to collect markers
echo Running: pytest --markers >> "%marker_output%"
pytest --markers >> "%marker_output%" 2>&1

echo. >> "%marker_output%"
echo ============================================ >> "%marker_output%"
echo MARKER USAGE IN TEST FILES >> "%marker_output%"
echo ============================================ >> "%marker_output%"
echo. >> "%marker_output%"

REM Search for marker usage in test files
echo Searching for @pytest.mark usage in test files... >> "%marker_output%"
findstr /s /n "@pytest.mark" tests\*.py >> "%marker_output%" 2>nul

echo. >> "%marker_output%"
echo ============================================ >> "%marker_output%"
echo SLOW/PERFORMANCE RELATED MARKERS >> "%marker_output%"
echo ============================================ >> "%marker_output%"
echo. >> "%marker_output%"

REM Search for performance-related markers specifically
echo Searching for pytest markers defined in pyproject.toml... >> "%marker_output%"
findstr /s /n /i "git_integration\|claude_integration" tests\*.py >> "%marker_output%" 2>nul

echo. >> "%marker_output%"
echo ============================================ >> "%marker_output%"
echo TEST FILES WITH POTENTIAL PERFORMANCE ISSUES >> "%marker_output%"
echo ============================================ >> "%marker_output%"
echo. >> "%marker_output%"

REM Search for potential performance issues in test code
echo Searching for potential performance issues... >> "%marker_output%"
findstr /s /n /i "sleep\|time\.sleep\|requests\|subprocess\|claude" tests\*.py >> "%marker_output%" 2>nul

if %ERRORLEVEL% neq 0 (
    echo.
    echo Note: Some searches may not have found matches - this is normal
)

echo.
echo SUCCESS: Marker analysis completed successfully

echo.
echo ============================================
echo Analysis complete. Next steps:
echo 1. Review marker analysis: %marker_output%
echo 2. Update slow_tests_inventory.md with marker information
echo 3. Use LLM prompts to analyze marker strategy
echo 4. Plan marker standardization
echo ============================================
echo.

REM Keep window open to review results
pause
