@echo off
cls
setlocal enabledelayedexpansion
REM Simple launcher for Claude Code with MCP servers
REM Assumes you're running from the project root

REM Check if virtual environment is activated
if "!VIRTUAL_ENV!"=="" (
    if not exist ".venv\Scripts\activate.bat" (
        echo ERROR: Virtual environment not found at .venv
        echo Please run: venv_tools\create_venv.bat
        echo Then try again.
        exit /b 1
    )
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    if "!VIRTUAL_ENV!"=="" (
        echo ERROR: Failed to activate virtual environment
        echo Please check .venv\Scripts\activate.bat
        exit /b 1
    )
)

REM --- Check Claude Code version (pinned to known-good version for Windows stdout capture) ---
REM See: https://github.com/anthropics/claude-code/issues/18748
REM See: https://github.com/MarcusJellinghaus/mcp_coder/issues/509
set "EXPECTED_CC_VER=2.1.40"
for /f "tokens=1" %%v in ('C:\Users\%USERNAME%\.local\bin\claude.exe --version 2^>nul') do set "CC_VER=%%v"
if "!CC_VER!"=="" (
    echo ERROR: Claude Code not found at C:\Users\%USERNAME%\.local\bin\claude.exe
    exit /b 1
)
if not "!CC_VER!"=="!EXPECTED_CC_VER!" (
    echo WARNING: Claude Code !CC_VER! may have Windows bash output capture issues
    echo   Expected: !EXPECTED_CC_VER!  Current: !CC_VER!
    echo   See https://github.com/MarcusJellinghaus/mcp_coder/issues/509
)

REM Set project directories for MCP servers
set "MCP_CODER_PROJECT_DIR=%CD%"
set "MCP_CODER_VENV_DIR=%CD%\.venv"
set "DISABLE_AUTOUPDATER=1"

REM Start Claude Code
echo Starting Claude Code with:
echo VIRTUAL_ENV=!VIRTUAL_ENV!
echo MCP_CODER_PROJECT_DIR=!MCP_CODER_PROJECT_DIR!
echo MCP_CODER_VENV_DIR=!MCP_CODER_VENV_DIR!
echo DISABLE_AUTOUPDATER=!DISABLE_AUTOUPDATER!
C:\Users\%USERNAME%\.local\bin\claude.exe %*