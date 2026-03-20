@echo off
cls
setlocal enabledelayedexpansion
REM Test agent mode: prompt, continue, MCP tool discovery, and file write
REM Uses the local .mcp.json with MCP servers

REM === Configuration ===
set "LOG_LEVEL=INFO"
set "LLM_METHOD=langchain"

REM === Setup ===
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Local virtual environment not found at .venv
    exit /b 1
)

set "EXPECTED_VENV=%CD%\.venv"
if not "!VIRTUAL_ENV!"=="" (
    if not "!VIRTUAL_ENV!"=="!EXPECTED_VENV!" (
        echo INFO: Deactivating wrong virtual environment
        call deactivate 2>nul
        set "VIRTUAL_ENV="
    )
)
if "!VIRTUAL_ENV!"=="" (
    echo Activating local virtual environment...
    call .venv\Scripts\activate.bat
)

python -c "import mcp_coder" 2>nul
if !errorlevel! neq 0 (
    echo ERROR: mcp-coder not found in local virtual environment
    exit /b 1
)

set "MCP_CODER_PROJECT_DIR=%CD%"
set "MCP_CODER_VENV_DIR=%CD%\.venv"

echo === Agent Mode Test ===
echo   VIRTUAL_ENV=!VIRTUAL_ENV!
echo   MCP_CODER_PROJECT_DIR=!MCP_CODER_PROJECT_DIR!
echo   LLM_METHOD=!LLM_METHOD!
echo   LOG_LEVEL=!LOG_LEVEL!
echo.

REM --- Test 1: Simple prompt ---
echo === Test 1: Simple prompt ===
mcp-coder --log-level !LOG_LEVEL! prompt "What is one + 1?" ^
    --llm-method !LLM_METHOD! ^
    --mcp-config .mcp.json ^
    --output-format json ^
    --timeout 60
echo.

REM --- Test 2: Continue session ---
echo === Test 2: Continue session (multiply by two) ===
mcp-coder --log-level !LOG_LEVEL! prompt "Please multiply the result by two" ^
    --llm-method !LLM_METHOD! ^
    --mcp-config .mcp.json ^
    --continue-session ^
    --timeout 60
echo.

REM --- Test 3: MCP tool discovery ---
echo === Test 3: MCP server discovery ===
mcp-coder --log-level !LOG_LEVEL! prompt "Which MCP servers do you see? List the available tools briefly." ^
    --llm-method !LLM_METHOD! ^
    --mcp-config .mcp.json ^
    --continue-session ^
    --timeout 60
echo.

REM --- Test 4: File write via MCP ---
echo === Test 4: Write file via MCP tool ===
if exist "test.md" del "test.md"

mcp-coder --log-level !LOG_LEVEL! prompt "Please create a file called test.md with the content: Test" ^
    --llm-method !LLM_METHOD! ^
    --mcp-config .mcp.json ^
    --continue-session ^
    --timeout 120
echo.

echo --- Verifying file ---
if exist "test.md" (
    echo SUCCESS: test.md was created
    echo Contents:
    type test.md
    echo.
    del "test.md"
    echo Cleaned up test.md
) else (
    echo FAIL: test.md was not created
)

echo.
echo === All tests complete ===
