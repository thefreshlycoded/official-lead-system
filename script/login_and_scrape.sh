#!/bin/bash

###############################################################################
# Interactive Upwork Scraper with Login Instructions
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔐 UPWORK SCRAPER LOGIN INSTRUCTIONS${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}Step 1: Browser Should Be Opening${NC}"
echo -e "   Looking for Chrome window with Upwork login page..."
echo -e "   If you don't see it, check behind other windows!\n"

echo -e "${YELLOW}Step 2: Find Chrome Browser${NC}"
echo -e "   • Look at your desktop"
echo -e "   • Check taskbar/dock"
echo -e "   • Click on Chrome icon if needed\n"

echo -e "${YELLOW}Step 3: Login to Upwork${NC}"
echo -e "   When Chrome opens, you'll see:"
echo -e "   ┌─────────────────────────────────┐"
echo -e "   │ Upwork Login Page               │"
echo -e "   │ ─────────────────────────────   │"
echo -e "   │ Email: [_______________]        │"
echo -e "   │ Password: [_______________]     │"
echo -e "   └─────────────────────────────────┘\n"

echo -e "${YELLOW}Step 4: Enter Your Credentials${NC}"
echo -e "   • Email: Your Upwork email"
echo -e "   • Password: Your Upwork password"
echo -e "   • 2FA: Complete if prompted\n"

echo -e "${YELLOW}Step 5: Wait for Scraper${NC}"
echo -e "   After login, scraper will:"
echo -e "   ✓ Navigate to jobs page"
echo -e "   ✓ Collect job listings"
echo -e "   ✓ Save to database"
echo -e "   ✓ Exit automatically\n"

echo -e "${YELLOW}Step 6: Monitor Progress${NC}"
echo -e "   Open another terminal and run:"
echo -e "   ${GREEN}tail -f log/upwork_scraper.log${NC}\n"

read -p "Press Enter when you're ready to start the scraper..."

echo -e "\n${BLUE}Starting scraper now...${NC}\n"

cd /Users/antonioirizarry/Desktop/Projects/lead_system

# Start the scraper
bash script/run_upwork_scraper.sh --hours=24 --pages=1 --require-login

echo -e "\n${GREEN}✅ Scraper finished!${NC}"
echo -e "Check your database:"
echo -e "${GREEN}rails console${NC}"
echo -e "${GREEN}JobListing.count${NC}\n"
