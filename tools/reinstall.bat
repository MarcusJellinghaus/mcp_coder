@echo off
REM Reinstall mcp-coder package in development mode
REM This script uninstalls and reinstalls the package to ensure clean installation

echo =============================================
echo MCP-Coder Package Reinstallation
echo =============================================
echo.

echo [1/4] Uninstalling existing packages...
echo Uninstalling mcp-coder...
pip uninstall mcp-coder -y
echo Uninstalling mcp-config...
pip uninstall mcp-config -y
echo Uninstalling mcp-code-checker...
pip uninstall mcp-code-checker -y
echo Uninstalling mcp-server-filesystem...
pip uninstall mcp-server-filesystem -y
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Some packages may not have been installed
) else (
    echo [OK] Packages uninstalled successfully
)
echo.

echo [2/4] Installing package in development mode...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Package installed successfully
echo.

echo [3/4] Installing development dependencies...
pip install -e ".[dev]"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Development dependencies installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Development dependencies installed successfully
echo.

echo [4/5] Verifying installation...
python -c "import mcp_coder; print('mcp_coder imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Import verification failed!
    echo The mcp_coder package is not working properly.
    pause
    exit /b 1
)
echo [OK] Package import verified successfully
echo.

echo [4.1/5] Verifying CLI entry point...
python -c "from mcp_coder.cli.main import main; print('CLI main function imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CLI entry point verification failed!
    echo The CLI is not working properly.
    pause
    exit /b 1
)
echo [OK] CLI entry point verified successfully
echo.

echo [4.2/5] Testing CLI basic functionality...
echo Testing mcp-coder command without arguments (should exit with code 1):
mcp-coder
if %ERRORLEVEL% EQU 1 (
    echo [OK] CLI basic functionality working (expected exit code 1)
) else (
    echo [ERROR] CLI not working as expected (exit code was %ERRORLEVEL%)
)
echo.

echo [5/5] Verifying MCP servers are installed...
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
pause