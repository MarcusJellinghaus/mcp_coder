@echo off
REM Download the console log of one Jenkins build. Usage: tools\jenkins_download_log.bat <job_path> <number> <output_file>
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto novenv
"%PYTHON%" "%~dp0jenkins_download_log.py" %*
exit /b %ERRORLEVEL%
:novenv
echo ERROR: project venv Python not found: %PYTHON% 1>&2
exit /b 1
