@echo off
REM Reinstall mcp-coder in editable mode (developer convenience).
REM Delegates to install.bat in the same dir, then activates the venv in
REM the caller's shell.

setlocal
set "REPO=%~dp0.."
call "%~dp0install.bat" "%REPO%" ^
    --source local ^
    --local-path "%REPO%" ^
    --extras dev ^
    --extra-packages "langchain langchain-anthropic mlflow" ^
    --refresh
if errorlevel 1 (
    echo [FAIL] install.bat failed
    exit /b 1
)
endlocal & call "%~dp0..\.venv\Scripts\activate.bat"
