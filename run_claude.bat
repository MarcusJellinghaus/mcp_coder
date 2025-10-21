@echo off
REM Set environment variables for Claude Code MCP servers
REM Uses batch file location as project directory

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo ERROR: Virtual environment is not activated!
    echo.
    echo Please activate the virtual environment first:
    echo   .venv\Scripts\activate
    echo.
    echo Then run this script again.
    exit /b 1
)

REM Get batch file directory and remove trailing backslash
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

REM Set MCP_CODER environment variables
set "MCP_CODER_PROJECT_DIR=%PROJECT_DIR%"
set "MCP_CODER_VENV_DIR=%PROJECT_DIR%\.venv"

REM Display variables for verification
REM echo Starting Claude Code with:
REM echo VIRTUAL_ENV=%VIRTUAL_ENV%
REM echo MCP_CODER_PROJECT_DIR=%MCP_CODER_PROJECT_DIR%
REM echo MCP_CODER_VENV_DIR=%MCP_CODER_VENV_DIR%
REM echo.

REM Start Claude Code
REM claude
C:\Users\%USERNAME%\.local\bin\claude.exe
