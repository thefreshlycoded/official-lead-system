#!/bin/bash

# Quick Reference: Undetected ChromeDriver Commands
# Usage: source this file or run individual commands

echo "=== Undetected ChromeDriver Quick Commands ==="

# View latest logs
alias scraper-logs="tail -100f upwork_ai/scraper.log"

# Install/update dependencies
update-deps() {
    cd upwork_ai
    pip install -r requirements.txt --upgrade
    cd ..
}

# Run main scraper
run-main() {
    cd upwork_ai
    python main.py
}

# Run with Rails integration
run-rails() {
    export RAILS_BASE_URL="http://localhost:3000"
    export UPLOAD_DEST="api"
    cd upwork_ai
    python run_upwork_latest.py
}

# Run standalone scraper with undetected-chromedriver
run-uc() {
    cd upwork_ai
    python run_standalone.py --uc
}

# Run standalone with standard selenium
run-selenium() {
    cd upwork_ai
    python run_standalone.py
}

# Clean temp profiles
clean-profiles() {
    find upwork_ai/chrome_profile_tmp_* -delete 2>/dev/null
    echo "✅ Cleaned temporary profiles"
}

# Clean all profiles (caution: removes saved login data)
clean-all-profiles() {
    read -p "⚠️  This will remove all saved login data. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf upwork_ai/chrome_profile upwork_ai/chrome_profile_tmp_*
        echo "✅ All profiles removed"
    else
        echo "Cancelled"
    fi
}

# Kill stuck Chrome processes
kill-chrome() {
    killall -9 chromedriver 2>/dev/null
    killall -9 "Google Chrome" 2>/dev/null
    echo "✅ Chrome processes terminated"
}

# Check Chrome version
check-chrome() {
    chrome_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if [ -x "$chrome_path" ]; then
        "$chrome_path" --version
    else
        echo "Chrome not found at: $chrome_path"
    fi
}

# Set Chrome binary location
set-chrome-bin() {
    chrome_path="${1:---interactive}"
    if [ "$chrome_path" = "--interactive" ]; then
        echo "Available Chrome binaries:"
        ls -la /Applications/ | grep -i chrome
        read -p "Enter full path to Chrome binary: " chrome_path
    fi
    export CHROME_BIN="$chrome_path"
    echo "✅ CHROME_BIN set to: $CHROME_BIN"
}

# Test UC connectivity
test-upwork() {
    cd upwork_ai
    python3 << 'EOF'
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

try:
    print("[Test] Initializing undetected-chromedriver...")
    driver = uc.Chrome()
    print("✅ Driver initialized successfully")

    print("[Test] Navigating to Upwork...")
    driver.get("https://www.upwork.com")

    print("[Test] Checking page load...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    print("✅ Page loaded successfully")
    print(f"    Title: {driver.title}")
    print(f"    URL: {driver.current_url}")

    driver.quit()
    print("✅ Test completed - UC is working!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
EOF
    cd ..
}

# Show environment setup
show-env() {
    echo "Current Environment:"
    echo "  Python: $(python --version)"
    echo "  UC Version: $(pip show undetected-chromedriver | grep Version)"
    echo "  Selenium Version: $(pip show selenium | grep Version)"
    echo "  Chrome: $(check-chrome)"
    echo ""
    echo "Environment Variables:"
    [ -n "$CHROME_BIN" ] && echo "  CHROME_BIN: $CHROME_BIN" || echo "  CHROME_BIN: (not set)"
    [ -n "$RAILS_BASE_URL" ] && echo "  RAILS_BASE_URL: $RAILS_BASE_URL" || echo "  RAILS_BASE_URL: (not set)"
    [ -n "$SCRAPER_ID" ] && echo "  SCRAPER_ID: $SCRAPER_ID" || echo "  SCRAPER_ID: (not set)"
}

# Help menu
help-uc() {
    cat << 'EOF'
Undetected ChromeDriver Quick Reference
=========================================

INSTALLATION & SETUP:
  update-deps              - Install/upgrade all dependencies
  check-chrome             - Check installed Chrome version
  set-chrome-bin [path]    - Set custom Chrome binary location
  show-env                 - Show current environment setup

RUNNING SCRAPERS:
  run-main                 - Run main.py scraper
  run-rails                - Run with Rails integration
  run-uc                   - Run standalone with UC
  run-selenium             - Run standalone with Selenium

MAINTENANCE:
  scraper-logs             - View latest scraper logs (tail)
  clean-profiles           - Remove temp profiles
  clean-all-profiles       - Remove all profiles (with confirmation)
  kill-chrome              - Kill stuck Chrome processes

TESTING & DIAGNOSTICS:
  test-upwork              - Test UC connectivity to Upwork
  show-env                 - Show environment variables

HELP:
  help-uc                  - Show this help menu

EXAMPLES:
  $ update-deps
  $ check-chrome
  $ test-upwork
  $ run-uc
  $ scraper-logs
  $ clean-profiles
EOF
}

# Print help if requested
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    help-uc
fi

echo ""
echo "Commands loaded! Type 'help-uc' for more info."
