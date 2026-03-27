@echo off
REM Manual streaming tests for issue #603
REM Usage: tools\manual_streaming_tests.bat [ndjson|text]

REM Deactivate any active venv, then activate project venv
call deactivate 2>nul
call .venv\Scripts\activate.bat

set MCPCODER=mcp-coder
set MCP_CONFIG=.mcp.json
set FMT=%~1
if "%FMT%"=="" set FMT=ndjson
REM Valid formats: text, json, session-id, ndjson, json-raw

echo === Format: %FMT% ===
echo.

echo === Test 1: Claude CLI streaming ===
%MCPCODER% prompt --llm-method claude --output-format %FMT% --timeout 60 "Count from 1 to 5, and run sleep(2) between each number. Just the numbers."
echo.

echo === Test 2: LangChain text streaming (no MCP) ===
%MCPCODER% prompt --llm-method langchain --output-format %FMT% --timeout 60 "Count from 1 to 5, and run sleep(2) between each number. Just the numbers."
echo.

echo === Test 3: LangChain agent - see MCP servers? ===
%MCPCODER% prompt --llm-method langchain --output-format %FMT% --timeout 120 --mcp-config %MCP_CONFIG% "List all MCP tools available to you, one per line."
echo.

echo === Test 4: LangChain agent - list directory ===
%MCPCODER% prompt --llm-method langchain --output-format %FMT% --timeout 120 --mcp-config %MCP_CONFIG% "Use your tools to list files in the project root directory."
echo.

echo === Test 5: LangChain agent - file lifecycle ===
%MCPCODER% prompt --llm-method langchain --output-format %FMT% --timeout 180 --mcp-config %MCP_CONFIG% "Using tools: 1) Create _test_603.txt with 'hello'. 2) Read it. 3) Edit it to 'hello streaming'. 4) Read it. 5) Delete it. 6) List dir to confirm gone."
echo.

echo === Done ===
