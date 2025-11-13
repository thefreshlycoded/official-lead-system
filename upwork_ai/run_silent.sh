#!/bin/bash

# Ultra-Silent Upwork Scraper
# Completely suppresses all multiprocessing warnings

echo "🤫 Ultra-Silent Upwork Scraper"
echo "============================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the upwork_ai directory."
    exit 1
fi

# Function to cleanup Chrome processes
cleanup_chrome() {
    echo "🧹 Cleaning up Chrome processes..."
    pkill -f "chrome.*remote-debugging" 2>/dev/null || true
    pkill -f "chromedriver" 2>/dev/null || true
    sleep 2
}

# Function to run scraper with complete silence of warnings
run_scraper_silent() {
    local mode="$1"

    echo "🔧 Preparing silent environment..."
    cleanup_chrome

    # Set all environment variables to suppress warnings
    export PYTHONWARNINGS="ignore"
    export CHROME_LOG_FILE="/dev/null"
    export MULTIPROCESSING_RESOURCE_TRACKER="false"
    export PYTHONDONTWRITEBYTECODE=1

    echo "🏃 Starting scraper in $mode mode (all warnings suppressed)..."

    # Run with complete stderr filtering to remove resource tracker warnings
    if [ "$mode" = "debug" ]; then
        python main.py --debug 2>&1 | grep -v "resource_tracker" | grep -v "leaked semaphore"
    elif [ "$mode" = "today" ]; then
        python main.py --hours=24 2>&1 | grep -v "resource_tracker" | grep -v "leaked semaphore"
    elif [ "$mode" = "fresh" ]; then
        python main.py --hours=12 2>&1 | grep -v "resource_tracker" | grep -v "leaked semaphore"
    else
        python main.py 2>&1 | grep -v "resource_tracker" | grep -v "leaked semaphore"
    fi

    echo ""
    echo "🧹 Post-run cleanup..."
    cleanup_chrome
}

# Parse command line argument
case "$1" in
    "debug")
        echo "🔍 Running in DEBUG mode - will analyze first job only"
        run_scraper_silent "debug"
        ;;
    "today")
        echo "📅 Running for TODAY's jobs only (24 hours)"
        run_scraper_silent "today"
        ;;
    "fresh")
        echo "🆕 Running for FRESH jobs only (12 hours)"
        run_scraper_silent "fresh"
        ;;
    "")
        echo "🚀 Running FULL scraper (24 hours default)"
        run_scraper_silent "full"
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

echo "✅ Silent scraper session complete!"
echo "📋 Check scraper.log for detailed results"
echo "🤫 All resource tracker warnings have been filtered out"