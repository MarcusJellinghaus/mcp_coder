@echo off
REM Simple implement workflow - orchestrates existing mcp-coder functionality
REM Created in Step 3: Create Simple Implement Workflow Script
REM Updated to support --log-level and --llm-method parameters

REM Set console to UTF-8 codepage to handle Unicode characters
chcp 65001 >nul 2>&1

REM Set Python to use UTF-8 encoding for all I/O operations
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8
set PYTHONUTF8=1

echo Starting implement workflow...
python workflows/implement.py --project-dir . --log-level INFO --llm-method claude_code_cli

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
