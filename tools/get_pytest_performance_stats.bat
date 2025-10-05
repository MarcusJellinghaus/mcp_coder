@echo off
REM Pytest Performance Statistics Batch Script
REM Runs pytest for each marker category and shows ONLY duration stats for 20 slowest tests
REM Outputs to timestamped file in docs/tests/performance_data/

REM Create timestamp for filename
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "SS=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%SS%"

REM Create output directory if it doesn't exist
if not exist "docs\tests\performance_data" mkdir "docs\tests\performance_data"

REM Set output file
set "output_file=docs\tests\performance_data\performance_stats_%timestamp%.txt"

REM Get git branch
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "git_branch=%%i"
if "%git_branch%"=="" set "git_branch=unknown"

REM Function to echo to both console and file
REM Usage: call :echo_both "message"
goto :start
:echo_both
echo %~1
echo %~1 >> "%output_file%"
exit /b
:start

REM Start output to both console and file
echo === PYTEST PERFORMANCE REPORT === > "%output_file%"
call :echo_both "=== PYTEST PERFORMANCE REPORT ==="
call :echo_both "Timestamp: %YYYY%-%MM%-%DD% %HH%:%Min%:%SS%"
call :echo_both "Git Branch: %git_branch%"
call :echo_both "Command: .\tools\get_pytest_performance_stats.bat"
call :echo_both ""
call :echo_both "========================================"
call :echo_both "Pytest Performance Statistics (Durations Only)"
call :echo_both "========================================"
call :echo_both " "

REM Unit tests (no markers - fast, mocked tests)
call :echo_both "[1/6] UNIT TESTS (no integration markers)"
call :echo_both "----------------------------------------"
set "temp_file=%temp%\pytest_output_%random%.txt"
pytest -m "not claude_cli_integration and not claude_api_integration and not git_integration and not formatter_integration and not github_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul
call :echo_both " "
call :echo_both " "

REM Claude CLI Integration Tests
call :echo_both "[2/6] CLAUDE CLI INTEGRATION tests"
call :echo_both "----------------------------------------"
set "temp_file=%temp%\pytest_output_%random%.txt"
pytest -m "claude_cli_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul
call :echo_both " "
call :echo_both " "

REM Claude API Integration Tests
call :echo_both "[3/6] CLAUDE API INTEGRATION tests"
call :echo_both "----------------------------------------"
set "temp_file=%temp%\pytest_output_%random%.txt"
pytest -m "claude_api_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul
call :echo_both " "
call :echo_both " "

REM Git Integration Tests
call :echo_both "[4/6] GIT INTEGRATION tests"
call :echo_both "----------------------------------------"
set "temp_file=%temp%\pytest_output_%random%.txt"
pytest -m "git_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul
call :echo_both " "
call :echo_both " "

REM Formatter Integration Tests
call :echo_both "[5/6] FORMATTER INTEGRATION tests"
call :echo_both "----------------------------------------"
set "temp_file=%temp%\pytest_output_%random%.txt"
pytest -m "formatter_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul
call :echo_both " "
call :echo_both " "

REM GitHub Integration Tests
call :echo_both "[6/6] GITHUB INTEGRATION tests"
call :echo_both "----------------------------------------"
set "temp_file=%temp%\pytest_output_%random%.txt"
pytest -m "github_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul
call :echo_both " "
call :echo_both " "

REM All tests combined
call :echo_both "========================================"
call :echo_both "[FINAL] ALL TESTS (complete suite)"
call :echo_both "========================================"
set "temp_file=%temp%\pytest_output_%random%.txt"
pytest --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul
call :echo_both " "
call :echo_both " "
call :echo_both "========================================"
call :echo_both "Performance statistics collection complete!"
call :echo_both "Output saved to: %output_file%"
call :echo_both "========================================"
echo.
echo Performance statistics saved to: %output_file%

