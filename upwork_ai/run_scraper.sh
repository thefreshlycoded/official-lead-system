#!/bin/bash

# Standalone Upwork Scraper Runner
# This script sets up the environment and runs the Python scraper

set -e

echo "🚀 Upwork Standalone Scraper"
echo "============================"

# Navigate to the upwork_ai directory
cd "$(dirname "$0")"

# Check if virtual environment exists, create if not
if [ ! -d "upwork_scraper_env" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv upwork_scraper_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source upwork_scraper_env/bin/activate

# Verify we're using the right Python
echo "   Using Python: $(which python3)"
echo "   Using pip: $(which pip)"

# Install/upgrade requirements
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set default database URL if not provided
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="postgresql+pg8000://postgres@localhost:5432/lead_system_development"
    echo "🗄️  Using default database: $DATABASE_URL"
fi

# Check for Chrome
echo "🌐 Checking for Chrome..."
if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo "   ✅ Found Google Chrome"
elif [ -f "/Applications/Google Chrome 2.app/Contents/MacOS/Google Chrome" ]; then
    echo "   ✅ Found Google Chrome 2"
elif [ -f "/Applications/Chromium.app/Contents/MacOS/Chromium" ]; then
    echo "   ✅ Found Chromium"
else
    echo "   ⚠️  Chrome not found in standard locations"
    echo "      Make sure Chrome is installed in /Applications/"
fi

echo ""
echo "🎯 Starting scraper..."
echo "   Database: $DATABASE_URL"
echo "   Python executable: $(which python3)"
echo ""

# Run the scraper with arguments passed to this script
# Make sure we're using the venv's python
upwork_scraper_env/bin/python3 run_standalone.py "$@"

echo ""
echo "✨ Scraper finished!"