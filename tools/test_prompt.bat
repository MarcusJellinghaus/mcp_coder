@echo off
REM Test prompt command with both short and long inputs
REM Tests both CLI and API methods with native Claude session support
REM
REM Usage:
REM   test_prompt.bat           Run tests in normal mode (minimal output)
REM   test_prompt.bat --debug   Run tests in debug mode (shows all LLM responses)
REM
REM Parameters:
REM   --debug    Optional. Enables debug mode which displays all LLM responses
REM              and JSON outputs. Does not change the commands executed.

setlocal enabledelayedexpansion

REM Parse command line arguments
set "DEBUG_MODE=0"
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--debug" (
    set "DEBUG_MODE=1"
)
shift
goto parse_args
:args_done

echo ========================================
echo Testing MCP Coder Prompt Command
if "%DEBUG_MODE%"=="1" echo [DEBUG MODE ENABLED]
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

REM Initialize duration tracking
set "TEST1_DURATION=N/A"
set "TEST2_DURATION=N/A"
set "TEST3_DURATION=N/A"
set "TEST4_DURATION=N/A"
set "TEST5_DURATION=N/A"
set "TEST6_DURATION=N/A"

REM Test 1: Short prompt with API method
echo ========================================
echo Test 1: Short prompt with API method
echo ========================================
echo Question: 1+1
echo.
set "TEST1_START=%TIME%"
mcp-coder prompt "1+1" --llm-method claude_code_api --timeout 30 > "%TEMP%\test1_output.txt" 2>&1
set "TEST1_EXIT=!errorlevel!"
set "TEST1_END=%TIME%"
call :calculate_duration "!TEST1_START!" "!TEST1_END!" TEST1_DURATION
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Response:
    type "%TEMP%\test1_output.txt"
    echo.
)
if !TEST1_EXIT! neq 0 (
    set "TEST1_RESULT=FAILED"
    echo FAILED: Test 1 failed with exit code !TEST1_EXIT!
) else (
    set "TEST1_RESULT=PASSED"
    echo SUCCESS: Test 1 passed
)
if exist "%TEMP%\test1_output.txt" del "%TEMP%\test1_output.txt"
echo.

REM Test 2: Short prompt with CLI method
echo ========================================
echo Test 2: Short prompt with CLI method
echo ========================================
echo Question: 1+1
echo.
set "TEST2_START=%TIME%"
mcp-coder prompt "1+1" --llm-method claude_code_cli --timeout 30 > "%TEMP%\test2_output.txt" 2>&1
set "TEST2_EXIT=!errorlevel!"
set "TEST2_END=%TIME%"
call :calculate_duration "!TEST2_START!" "!TEST2_END!" TEST2_DURATION
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Response:
    type "%TEMP%\test2_output.txt"
    echo.
)
if !TEST2_EXIT! neq 0 (
    set "TEST2_RESULT=FAILED"
    echo FAILED: Test 2 failed with exit code !TEST2_EXIT!
) else (
    set "TEST2_RESULT=PASSED"
    echo SUCCESS: Test 2 passed
)
if exist "%TEMP%\test2_output.txt" del "%TEMP%\test2_output.txt"
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
set "TEST3_START=%TIME%"
mcp-coder prompt "!LONG_PROMPT!" --llm-method claude_code_api --timeout 90 > "%TEMP%\test3_output.txt" 2>&1
set "TEST3_EXIT=!errorlevel!"
set "TEST3_END=%TIME%"
call :calculate_duration "!TEST3_START!" "!TEST3_END!" TEST3_DURATION
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Response:
    type "%TEMP%\test3_output.txt"
    echo.
)
if !TEST3_EXIT! neq 0 (
    set "TEST3_RESULT=FAILED"
    echo FAILED: Test 3 failed with exit code !TEST3_EXIT!
    echo Note: Long prompts may fail due to token limits or timeout
) else (
    set "TEST3_RESULT=PASSED"
    echo SUCCESS: Test 3 passed
)
if exist "%TEMP%\test3_output.txt" del "%TEMP%\test3_output.txt"

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
set "TEST4_START=%TIME%"
mcp-coder prompt "!LONG_PROMPT!" --llm-method claude_code_cli --timeout 90 > "%TEMP%\test4_output.txt" 2>&1
set "TEST4_EXIT=!errorlevel!"
set "TEST4_END=%TIME%"
call :calculate_duration "!TEST4_START!" "!TEST4_END!" TEST4_DURATION
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Response:
    type "%TEMP%\test4_output.txt"
    echo.
)
if !TEST4_EXIT! neq 0 (
    set "TEST4_RESULT=FAILED"
    echo FAILED: Test 4 failed with exit code !TEST4_EXIT!
    echo Note: CLI method may have issues with very long prompts
) else (
    set "TEST4_RESULT=PASSED"
    echo SUCCESS: Test 4 passed
)
if exist "%TEMP%\test4_output.txt" del "%TEMP%\test4_output.txt"

REM Clean up temp file
if exist "%TEMP%\test4_prompt.txt" del "%TEMP%\test4_prompt.txt"
echo.

REM Test 5: Session continuity with API method using Claude's native sessions
echo ========================================
echo Test 5: Session continuity with API method
echo ========================================
echo Testing session continuity with API method using Claude native sessions...
echo.
set "TEST5_START=%TIME%"

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
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] First call JSON response:
    type "%TEMP%\test5_first.json"
    echo.
)
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
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Second call response:
    type "%TEMP%\test5_response.txt"
    echo.
)
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
set "TEST5_END=%TIME%"
call :calculate_duration "!TEST5_START!" "!TEST5_END!" TEST5_DURATION
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
set "TEST6_START=%TIME%"

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
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] First call JSON response:
    type "%TEMP%\test6_first.json"
    echo.
)
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
if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Second call response:
    type "%TEMP%\test6_response.txt"
    echo.
)
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
set "TEST6_END=%TIME%"
call :calculate_duration "!TEST6_START!" "!TEST6_END!" TEST6_DURATION
REM Clean up temp files
if exist "%TEMP%\test6_first.json" del "%TEMP%\test6_first.json"
if exist "%TEMP%\test6_response.txt" del "%TEMP%\test6_response.txt"
echo.

echo ========================================
echo Test Results Summary
echo %DATE% - %TIME:~0,5%
echo ========================================
echo Test 1 (Short/API):            !TEST1_RESULT!    Duration: !TEST1_DURATION!
echo Test 2 (Short/CLI):            !TEST2_RESULT!    Duration: !TEST2_DURATION!
echo Test 3 (Long/API):             !TEST3_RESULT!    Duration: !TEST3_DURATION!
echo Test 4 (Long/CLI):             !TEST4_RESULT!    Duration: !TEST4_DURATION!
echo Test 5 (Session/API):          !TEST5_RESULT!    Duration: !TEST5_DURATION!
echo Test 6 (Session/CLI):          !TEST6_RESULT!    Duration: !TEST6_DURATION!
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

if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Debug mode was enabled
    echo.
)

endlocal

REM Return failure code if any tests failed
if !FAILURES! gtr 0 exit /b 1
exit /b 0

REM Function to calculate duration between two times
:calculate_duration
setlocal enabledelayedexpansion
set "start_time=%~1"
set "end_time=%~2"
set "return_var=%~3"

REM Extract hours, minutes, seconds, and centiseconds
for /f "tokens=1-4 delims=:., " %%a in ("!start_time!") do (
    set /a start_h=%%a
    set /a start_m=%%b
    set /a start_s=%%c
    set /a start_cs=%%d
)

for /f "tokens=1-4 delims=:., " %%a in ("!end_time!") do (
    set /a end_h=%%a
    set /a end_m=%%b
    set /a end_s=%%c
    set /a end_cs=%%d
)

REM Convert to centiseconds
set /a start_total=((start_h*3600)+(start_m*60)+start_s)*100+start_cs
set /a end_total=((end_h*3600)+(end_m*60)+end_s)*100+end_cs

REM Handle midnight crossing
if !end_total! lss !start_total! set /a end_total+=8640000

REM Calculate difference
set /a diff=end_total-start_total

REM Convert back to readable format
set /a diff_s=diff/100
set /a diff_cs=diff%%100
set /a diff_m=diff_s/60
set /a diff_s=diff_s%%60

REM Format output
if !diff_m! gtr 0 (
    set "duration=!diff_m!m !diff_s!.!diff_cs!s"
) else (
    set "duration=!diff_s!.!diff_cs!s"
)

endlocal & set "%return_var%=%duration%"
goto :eof
