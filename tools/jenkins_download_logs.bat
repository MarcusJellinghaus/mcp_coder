@echo off
REM Download console logs of recent Jenkins builds. Usage: tools\jenkins_download_logs.bat [--limit N] [--folder PATH] [--status a,b] [--outdir DIR]
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto novenv
"%PYTHON%" "%~dp0jenkins_download_logs.py" %*
exit /b %ERRORLEVEL%
:novenv
echo ERROR: project venv Python not found: %PYTHON% 1>&2
exit /b 1
