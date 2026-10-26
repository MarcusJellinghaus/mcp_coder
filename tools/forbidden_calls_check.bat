@echo off
REM Check src for git subprocess argv and direct mcp_workspace imports
REM
REM Usage from cmd.exe: tools\forbidden_calls_check.bat

python tools\check_forbidden_calls.py %*
exit /b %ERRORLEVEL%
