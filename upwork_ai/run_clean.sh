#!/bin/bash

# Enhanced Upwork Scraper Launcher
# This script properly manages Chrome processes and prevents resource leaks

echo "🚀 Enhanced Upwork Scraper Launcher"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the upwork_ai directory."
    exit 1
fi

# Function to cleanup Chrome processes
cleanup_chrome() {
    echo "🧹 Cleaning up any existing Chrome processes..."
    pkill -f "chrome.*remote-debugging" 2>/dev/null || true
    pkill -f "chromedriver" 2>/dev/null || true
    sleep 2
}

# Function to run scraper with proper cleanup
run_scraper() {
    local mode="$1"

    echo "🔧 Preparing Chrome environment..."
    cleanup_chrome

    # Set environment variables to reduce warnings
    export PYTHONWARNINGS="ignore"
    export CHROME_LOG_FILE="/dev/null"

    echo "🏃 Starting scraper in $mode mode..."

    if [ "$mode" = "debug" ]; then
        python main.py --debug 2>/dev/null
    elif [ "$mode" = "today" ]; then
        python main.py --hours=24 2>/dev/null
    elif [ "$mode" = "fresh" ]; then
        python main.py --hours=12 2>/dev/null
    else
        python main.py 2>/dev/null
    fi

    echo "🧹 Post-run cleanup..."
    cleanup_chrome
}

# Parse command line argument
case "$1" in
    "debug")
        echo "🔍 Running in DEBUG mode - will analyze first job only"
        run_scraper "debug"
        ;;
    "today")
        echo "📅 Running for TODAY's jobs only (24 hours)"
        run_scraper "today"
        ;;
    "fresh")
        echo "🆕 Running for FRESH jobs only (12 hours)"
        run_scraper "fresh"
        ;;
    "")
        echo "🚀 Running FULL scraper (24 hours default)"
        run_scraper "full"
        ;;
    *)
        echo "Usage: $0 [debug|today|fresh]"
        echo ""
        echo "Options:"
        echo "  debug  - Debug mode: analyze first job page only"
        echo "  today  - Scrape jobs from last 24 hours only"
        echo "  fresh  - Scrape jobs from last 12 hours only"
        echo "  (none) - Full scraping with 24-hour default"
        exit 1
        ;;
esac

echo "✅ Scraper session complete!"
echo "📋 Check scraper.log for detailed results"