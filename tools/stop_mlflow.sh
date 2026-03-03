#!/bin/bash
# Stop MLflow UI server
# This script finds and terminates MLflow processes

set -e

echo "============================================================"
echo "  MLflow Stop Script"
echo "============================================================"

# Find MLflow processes
echo ""
echo "Searching for MLflow processes..."

# Method 1: Look for 'mlflow ui' or 'mlflow server' processes
MLFLOW_PIDS=$(pgrep -f 'mlflow (ui|server)' 2>/dev/null || true)

# Method 2: Also check for waitress-serve (MLflow's default WSGI server)
WAITRESS_PIDS=$(pgrep -f 'waitress-serve.*mlflow' 2>/dev/null || true)

# Method 3: Check for gunicorn serving MLflow
GUNICORN_PIDS=$(pgrep -f 'gunicorn.*mlflow' 2>/dev/null || true)

# Combine all PIDs and remove duplicates
ALL_PIDS=$(echo "$MLFLOW_PIDS $WAITRESS_PIDS $GUNICORN_PIDS" | tr ' ' '\n' | sort -u | grep -v '^$' || true)

if [ -z "$ALL_PIDS" ]; then
    echo "[OK] No MLflow processes found"
    
    # Verify port 5000 is free
    if command -v lsof &> /dev/null; then
        PORT_OWNER=$(lsof -ti:5000 2>/dev/null || true)
        if [ -n "$PORT_OWNER" ]; then
            echo "[WARN] Port 5000 is in use by PID: $PORT_OWNER"
            echo "       This may not be MLflow. Check with: ps -p $PORT_OWNER -o comm="
        else
            echo "[OK] Port 5000 is free"
        fi
    fi
    
    echo ""
    echo "MLflow is stopped."
    exit 0
fi

# Display found processes
echo ""
echo "Found MLflow processes:"
for pid in $ALL_PIDS; do
    if ps -p "$pid" &>/dev/null; then
        CMD=$(ps -p "$pid" -o command= 2>/dev/null || echo "unknown")
        echo "  PID $pid: $CMD"
    fi
done

# Kill processes
echo ""
echo "Stopping MLflow processes..."
for pid in $ALL_PIDS; do
    if ps -p "$pid" &>/dev/null; then
        echo -n "  Killing PID $pid... "
        if kill "$pid" 2>/dev/null; then
            echo "[OK]"
            # Wait a moment for graceful shutdown
            sleep 1
            
            # Force kill if still running
            if ps -p "$pid" &>/dev/null; then
                echo "    Process still running, forcing termination..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        else
            echo "[FAIL] (may need sudo)"
        fi
    fi
done

# Verify processes are gone
echo ""
echo "Verification:"
sleep 1

REMAINING=$(echo "$ALL_PIDS" | tr ' ' '\n' | while read pid; do
    if [ -n "$pid" ] && ps -p "$pid" &>/dev/null; then
        echo "$pid"
    fi
done)

if [ -z "$REMAINING" ]; then
    echo "[OK] All MLflow processes stopped"
    
    # Verify port is free
    if command -v lsof &> /dev/null; then
        PORT_OWNER=$(lsof -ti:5000 2>/dev/null || true)
        if [ -n "$PORT_OWNER" ]; then
            echo "[WARN] Port 5000 still in use by PID: $PORT_OWNER"
        else
            echo "[OK] Port 5000 is free"
        fi
    fi
    
    # Test HTTP connection
    if command -v curl &> /dev/null; then
        if curl -s --connect-timeout 2 http://localhost:5000/ >/dev/null 2>&1; then
            echo "[WARN] HTTP server still responding on port 5000"
        else
            echo "[OK] HTTP server not responding"
        fi
    fi
    
    echo ""
    echo "============================================================"
    echo "SUCCESS: MLflow stopped"
    echo "============================================================"
    exit 0
else
    echo "[FAIL] Some processes still running: $REMAINING"
    echo ""
    echo "Try running with sudo:"
    echo "  sudo $0"
    exit 1
fi
