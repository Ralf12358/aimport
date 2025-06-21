#!/bin/bash

# Test script for aimport project
# Run all unit tests using pytest

echo "Running aimport unit tests..."
echo "================================"

# Activate virtual environment and run tests
uv run python -m pytest tests/ -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed!"
    exit 1
fi
