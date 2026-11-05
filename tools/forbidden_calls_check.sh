#!/bin/bash
# Check src for git and quality-tool subprocess argv and direct mcp_workspace imports
#
# Usage from Git Bash: ./tools/forbidden_calls_check.sh

python tools/check_forbidden_calls.py "$@"
