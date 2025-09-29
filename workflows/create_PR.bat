@echo off
REM create_PR.bat - Windows Batch Wrapper for PR Creation Workflow
REM
REM Usage:
REM   create_PR.bat [--project-dir <path>] [--log-level <level>]
REM
REM Parameters:
REM   --project-dir   Project directory path (default: current directory)
REM   --log-level     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
REM
REM Examples:
REM   create_PR.bat
REM   create_PR.bat --project-dir "C:\my\project" --log-level DEBUG
REM
REM This wrapper sets up the Python environment and executes the PR workflow.

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%

echo Starting create_PR workflow...
python workflows\create_PR.py --project-dir . --log-level INFO --llm-method claude_code_cli

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
