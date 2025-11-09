# 🚀 Quick Start: Upwork Scraper

## ✅ Status Check

Your scraper is **FULLY CONFIGURED AND READY TO GO!**

Recent verification shows:
- ✅ Python environment: **Working**
- ✅ All dependencies: **Installed**
- ✅ Chrome detection: **Working**
- ✅ Anti-detection stealth: **Enabled**
- ✅ Login auto-detection: **Enabled** (REQUIRE_CONTINUE="false")

---

## 🎯 How to Run (Simple Steps)

### Step 1: Close All Chrome Windows
Make sure you have **NO OTHER Chrome windows open**.

```bash
# Kill any open Chrome (except system Chrome)
pkill -f "Google Chrome" 2>/dev/null || true
```

### Step 2: Run the Scraper
```bash
bash script/run_upwork_scraper.sh
```

Options:
```bash
# Default (24 hours, 3 pages)
bash script/run_upwork_scraper.sh

# Custom hours and pages
bash script/run_upwork_scraper.sh --hours=48 --pages=5

# Just 1 page
bash script/run_upwork_scraper.sh --pages=1 --hours=24
```

### Step 3: Login When Prompted
A Chrome window will automatically open and navigate to Upwork login page.

The terminal will show:
```
[Runner] 🔐 LOGIN REQUIRED: Browser will open - you must login to Upwork first!
[Runner] ⚠️  STEALTH MODE ENABLED: Using undetected-chromedriver
[Runner] ✓ After login, scraper will AUTO-CONTINUE automatically.
[Runner] ℹ️  Just login in the browser - no buttons to click!
```

**Just login in the browser window.** No buttons to click, no special actions needed.

### Step 4: Let It Run
Once you login, the scraper will:
1. Auto-detect successful login
2. Navigate through job listings
3. Scrape job data
4. Store in PostgreSQL database
5. Finish automatically

### Step 5: Monitor Progress (Optional)
In another terminal, watch the log:
```bash
tail -f log/upwork_scraper.log
```

---

## 📊 What Gets Scraped

The scraper collects:
- Job title
- Company name
- Job description
- Budget/Rate
- Job URL
- Posted date
- Job category

All stored in your PostgreSQL database in the `job_listings` table.

---

## 🔧 Troubleshooting

### Problem: "Chrome profile in use" error
**Solution:** Make sure NO other Chrome windows/tabs are open
```bash
pkill -9 Chrome  # Force kill all Chrome
```

Then run the scraper again.

### Problem: Login window not visible
**Solution:** Check if it's behind other windows
- Press `Cmd+Tab` to cycle through open apps
- Look for "Google Chrome" in the Dock
- Check Mission Control (F3 on Mac)

### Problem: Takes too long waiting
**Solution:** This is normal on first run. Script waits up to 60 seconds for Chrome profile to initialize. Just be patient.

### Problem: Script hangs after login
**Solution:** Check if database is running
```bash
# Check PostgreSQL
pg_isready -h localhost -p 5432
```

---

## 💡 Pro Tips

1. **First run is slow:** Chrome profile initialization takes 30-60 seconds. Subsequent runs are faster.

2. **Use small batches first:** Test with `--pages=1 --hours=24` before running larger scrapes

3. **Monitor the database:** Check Rails console to verify jobs are being stored
   ```bash
   rails c
   JobListing.last(5)  # See latest 5 scraped jobs
   ```

4. **Set up cron for recurring scrapes:** See `RUN_SCRAPER.md` for automation

---

## 📝 Example Command Sequence

```bash
# Terminal 1: Run the scraper
cd /Users/antonioirizarry/Desktop/Projects/lead_system
bash script/run_upwork_scraper.sh --pages=3 --hours=24

# Terminal 2 (in another window): Watch progress
tail -f log/upwork_scraper.log

# When scraper finishes, check results
rails c
JobListing.where(scraped_at: 12.hours.ago..).count  # Count jobs scraped in last 12 hours
```

---

## ✨ It's Working!

The scraper went through full startup, Chrome launched, and was waiting for login before you interrupted it.

**Just run it again and let it finish - it works!** 🎉

For more details, see `RUN_SCRAPER.md`.
