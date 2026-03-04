#!/bin/bash
# Start MLflow UI server using tracking_uri from config.toml
# This script reads the MLflow configuration and starts the UI accordingly

set -e

echo "Reading MLflow configuration from config.toml..."

# Use Python helper to read tracking_uri from config.toml
TRACKING_URI=$(python3 tools/get_mlflow_config.py 2>/dev/null || true)

# Fallback to default if Python script fails
if [ -z "$TRACKING_URI" ]; then
    echo "Warning: Could not read config.toml, using default location"
    TRACKING_URI="sqlite:///$HOME/mlflow_data/mlflow.db"
fi

# Check if using SQLite or filesystem backend
if [[ "$TRACKING_URI" == sqlite:* ]]; then
    echo "Backend: SQLite database (recommended)"
    
    # Extract database file path from URI
    DB_PATH="${TRACKING_URI#sqlite:///}"
    DB_DIR="$(dirname "$DB_PATH")"
    
    # Create parent directory if it doesn't exist
    if [ ! -d "$DB_DIR" ]; then
        echo "Creating database directory: $DB_DIR"
        mkdir -p "$DB_DIR"
    fi
else
    echo "Backend: Filesystem (deprecated - consider switching to SQLite)"
    
    # Expand ~ if present
    TRACKING_URI="${TRACKING_URI/#\~/$HOME}"
    
    # Create directory if it doesn't exist
    if [ ! -d "$TRACKING_URI" ]; then
        echo "Creating MLflow data directory: $TRACKING_URI"
        mkdir -p "$TRACKING_URI"
    fi
fi

echo "MLflow tracking URI: $TRACKING_URI"
echo "MLflow UI will open at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start MLflow UI with explicit backend store
mlflow ui --backend-store-uri "$TRACKING_URI"
