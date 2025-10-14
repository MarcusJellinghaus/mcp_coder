@echo off
REM define_labels.bat - Windows Batch Wrapper for Label Definition Workflow
REM
REM Usage:
REM   define_labels.bat [--project-dir <path>] [--log-level <level>] [--dry-run]
REM
REM Parameters:
REM   --project-dir   Project directory path (default: current directory)
REM   --log-level     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
REM   --dry-run       Preview changes without applying them
REM
REM Examples:
REM   define_labels.bat
REM   define_labels.bat --dry-run
REM   define_labels.bat --project-dir "C:\my\project" --log-level DEBUG
REM   define_labels.bat --project-dir . --log-level INFO --dry-run
REM
REM This wrapper sets up the Python environment and executes the label definition workflow.

REM Set console to UTF-8 codepage to handle Unicode characters
chcp 65001 >nul 2>&1

REM Set Python to use UTF-8 encoding for all I/O operations
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUTF8=1

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%

python "%~dp0define_labels.py" %*

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
