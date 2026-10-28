#!/usr/bin/env bash
# Generate architecture documentation (dependency graph and report)
#
# Creates:
#   - docs/architecture/dependencies/dependency_graph.html
#   - docs/architecture/dependencies/dependency_report.html

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "$SCRIPT_DIR/tach_docs.py" "$@"
