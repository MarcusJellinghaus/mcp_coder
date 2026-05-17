#!/bin/bash
# Reinstall mcp-coder in editable mode (developer convenience).
# Delegates to ../install.sh, then activates the venv if sourced.
#
# Usage: source tools/reinstall_local.sh   (persists venv activation)
#    or: bash   tools/reinstall_local.sh   (does not persist activation)

(return 0 2>/dev/null) && _SOURCED=1 || _SOURCED=0

_SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
_SCRIPT_DIR="$( cd "$( dirname "$_SCRIPT_PATH" )" && pwd )"
REPO_DIR="$( cd "$_SCRIPT_DIR/.." && pwd )"
VENV_BIN="$REPO_DIR/.venv/bin"

if ! "$REPO_DIR/install.sh" "$REPO_DIR" \
    --source local \
    --local-path "$REPO_DIR" \
    --extras dev \
    --extra-packages "langchain langchain-anthropic mlflow" \
    --refresh; then
    echo "[FAIL] install.sh failed"
    [ "$_SOURCED" = "1" ] && return 1 || exit 1
fi

# Activate venv (only persists if this script was sourced)
if [ -n "$VIRTUAL_ENV" ] && [ "$VIRTUAL_ENV" != "$REPO_DIR/.venv" ]; then
    echo "  Deactivating wrong virtual environment: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

if [ "$VIRTUAL_ENV" != "$REPO_DIR/.venv" ]; then
    # shellcheck disable=SC1090,SC1091
    source "$VENV_BIN/activate"
fi

if [ "$_SOURCED" != "1" ]; then
    echo ""
    echo "Note: Activation does not persist because this script was not sourced."
    echo "      To activate now, run:  source $VENV_BIN/activate"
fi

unset _SOURCED _SCRIPT_PATH _SCRIPT_DIR REPO_DIR VENV_BIN
