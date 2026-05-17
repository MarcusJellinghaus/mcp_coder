@echo off
REM Reinstall mcp-coder in editable mode (developer convenience).
REM Delegates to ..\install.bat, then activates the venv in the caller's shell.

setlocal
set "REPO=%~dp0.."
call "%REPO%\install.bat" "%REPO%" ^
    --source local ^
    --local-path "%REPO%" ^
    --extras dev ^
    --extra-packages "langchain langchain-anthropic mlflow" ^
    --skip-templates ^
    --refresh
if errorlevel 1 (
    echo [FAIL] install.bat failed
    exit /b 1
)
endlocal & call "%~dp0..\.venv\Scripts\activate.bat"
