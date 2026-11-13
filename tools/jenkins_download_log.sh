#!/usr/bin/env bash
# Download the console log of one Jenkins build. Usage: tools/jenkins_download_log.sh <job_path> <number> <output_file>
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/../.venv/Scripts/python.exe"
[ -x "$PYTHON" ] || PYTHON="$SCRIPT_DIR/../.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    echo "ERROR: project venv Python not found (expected $SCRIPT_DIR/../.venv/Scripts/python.exe or $SCRIPT_DIR/../.venv/bin/python)" >&2
    exit 1
fi
exec "$PYTHON" "$SCRIPT_DIR/jenkins_download_log.py" "$@"
