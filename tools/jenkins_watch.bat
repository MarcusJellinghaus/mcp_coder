@echo off
REM Watch Jenkins builds until something needs a look. Usage: tools\jenkins_watch.bat [--issue N [--repo NAME]] [--job PATH] [--watch-only] [--log-dir DIR], or --list [--issue N], or --inspect N [N ...]
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto novenv
"%PYTHON%" "%~dp0jenkins_watch.py" %*
exit /b %ERRORLEVEL%
:novenv
echo ERROR: project venv Python not found: %PYTHON% 1>&2
exit /b 1
