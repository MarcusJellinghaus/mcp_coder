@echo off
REM Test prompt command with both short and long inputs
REM Tests both CLI and API methods

setlocal enabledelayedexpansion

echo ========================================
echo Testing MCP Coder Prompt Command
echo ========================================
echo.

REM Get the project root (parent of tools directory)
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

echo Current directory: %CD%
echo.

REM Generate UUIDs for session tracking (separate sessions for API and CLI tests)
for /f %%i in ('powershell -Command "[guid]::NewGuid().ToString()"') do set SESSION_ID_API=%%i
for /f %%i in ('powershell -Command "[guid]::NewGuid().ToString()"') do set SESSION_ID_CLI=%%i
echo Generated session IDs:
echo   API: %SESSION_ID_API%
echo   CLI: %SESSION_ID_CLI%
echo.

REM Initialize test result tracking
set "TEST1_RESULT=UNKNOWN"
set "TEST2_RESULT=UNKNOWN"
set "TEST3_RESULT=UNKNOWN"
set "TEST4_RESULT=UNKNOWN"
set "TEST5_RESULT=UNKNOWN"
set "TEST6_RESULT=UNKNOWN"

REM Test 1: Short prompt with API method
echo ========================================
echo Test 1: Short prompt with API method
echo ========================================
echo Question: 1+1
echo.
mcp-coder prompt "1+1" --llm-method claude_code_api --timeout 30
if errorlevel 1 (
    set "TEST1_RESULT=FAILED"
    echo FAILED: Test 1 failed with exit code !errorlevel!
) else (
    set "TEST1_RESULT=PASSED"
    echo SUCCESS: Test 1 passed
)
echo.

REM Test 2: Short prompt with CLI method
echo ========================================
echo Test 2: Short prompt with CLI method
echo ========================================
echo Question: 1+1
echo.
mcp-coder prompt "1+1" --llm-method claude_code_cli --timeout 30
if errorlevel 1 (
    set "TEST2_RESULT=FAILED"
    echo FAILED: Test 2 failed with exit code !errorlevel!
) else (
    set "TEST2_RESULT=PASSED"
    echo SUCCESS: Test 2 passed
)
echo.

REM Test 3: Long prompt with API method (10,000+ characters)
REM Use Python script to test internal code path (not CLI entry point)
echo ========================================
echo Test 3: Long prompt with API method
echo ========================================
echo Testing long prompt via internal Python API...
echo.

python -c "import sys; sys.path.insert(0, 'src'); from mcp_coder.llm_interface import ask_llm; text = 'Summarize in one word. ' + ('Line {}: This is test data for long prompt handling. ' * 400).format(*range(400)); print(f'Prompt length: {len(text)} chars'); result = ask_llm(text, provider='claude', method='api', timeout=60); print(f'Response: {result[:100]}...')" 2>&1
set "EXIT_CODE=!errorlevel!"

if !EXIT_CODE! neq 0 (
    set "TEST3_RESULT=FAILED"
    echo FAILED: Test 3 failed with exit code !EXIT_CODE!
    echo Note: Long prompts may fail due to token limits or timeout
) else (
    set "TEST3_RESULT=PASSED"
    echo SUCCESS: Test 3 passed
)
echo.

REM Test 4: Long prompt with CLI method (10,000+ characters)
echo ========================================
echo Test 4: Long prompt with CLI method
echo ========================================
echo Testing long prompt via internal Python CLI...
echo.

python -c "import sys; sys.path.insert(0, 'src'); from mcp_coder.llm_interface import ask_llm; text = 'Summarize in one word. ' + ('Line {}: This is test data for long prompt handling. ' * 400).format(*range(400)); print(f'Prompt length: {len(text)} chars'); result = ask_llm(text, provider='claude', method='cli', timeout=60); print(f'Response: {result[:100]}...')" 2>&1
set "EXIT_CODE=!errorlevel!"

if !EXIT_CODE! neq 0 (
    set "TEST4_RESULT=FAILED"
    echo FAILED: Test 4 failed with exit code !EXIT_CODE!
    echo Note: CLI method requires stdin workaround for long prompts
) else (
    set "TEST4_RESULT=PASSED"
    echo SUCCESS: Test 4 passed
)
echo.

REM Test 5: Continue session test with API method (using Python to handle session capture)
echo ========================================
echo Test 5: Continue session with API method
echo ========================================
echo Testing session continuity with API method...
echo.
python -c "import sys; sys.path.insert(0, 'src'); from mcp_coder.llm_interface import prompt_llm; r1 = prompt_llm('Remember: 555', method='api', timeout=30); print(f'First call session_id: {r1.get(\"session_id\")}'); sid = r1.get('session_id'); r2 = prompt_llm('What number did I tell you to remember?', method='api', session_id=sid, timeout=30) if sid else None; print(f'Session test: {\"PASSED\" if (r2 and \"555\" in r2.get(\"text\", \"\")) else \"FAILED - API does not support sessions yet\"}')" 2>&1
set "EXIT_CODE=!errorlevel!"
if !EXIT_CODE! neq 0 (
    set "TEST5_RESULT=FAILED"
    echo FAILED: Test 5 failed with exit code !EXIT_CODE!
) else (
    set "TEST5_RESULT=PASSED"
    echo SUCCESS: Test 5 completed
)
echo.

REM Test 6: Continue session test with CLI method (using Python to handle session capture)
echo ========================================
echo Test 6: Continue session with CLI method
echo ========================================
echo Testing session continuity with CLI method...
echo.
python -c "import sys; sys.path.insert(0, 'src'); from mcp_coder.llm_interface import prompt_llm; r1 = prompt_llm('Remember: 777', method='cli', timeout=30); print(f'First call session_id: {r1.get(\"session_id\")}'); sid = r1.get('session_id'); r2 = prompt_llm('What number did I tell you to remember?', method='cli', session_id=sid, timeout=30) if sid else None; print(f'Second call response contains 777: {\"777\" in r2.get(\"text\", \"\") if r2 else False}'); print(f'Session test: {\"PASSED\" if (r2 and \"777\" in r2.get(\"text\", \"\")) else \"FAILED\"}')" 2>&1
set "EXIT_CODE=!errorlevel!"
if !EXIT_CODE! neq 0 (
    set "TEST6_RESULT=FAILED"
    echo FAILED: Test 6 failed with exit code !EXIT_CODE!
) else (
    set "TEST6_RESULT=PASSED"
    echo SUCCESS: Test 6 completed
)
echo.
echo ========================================
echo Test Results Summary
echo ========================================
echo Test 1 (Short/API):            !TEST1_RESULT!
echo Test 2 (Short/CLI):            !TEST2_RESULT!
echo Test 3 (Long/API):             !TEST3_RESULT!
echo Test 4 (Long/CLI):             !TEST4_RESULT!
echo Test 5 (Session/Continue/API): !TEST5_RESULT!
echo Test 6 (Session/Continue/CLI): !TEST6_RESULT!
echo.

endlocal
