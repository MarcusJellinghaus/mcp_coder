@echo off
REM issue_stats.bat - Windows Batch Wrapper for Issue Statistics Workflow
REM
REM Usage:
REM   issue_stats.bat [--project-dir <path>] [--log-level <level>] [--filter <filter>] [--details] [--ignore-labels <label1,label2,...>]
REM
REM Parameters:
REM   --project-dir   Project directory path (default: current directory)
REM   --log-level     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
REM   --filter        Filter by category: all, human, bot (default: all)
REM   --details       Show individual issues with clickable links
REM   --ignore-labels Comma-separated list of label patterns to ignore (can be specified multiple times)
REM
REM Examples:
REM   issue_stats.bat
REM   issue_stats.bat --filter human
REM   issue_stats.bat --details
REM   issue_stats.bat --ignore-labels "status-*" --ignore-labels "priority-*"
REM   issue_stats.bat --project-dir "C:\my\project" --log-level DEBUG --filter bot --details
REM
REM This wrapper sets up the Python environment and executes the issue statistics workflow.

REM Set console to UTF-8 codepage to handle Unicode characters
chcp 65001 >nul 2>&1

REM Set Python to use UTF-8 encoding for all I/O operations
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUTF8=1

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%

python "%~dp0issue_stats.py" %*

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
