@echo off
REM Batch file to run "mcp-coder coordinator run --all" every 5 minutes
REM Press Ctrl+C to stop the loop

echo Starting mcp-coder coordinator run loop (every 5 minutes)
echo Press Ctrl+C to stop
echo.

:loop
echo ========================================
echo Running at %date% %time%
echo ========================================
mcp-coder coordinator run --all

echo.
echo Waiting 5 minutes before next run...
echo Next run at %time%
timeout /t 300 /nobreak

goto loop
