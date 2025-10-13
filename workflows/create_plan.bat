@echo off
REM create_plan.bat - Windows Batch Wrapper for Plan Generation Workflow
REM
REM Usage:
REM   create_plan.bat <issue_number> [--project-dir <path>] [--log-level <level>] [--llm-method <method>]
REM
REM Parameters:
REM   issue_number    GitHub issue number (required)
REM   --project-dir   Project directory path (default: current directory)
REM   --log-level     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
REM   --llm-method    LLM method: claude_code_cli, claude_code_api (default: claude_code_cli)
REM
REM Examples:
REM   create_plan.bat 123
REM   create_plan.bat 123 --project-dir "C:\my\project" --log-level DEBUG
REM   create_plan.bat 123 --llm-method claude_code_api
REM
REM This wrapper sets up the Python environment and executes the plan generation workflow.

REM Set console to UTF-8 codepage to handle Unicode characters
chcp 65001 >nul 2>&1

REM Set Python to use UTF-8 encoding for all I/O operations
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUTF8=1

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%

echo Starting create_plan workflow...
python workflows\create_plan.py %*

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
