@echo off
cls
setlocal enabledelayedexpansion
REM Local launcher for Claude Code with MCP servers using active environment
REM Uses --active flag to target the active environment where mcp-coder is installed

REM Check if mcp-coder is available in active environment
mcp-coder --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ERROR: mcp-coder not found in PATH
    echo Make sure mcp-coder is installed in your active environment
    echo Try: pip install mcp-coder
    exit /b 1
)

REM Set project directories for MCP servers
set "MCP_CODER_PROJECT_DIR=%CD%"
set "MCP_CODER_VENV_DIR=%CD%\.venv"
set "DISABLE_AUTOUPDATER=1"

REM Start Claude Code using the local mcp-coder installation
echo Starting Claude Code:
echo VIRTUAL_ENV=!VIRTUAL_ENV!
echo MCP_CODER_PROJECT_DIR=!MCP_CODER_PROJECT_DIR!
echo MCP_CODER_VENV_DIR=!MCP_CODER_VENV_DIR!
echo DISABLE_AUTOUPDATER=!DISABLE_AUTOUPDATER!
C:\Users\%USERNAME%\.local\bin\claude.exe %*