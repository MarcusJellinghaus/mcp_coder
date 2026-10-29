#!/usr/bin/env bash
# List recent Jenkins builds. Usage: tools/jenkins_builds.sh [--limit N] [--job PATH | --all-jobs] [--status a,b] [--name-pattern REGEX]
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/../.venv/Scripts/python.exe"
[ -x "$PYTHON" ] || PYTHON="$SCRIPT_DIR/../.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    echo "ERROR: project venv Python not found (expected $SCRIPT_DIR/../.venv/Scripts/python.exe or $SCRIPT_DIR/../.venv/bin/python)" >&2
    exit 1
fi
exec "$PYTHON" "$SCRIPT_DIR/jenkins_builds.py" "$@"
