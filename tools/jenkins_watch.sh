#!/usr/bin/env bash
# Watch Jenkins builds until something needs a look. Usage: tools/jenkins_watch.sh [--issue N [--repo NAME]] [--job PATH] [--watch-only] [--log-dir DIR], or --list [--issue N], or --inspect N [N ...]
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/../.venv/Scripts/python.exe"
[ -x "$PYTHON" ] || PYTHON="$SCRIPT_DIR/../.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    echo "ERROR: project venv Python not found (expected $SCRIPT_DIR/../.venv/Scripts/python.exe or $SCRIPT_DIR/../.venv/bin/python)" >&2
    exit 1
fi
exec "$PYTHON" "$SCRIPT_DIR/jenkins_watch.py" "$@"
