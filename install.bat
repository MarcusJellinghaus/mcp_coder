@echo off
setlocal enableextensions
python "%~dp0tools\install.py" %*
exit /b %errorlevel%
