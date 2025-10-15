@echo off
REM validate_labels.bat - Windows Batch Wrapper for Label Validation Workflow
REM
REM Usage:
REM   validate_labels.bat [--project-dir <path>] [--log-level <level>] [--dry-run]
REM
REM Parameters:
REM   --project-dir   Project directory path (default: current directory)
REM   --log-level     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
REM   --dry-run       Preview validation results without making changes
REM
REM Examples:
REM   validate_labels.bat
REM   validate_labels.bat --dry-run
REM   validate_labels.bat --project-dir "C:\my\project" --log-level DEBUG
REM   validate_labels.bat --project-dir . --log-level INFO --dry-run
REM
REM This wrapper sets up the Python environment and executes the label validation workflow.

REM Set console to UTF-8 codepage to handle Unicode characters in label names
chcp 65001 >nul 2>&1

REM Set Python to use UTF-8 encoding for all I/O operations
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUTF8=1

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%

python "%~dp0validate_labels.py" %*

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
