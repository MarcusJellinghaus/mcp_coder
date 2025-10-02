@echo off
REM Pytest Performance Statistics Batch Script
REM Runs pytest for each marker category and shows ONLY duration stats for 20 slowest tests

echo ========================================
echo Pytest Performance Statistics (Durations Only)
echo ========================================
echo.

REM Unit tests (no markers - fast, mocked tests)
echo [1/6] UNIT TESTS (no integration markers)
echo ----------------------------------------
pytest -m "not claude_cli_integration and not claude_api_integration and not git_integration and not formatter_integration and not github_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s"
echo.

REM Claude CLI Integration Tests
echo [2/6] CLAUDE CLI INTEGRATION tests
echo ----------------------------------------
pytest -m "claude_cli_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s"
echo.

REM Claude API Integration Tests
echo [3/6] CLAUDE API INTEGRATION tests
echo ----------------------------------------
pytest -m "claude_api_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s"
echo.

REM Git Integration Tests
echo [4/6] GIT INTEGRATION tests
echo ----------------------------------------
pytest -m "git_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s"
echo.

REM Formatter Integration Tests
echo [5/6] FORMATTER INTEGRATION tests
echo ----------------------------------------
pytest -m "formatter_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s"
echo.

REM GitHub Integration Tests
echo [6/6] GITHUB INTEGRATION tests
echo ----------------------------------------
pytest -m "github_integration" --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s"
echo.

REM All tests combined
echo ========================================
echo [FINAL] ALL TESTS (complete suite)
echo ========================================
pytest --durations=20 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s"
echo.

echo ========================================
echo Performance statistics collection complete!
echo ========================================
pause
