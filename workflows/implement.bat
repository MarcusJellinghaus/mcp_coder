@echo off
REM Simple implement workflow - orchestrates existing mcp-coder functionality
REM Created in Step 3: Create Simple Implement Workflow Script
REM Updated to support --log-level and --llm-method parameters

echo Starting implement workflow...
python workflows/implement.py --project-dir . --log-level INFO --llm-method claude_code_cli

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
