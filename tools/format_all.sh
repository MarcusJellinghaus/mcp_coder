#!/bin/bash
# Format all Python code with black and isort

set -e  # Exit on error

echo "Formatting Python code..."
echo ""

echo "Running isort..."
isort --profile=black --float-to-top src tests

echo ""
echo "Running black..."
black src tests

echo ""
echo "✅ Formatting complete!"
