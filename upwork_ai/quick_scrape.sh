#!/bin/bash

# Quick Scrape Script - Easy time-based filtering for Upwork scraper
# Usage: ./quick_scrape.sh [today|fresh|recent|extended]

case "$1" in
    "today")
        echo "🕐 Scraping TODAY'S jobs only (24 hours)..."
        python main.py --hours=24
        ;;
    "fresh")
        echo "🕐 Scraping FRESH jobs only (12 hours)..."
        python main.py --hours=12
        ;;
    "recent")
        echo "🕐 Scraping RECENT jobs (6 hours)..."
        python main.py --hours=6
        ;;
    "extended")
        echo "🕐 Scraping EXTENDED range (36 hours - includes some yesterday)..."
        python main.py --hours=36
        ;;
    "debug")
        echo "🔍 Running DEBUG mode with today's filter..."
        python main.py --debug --hours=24
        ;;
    *)
        echo "📋 Upwork Scraper - Time-based filtering options:"
        echo ""
        echo "   ./quick_scrape.sh today     - Only today's jobs (24 hours)"
        echo "   ./quick_scrape.sh fresh     - Fresh jobs only (12 hours)"
        echo "   ./quick_scrape.sh recent    - Recent jobs only (6 hours)"
        echo "   ./quick_scrape.sh extended  - Extended range (36 hours)"
        echo "   ./quick_scrape.sh debug     - Debug mode (24 hours)"
        echo ""
        echo "   python main.py --hours=X    - Custom hours (X = number)"
        echo "   python main.py              - Default (24 hours - today only)"
        ;;
esac