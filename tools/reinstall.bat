@echo off
REM Reinstall mcp-coder package in development mode
REM This script uninstalls and reinstalls the package to ensure clean installation

echo =============================================
echo MCP-Coder Package Reinstallation
echo =============================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] uv not found. Installing uv...
    pip install uv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install uv!
        echo Please install uv manually: pip install uv
        pause
        exit /b 1
    )
    echo [OK] uv installed successfully
    echo.
)
echo [OK] uv is available
echo.

REM Check if running in a virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo [ERROR] Not running in a virtual environment!
    echo.
    echo This script must be run from within a Python virtual environment.
    echo.
    echo To create a virtual environment:
    echo   python -m venv .venv
    echo.
    echo Then activate your virtual environment:
    echo   .venv\Scripts\activate
    echo.
    pause
    exit /b 1
)
echo [OK] Running in virtual environment: %VIRTUAL_ENV%
echo.

echo [1/7] Uninstalling existing packages...
echo Uninstalling mcp-coder...
uv pip uninstall mcp-coder 2>nul
echo Uninstalling mcp-config...
uv pip uninstall mcp-config 2>nul
echo Uninstalling mcp-code-checker...
uv pip uninstall mcp-code-checker 2>nul
echo Uninstalling mcp-server-filesystem...
uv pip uninstall mcp-server-filesystem 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Some packages may not have been installed
) else (
    echo [OK] Packages uninstalled successfully
)
echo.

echo [2/7] Installing package in development mode...
uv pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Package installed successfully
echo.

echo [3/7] Installing development dependencies...
uv pip install -e ".[dev]"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Development dependencies installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Development dependencies installed successfully
echo.

echo [4/7] Verifying installation...
python -c "import mcp_coder; print('mcp_coder imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Import verification failed!
    echo The mcp_coder package is not working properly.
    pause
    exit /b 1
)
echo [OK] Package import verified successfully
echo.

echo [5/7] Verifying CLI entry point...
python -c "from mcp_coder.cli.main import main; print('CLI main function imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CLI entry point verification failed!
    echo The CLI is not working properly.
    pause
    exit /b 1
)
echo [OK] CLI entry point verified successfully
echo.

echo [6/7] Testing CLI basic functionality...
echo Testing mcp-coder command without arguments (should exit with code 1):
mcp-coder
set CLI_EXIT_CODE=%ERRORLEVEL%
if %CLI_EXIT_CODE% EQU 1 (
    echo [OK] CLI basic functionality working ^(expected exit code 1^)
) else (
    echo [ERROR] CLI not working as expected ^(exit code was %CLI_EXIT_CODE%^)
)
echo.

echo [7/7] Verifying MCP servers are installed...
python -c "import mcp_code_checker; print('mcp-code-checker installed successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo Warning: mcp-code-checker not available
) else (
    echo [OK] MCP code checker verified
)
python -c "import mcp_server_filesystem; print('mcp-server-filesystem installed successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo Warning: mcp-server-filesystem not available
) else (
    echo [OK] MCP server filesystem verified
)
echo.

echo =============================================
echo Reinstallation completed successfully!
echo You can now use the mcp_coder module
echo =============================================
