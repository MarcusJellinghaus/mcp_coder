@echo off
REM Windows batch wrapper for create_PR.py workflow script
REM
REM This script provides a convenient Windows interface to the PR creation workflow.
REM It validates the environment, activates the virtual environment if needed,
REM and executes the Python script with proper error handling.
REM
REM Usage: create_PR.bat [--project-dir PATH] [--log-level LEVEL]
REM   --project-dir PATH   Project directory path (default: current directory)
REM   --log-level LEVEL    Set logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
REM
REM Examples:
REM   create_PR.bat                              # Use current directory, INFO logging
REM   create_PR.bat --log-level DEBUG            # Use current directory, DEBUG logging
REM   create_PR.bat --project-dir C:\my\project  # Specify project directory
REM

setlocal enabledelayedexpansion

REM Check if we're in the correct directory structure
if not exist "workflows\create_PR.py" (
    echo ERROR: create_PR.py not found in workflows\ directory
    echo Please run this script from the project root directory
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not available in PATH
    echo Please ensure Python is installed and accessible
    exit /b 1
)

REM Check if virtual environment exists and activate it
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment
        exit /b 1
    )
) else if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment
        exit /b 1
    )
) else (
    echo WARNING: No virtual environment found (.venv or venv)
    echo Proceeding with system Python installation
)

REM Verify required Python packages are available
python -c "import sys; sys.path.insert(0, 'src'); import mcp_coder" >nul 2>&1
if errorlevel 1 (
    echo ERROR: mcp_coder package not found
    echo Please ensure the package is installed or src/ is in PYTHONPATH
    exit /b 1
)

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM Execute the Python script with all passed arguments
echo Starting PR creation workflow...
echo Using project directory: %CD%
echo.

python workflows\create_PR.py %*

REM Capture exit code from Python script
set exit_code=%errorlevel%

REM Provide user feedback based on exit code
if %exit_code% equ 0 (
    echo.
    echo SUCCESS: PR creation workflow completed successfully!
) else (
    echo.
    echo ERROR: PR creation workflow failed with exit code %exit_code%
    echo Check the log output above for details
)

REM Preserve exit code for calling scripts
exit /b %exit_code%