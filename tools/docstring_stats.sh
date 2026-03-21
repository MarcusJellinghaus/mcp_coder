#!/bin/bash
# Count docstring errors by type for pylint and ruff
#
# Usage from Git Bash: ./tools/docstring_stats.sh

echo "=== Pylint docstring errors ==="
pylint ./src ./tests --disable=all --enable=C0114,C0115,C0116 --score=no 2>&1 | grep -oP 'C011[456]' | sort | uniq -c | sort -rn
echo ""

echo "=== Ruff docstring errors ==="
ruff check --select D,DOC --preview src tests 2>&1 | grep -oE '[D][0-9]+|DOC[0-9]+' | sort | uniq -c | sort -rn
