#!/bin/bash

###############################################################################
# Simple Upwork Scraper Wrapper
# Usage: bash script/scrape.sh [pages] [hours]
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PAGES=${1:-1}
HOURS=${2:-24}

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 UPWORK SCRAPER${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}⚙️  Configuration:${NC}"
echo -e "   Pages: ${GREEN}$PAGES${NC}"
echo -e "   Hours: ${GREEN}$HOURS${NC}"
echo -e "   Login: ${GREEN}REQUIRED${NC}\n"

echo -e "${YELLOW}📋 What will happen:${NC}"
echo -e "   1. Browser will open"
echo -e "   2. ${GREEN}YOU MUST LOGIN${NC} to your Upwork account"
echo -e "   3. After login, scraper runs automatically"
echo -e "   4. Jobs are saved to database\n"

echo -e "${YELLOW}ℹ️  Tips:${NC}"
echo -e "   • Keep browser open until scraper finishes"
echo -e "   • Check log: tail -f log/upwork_scraper.log"
echo -e "   • View results: rails console\n"

# Run the scraper
cd "$(dirname "$0")/.."
bash script/run_upwork_scraper.sh --hours="$HOURS" --pages="$PAGES" --require-login
