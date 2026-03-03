@echo off
setlocal enabledelayedexpansion
REM Start MLflow UI server using tracking_uri from config.toml
REM This script reads the MLflow configuration and starts the UI accordingly

echo Reading MLflow configuration from config.toml...

REM Use Python helper to read tracking_uri from config.toml
for /f "usebackq delims=" %%i in (`python tools\get_mlflow_config.py 2^>nul`) do set TRACKING_URI=%%i

REM Fallback to default if Python script fails
if "!TRACKING_URI!"=="" (
    echo Warning: Could not read config.toml, using default location
    set TRACKING_URI=sqlite:///%USERPROFILE%/mlflow_data/mlflow.db
)

REM Check if using SQLite backend by checking first 9 characters
set "FIRST_CHARS=!TRACKING_URI:~0,9!"

if "!FIRST_CHARS!"=="sqlite://" (
    echo Backend: SQLite database (recommended^)
    
    REM Extract database file path from URI (remove sqlite:///)
    set DB_PATH=!TRACKING_URI:~10!
    
    REM Convert forward slashes to backslashes for Windows directory operations
    set DB_PATH_WIN=!DB_PATH:/=\!
    
    REM Get parent directory
    for %%F in ("!DB_PATH_WIN!") do set DB_DIR=%%~dpF
    
    REM Create parent directory if it doesn't exist
    if not exist "!DB_DIR!" (
        echo Creating database directory: !DB_DIR!
        mkdir "!DB_DIR!"
    )
    
    REM TRACKING_URI stays as SQLite URI (no modification needed)
) else (
    echo Backend: Filesystem (deprecated - consider switching to SQLite^)
    
    REM Convert forward slashes to backslashes for directory operations
    set TRACKING_DIR_WIN=!TRACKING_URI:/=\!
    
    REM Create directory if it doesn't exist
    if not exist "!TRACKING_DIR_WIN!" (
        echo Creating MLflow data directory: !TRACKING_DIR_WIN!
        mkdir "!TRACKING_DIR_WIN!"
    )
    
    REM Add file:/// prefix for filesystem backend on Windows
    set TRACKING_URI=file:///!TRACKING_URI!
)

echo MLflow tracking URI: !TRACKING_URI!
echo MLflow UI will open at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start MLflow UI with explicit backend store
mlflow ui --backend-store-uri "!TRACKING_URI!"

endlocal
