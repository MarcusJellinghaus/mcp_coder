@echo off
REM List recent Jenkins builds. Usage: tools\jenkins_builds.bat [--limit N] [--job PATH | --all-jobs] [--status a,b] [--name-pattern REGEX]
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto novenv
"%PYTHON%" "%~dp0jenkins_builds.py" %*
exit /b %ERRORLEVEL%
:novenv
echo ERROR: project venv Python not found: %PYTHON% 1>&2
exit /b 1
