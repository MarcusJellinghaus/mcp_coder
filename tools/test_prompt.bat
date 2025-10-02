@echo off
REM Test prompt command with both short and long inputs
REM Tests both CLI and API methods with native Claude session support

setlocal enabledelayedexpansion

echo ========================================
echo Testing MCP Coder Prompt Command
echo ========================================
echo.

REM Get the project root (parent of tools directory)
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

REM Activate virtual environment if not already activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
        echo Virtual environment activated
    ) else (
        echo ERROR: Virtual environment not found at .venv\Scripts\activate.bat
        exit /b 1
    )
) else (
    echo Virtual environment already active: %VIRTUAL_ENV%
)
echo.

echo Current directory: %CD%
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
echo ========================================
echo Test 3: Long prompt with API method
echo ========================================
echo Generating long prompt (~24KB)...
echo.

REM Generate long prompt using PowerShell and save to temp file
powershell -Command "$prompt = 'Summarize in one word. '; for($i=0; $i -lt 400; $i++) { $prompt += \"Line $i`: This is test data for long prompt handling. \" }; $prompt | Out-File -FilePath '%TEMP%\test3_prompt.txt' -Encoding UTF8 -NoNewline"

REM Display prompt length
for %%A in ("%TEMP%\test3_prompt.txt") do set "PROMPT_SIZE=%%~zA"
echo Prompt length: !PROMPT_SIZE! bytes
echo.

REM Read prompt from file and pass to mcp-coder
set /p LONG_PROMPT=<"%TEMP%\test3_prompt.txt"
mcp-coder prompt "!LONG_PROMPT!" --llm-method claude_code_api --timeout 90
if errorlevel 1 (
    set "TEST3_RESULT=FAILED"
    echo FAILED: Test 3 failed with exit code !errorlevel!
    echo Note: Long prompts may fail due to token limits or timeout
) else (
    set "TEST3_RESULT=PASSED"
    echo SUCCESS: Test 3 passed
)

REM Clean up temp file
if exist "%TEMP%\test3_prompt.txt" del "%TEMP%\test3_prompt.txt"
echo.

REM Test 4: Long prompt with CLI method (10,000+ characters)
echo ========================================
echo Test 4: Long prompt with CLI method
echo ========================================
echo Generating long prompt (~24KB)...
echo.

REM Generate long prompt using PowerShell and save to temp file
powershell -Command "$prompt = 'Summarize in one word. '; for($i=0; $i -lt 400; $i++) { $prompt += \"Line $i`: This is test data for long prompt handling. \" }; $prompt | Out-File -FilePath '%TEMP%\test4_prompt.txt' -Encoding UTF8 -NoNewline"

REM Display prompt length
for %%A in ("%TEMP%\test4_prompt.txt") do set "PROMPT_SIZE=%%~zA"
echo Prompt length: !PROMPT_SIZE! bytes
echo.

REM Read prompt from file and pass to mcp-coder
set /p LONG_PROMPT=<"%TEMP%\test4_prompt.txt"
mcp-coder prompt "!LONG_PROMPT!" --llm-method claude_code_cli --timeout 90
if errorlevel 1 (
    set "TEST4_RESULT=FAILED"
    echo FAILED: Test 4 failed with exit code !errorlevel!
    echo Note: CLI method may have issues with very long prompts
) else (
    set "TEST4_RESULT=PASSED"
    echo SUCCESS: Test 4 passed
)

REM Clean up temp file
if exist "%TEMP%\test4_prompt.txt" del "%TEMP%\test4_prompt.txt"
echo.

REM Test 5: Session continuity with API method using Claude's native sessions
echo ========================================
echo Test 5: Session continuity with API method
echo ========================================
echo Testing session continuity with API method using Claude native sessions...
echo.

REM First call - establish session and capture session_id
echo First call: Setting up session with number 555...
mcp-coder prompt "Remember this number: 555. Reply with only 'OK' and nothing else." --llm-method claude_code_api --timeout 30 --output-format json > "%TEMP%\test5_first.json" 2>&1
if errorlevel 1 (
    set "TEST5_RESULT=FAILED"
    echo FAILED: Test 5 failed on first call with exit code !errorlevel!
    echo First call output:
    type "%TEMP%\test5_first.json"
    goto :test5_end
)
echo First call succeeded

REM Extract session_id from JSON output using PowerShell
set "SESSION_ID_API="
for /f "delims=" %%i in ('powershell -Command "(Get-Content '%TEMP%\test5_first.json' -Raw | ConvertFrom-Json).session_id"') do set "SESSION_ID_API=%%i"

if "%SESSION_ID_API%"=="" (
    set "TEST5_RESULT=FAILED"
    echo FAILED: Could not extract session_id from first response
    echo First call output:
    type "%TEMP%\test5_first.json"
    goto :test5_end
)

echo Extracted session_id: %SESSION_ID_API%
echo.

REM Second call - continue session using extracted session_id
echo Second call: Testing session memory with session_id...
mcp-coder prompt "What number did I tell you to remember?" --llm-method claude_code_api --session-id %SESSION_ID_API% --timeout 30 > "%TEMP%\test5_response.txt" 2>&1
if errorlevel 1 (
    set "TEST5_RESULT=FAILED"
    echo FAILED: Test 5 failed on second call with exit code !errorlevel!
    echo Second call output:
    type "%TEMP%\test5_response.txt"
    goto :test5_end
)

REM Check if response contains the number 555
findstr /i "555" "%TEMP%\test5_response.txt" > nul
if errorlevel 1 (
    set "TEST5_RESULT=FAILED"
    echo FAILED: Response does not contain "555" - session not maintained
    echo Response:
    type "%TEMP%\test5_response.txt"
) else (
    set "TEST5_RESULT=PASSED"
    echo SUCCESS: Session maintained - response contains "555"
)

:test5_end
REM Clean up temp files
if exist "%TEMP%\test5_first.json" del "%TEMP%\test5_first.json"
if exist "%TEMP%\test5_response.txt" del "%TEMP%\test5_response.txt"
echo.

REM Test 6: Session continuity with CLI method using Claude's native sessions
echo ========================================
echo Test 6: Session continuity with CLI method
echo ========================================
echo Testing session continuity with CLI method using Claude native sessions...
echo.

REM First call - establish session and capture session_id
echo First call: Setting up session with number 777...
mcp-coder prompt "Remember this number: 777. Reply with only 'OK' and nothing else." --llm-method claude_code_cli --timeout 30 --output-format json > "%TEMP%\test6_first.json" 2>&1
if errorlevel 1 (
    set "TEST6_RESULT=FAILED"
    echo FAILED: Test 6 failed on first call with exit code !errorlevel!
    echo First call output:
    type "%TEMP%\test6_first.json"
    goto :test6_end
)
echo First call succeeded

REM Extract session_id from JSON output using PowerShell
set "SESSION_ID_CLI="
for /f "delims=" %%i in ('powershell -Command "(Get-Content '%TEMP%\test6_first.json' -Raw | ConvertFrom-Json).session_id"') do set "SESSION_ID_CLI=%%i"

if "%SESSION_ID_CLI%"=="" (
    set "TEST6_RESULT=FAILED"
    echo FAILED: Could not extract session_id from first response
    echo First call output:
    type "%TEMP%\test6_first.json"
    goto :test6_end
)

echo Extracted session_id: %SESSION_ID_CLI%
echo.

REM Second call - continue session using extracted session_id
echo Second call: Testing session memory with session_id...
mcp-coder prompt "What number did I tell you to remember?" --llm-method claude_code_cli --session-id %SESSION_ID_CLI% --timeout 30 > "%TEMP%\test6_response.txt" 2>&1
if errorlevel 1 (
    set "TEST6_RESULT=FAILED"
    echo FAILED: Test 6 failed on second call with exit code !errorlevel!
    echo Second call output:
    type "%TEMP%\test6_response.txt"
    goto :test6_end
)

REM Check if response contains the number 777
findstr /i "777" "%TEMP%\test6_response.txt" > nul
if errorlevel 1 (
    set "TEST6_RESULT=FAILED"
    echo FAILED: Response does not contain "777" - session not maintained
    echo Response:
    type "%TEMP%\test6_response.txt"
) else (
    set "TEST6_RESULT=PASSED"
    echo SUCCESS: Session maintained - response contains "777"
)

:test6_end
REM Clean up temp files
if exist "%TEMP%\test6_first.json" del "%TEMP%\test6_first.json"
if exist "%TEMP%\test6_response.txt" del "%TEMP%\test6_response.txt"
echo.

echo ========================================
echo Test Results Summary
echo ========================================
echo Test 1 (Short/API):            !TEST1_RESULT!
echo Test 2 (Short/CLI):            !TEST2_RESULT!
echo Test 3 (Long/API):             !TEST3_RESULT!
echo Test 4 (Long/CLI):             !TEST4_RESULT!
echo Test 5 (Session/API):          !TEST5_RESULT!
echo Test 6 (Session/CLI):          !TEST6_RESULT!
echo.

REM Count failures
set /a FAILURES=0
if "!TEST1_RESULT!"=="FAILED" set /a FAILURES+=1
if "!TEST2_RESULT!"=="FAILED" set /a FAILURES+=1
if "!TEST3_RESULT!"=="FAILED" set /a FAILURES+=1
if "!TEST4_RESULT!"=="FAILED" set /a FAILURES+=1
if "!TEST5_RESULT!"=="FAILED" set /a FAILURES+=1
if "!TEST6_RESULT!"=="FAILED" set /a FAILURES+=1

echo Total failures: !FAILURES!/6
echo.

endlocal

REM Return failure code if any tests failed
if !FAILURES! gtr 0 exit /b 1
exit /b 0
