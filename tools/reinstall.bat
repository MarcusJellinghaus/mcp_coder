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
    echo ✓ Packages uninstalled successfully
)
echo.

echo [2/4] Installing package in development mode...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo ✓ Package installed successfully
echo.

echo [3/4] Verifying installation...
python -c "import mcp_coder; print('mcp_coder imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Import verification failed!
    echo The mcp_coder package is not working properly.
    pause
    exit /b 1
)
echo ✓ Package import verified successfully
echo.

echo [4/4] Verifying MCP servers are installed...
python -c "import mcp_code_checker; print('mcp-code-checker installed successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo Warning: mcp-code-checker not available
) else (
    echo ✓ MCP code checker verified
)
python -c "import mcp_server_filesystem; print('mcp-server-filesystem installed successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo Warning: mcp-server-filesystem not available
) else (
    echo ✓ MCP server filesystem verified
)
echo.

echo =============================================
echo Reinstallation completed successfully!
echo You can now use the mcp_coder module
echo =============================================
pause