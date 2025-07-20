#!/bin/bash

# Simple build script for development
set -e

echo "🏗️  Building slack-joke-agent package..."

# Install build dependencies
echo "📦 Installing build tools..."
python3 -m pip install --upgrade pip build twine

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Run tests
echo "🧪 Running tests..."
if [ -f "test_slack_agent.py" ]; then
    python3 test_slack_agent.py
else
    echo "⚠️  No tests found - skipping test phase"
fi

# Build the package
echo "🔨 Building package..."
python3 -m build

# Check the package
echo "🔍 Checking package..."
python3 -m twine check dist/*

echo "✅ Build complete!"
echo "📁 Built packages are in: ./dist/"
ls -la dist/

echo ""
echo "🚀 To publish to Test PyPI:"
echo "python3 -m twine upload --repository testpypi dist/*"
echo ""
echo "🌟 To publish to Production PyPI:"
echo "python3 -m twine upload dist/*"