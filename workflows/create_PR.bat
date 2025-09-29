@echo off
REM Simple create_pr workflow
REM Updated to support --log-level and --llm-method parameters

echo Starting create_pr workflow...
python workflows/create_py.py --project-dir . --log-level INFO --llm-method claude_code_cli

if %ERRORLEVEL% neq 0 (
    echo Workflow failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Workflow completed successfully!
