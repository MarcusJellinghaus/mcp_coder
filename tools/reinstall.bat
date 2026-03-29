@echo off
setlocal enabledelayedexpansion
REM Reinstall mcp-coder package (non-editable, from PyPI)
REM For end-users. Developers should use tools\reinstall_local.bat instead.
REM Usage: call tools\reinstall.bat  (from project root)
echo =============================================
echo MCP-Coder Package Reinstallation (PyPI)
echo =============================================
echo.
echo NOTE: This installs from PyPI (non-editable).
echo       Developers should use tools\reinstall_local.bat instead.
echo.

REM Determine project root (parent of tools directory)
set "PROJECT_DIR=%~dp0.."
pushd "!PROJECT_DIR!"
set "PROJECT_DIR=%CD%"
popd

set "VENV_DIR=!PROJECT_DIR!\.venv"
set "VENV_SCRIPTS=!VENV_DIR!\Scripts"
echo [0/5] Checking Python environment...

REM Guard: if a venv is active, it must be the project-local .venv
if defined VIRTUAL_ENV (
    if /I not "!VIRTUAL_ENV!"=="!VENV_DIR!" (
        echo [FAIL] Wrong virtual environment is active!
        echo.
        echo   Active venv:   !VIRTUAL_ENV!
        echo   Expected venv: !VENV_DIR!
        echo.
        echo   Deactivate the current venv first, or activate the correct one:
        echo     !VENV_DIR!\Scripts\activate
        exit /b 1
    )
)

REM Check if uv is available
where uv >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] uv not found. Install it: pip install uv
    exit /b 1
)
echo [OK] uv found

REM Check if local .venv exists
if not exist "!VENV_SCRIPTS!\activate.bat" (
    echo Local virtual environment not found at !VENV_DIR!
    uv venv .venv
    echo Local virtual environment created at !VENV_DIR!
)
echo [OK] Target environment: !VENV_DIR!
echo.

echo [1/5] Uninstalling existing packages...
uv pip uninstall mcp-coder mcp-tools-py mcp-config mcp-workspace --python "!VENV_SCRIPTS!\python.exe" 2>nul
echo [OK] Packages uninstalled

echo.
echo [2/5] Installing mcp-coder from PyPI (non-editable)...
uv pip install "mcp-coder[dev]" --python "!VENV_SCRIPTS!\python.exe"
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] Installation failed!
    exit /b 1
)
echo [OK] Package and dev dependencies installed

echo.
echo [3/5] Verifying CLI entry points in venv...

if not exist "!VENV_SCRIPTS!\mcp-tools-py.exe" (
    echo [FAIL] mcp-tools-py.exe not found in !VENV_SCRIPTS!
    echo   The entry point was not installed into the virtual environment.
    exit /b 1
)
echo [OK] mcp-tools-py.exe found in !VENV_SCRIPTS!

if not exist "!VENV_SCRIPTS!\mcp-workspace.exe" (
    echo [FAIL] mcp-workspace.exe not found in !VENV_SCRIPTS!
    echo   The entry point was not installed into the virtual environment.
    exit /b 1
)
echo [OK] mcp-workspace.exe found in !VENV_SCRIPTS!

if not exist "!VENV_SCRIPTS!\mcp-coder.exe" (
    echo [FAIL] mcp-coder.exe not found in !VENV_SCRIPTS!
    echo   The entry point was not installed into the virtual environment.
    exit /b 1
)
echo [OK] mcp-coder.exe found in !VENV_SCRIPTS!

echo.
echo [4/5] Verifying CLI functionality...
"!VENV_SCRIPTS!\mcp-tools-py.exe" --help >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] mcp-tools-py CLI verification failed!
    exit /b 1
)
echo [OK] mcp-tools-py CLI works

"!VENV_SCRIPTS!\mcp-workspace.exe" --help >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] mcp-workspace CLI verification failed!
    exit /b 1
)
echo [OK] mcp-workspace CLI works

"!VENV_SCRIPTS!\mcp-coder.exe" --help >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] mcp-coder CLI verification failed!
    exit /b 1
)
echo [OK] mcp-coder CLI works

echo.
echo =============================================
echo [5/5] Reinstallation completed successfully!
echo.
echo Entry points installed in: !VENV_SCRIPTS!
echo   - mcp-tools-py.exe
echo   - mcp-workspace.exe
echo   - mcp-coder.exe
echo =============================================
echo.

REM Pass VENV_DIR out of setlocal scope so activation persists to caller
endlocal & set "_REINSTALL_VENV=%VENV_DIR%"

REM Deactivate wrong venv if one is active
if defined VIRTUAL_ENV (
    if not "%VIRTUAL_ENV%"=="%_REINSTALL_VENV%" (
        echo   Deactivating wrong virtual environment: %VIRTUAL_ENV%
        call deactivate 2>nul
    )
)

REM Activate the correct venv (persists to caller's shell)
if not "%VIRTUAL_ENV%"=="%_REINSTALL_VENV%" (
    echo   Activating virtual environment: %_REINSTALL_VENV%
    call "%_REINSTALL_VENV%\Scripts\activate.bat"
)

set "_REINSTALL_VENV="
