@echo off
setlocal enableextensions
python "%~dp0install.py" %*
exit /b %errorlevel%
