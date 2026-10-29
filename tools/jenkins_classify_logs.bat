@echo off
REM Tag downloaded Jenkins console logs with known issue ids. Usage: tools\jenkins_classify_logs.bat [--logdir DIR] [--patterns FILE]
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto novenv
"%PYTHON%" "%~dp0jenkins_classify_logs.py" %*
exit /b %ERRORLEVEL%
:novenv
echo ERROR: project venv Python not found: %PYTHON% 1>&2
exit /b 1
