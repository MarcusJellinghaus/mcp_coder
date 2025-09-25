@echo off
REM Simple implement workflow - orchestrates existing mcp-coder functionality
REM Created in Step 3: Create Simple Implement Workflow Script
REM Updated to support --log-level parameter

echo Starting implement workflow...
python workflows/implement.py --project-dir . --log-level INFO

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
