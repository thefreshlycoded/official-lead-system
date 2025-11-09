#!/usr/bin/env python3
"""
Standalone Upwork scraper - no Rails integration.
Just opens Chrome, lets you log in manually, scrapes recent jobs, and saves to Postgres.
"""
import argparse
import os
import time
import shutil
import random
import requests
from selenium.webdriver.chrome.options import Options as SeleniumOptions
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium_stealth import stealth
try:
    import undetected_chromedriver as uc
except Exception:
    uc = None
from sqlalchemy import create_engine, text

# Database connection - update this for your setup
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+pg8000://postgres@localhost:5432/lead_system_development")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

print(f"[Scraper] Connecting to database: {DATABASE_URL}")

def find_chrome_binary():
    """Find Chrome binary on the system"""
    override = os.environ.get("CHROME_BIN")
    if override and os.path.exists(override):
        return override

    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome 2.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/opt/homebrew/bin/chromium",
        "/usr/local/bin/google-chrome",
        "/usr/bin/google-chrome",
    ]

    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def setup_driver(use_uc=False):
    """Set up Chrome driver with anti-detection measures"""
    # Create profile directory
    profile_dir = os.path.join(os.getcwd(), "upwork_ai", "chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)

    # Chrome options
    options = SeleniumOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--profile-directory=Default")

    # Find Chrome binary
    chrome_binary = find_chrome_binary()
    if chrome_binary:
        options.binary_location = chrome_binary
        print(f"[Driver] Using Chrome: {chrome_binary}")
    else:
        print("[Driver] Warning: Chrome not found in standard locations")

    # Create driver
    if use_uc and uc is not None:
        print("[Driver] Using undetected-chromedriver")
        try:
            driver = uc.Chrome(options=options, user_data_dir=profile_dir)
        except Exception as e:
            print(f"[Driver] UC failed: {e}, falling back to standard Selenium")
            driver = webdriver.Chrome(options=options)
    else:
        print("[Driver] Using standard Selenium WebDriver")
        driver = webdriver.Chrome(options=options)

    driver.set_window_size(1280, 900)

    # Apply stealth measures
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
                Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
                """
            }
        )
        stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="MacIntel")
    except Exception as e:
        print(f"[Driver] Stealth setup warning: {e}")

    return driver

def wait_for_login(driver):
    """Navigate to login and wait for user to complete it"""
    login_url = 'https://www.upwork.com/ab/account-security/login'
    print(f"[Login] Opening {login_url}")
    driver.get(login_url)

    print("\n" + "="*60)
    print("🚀 CHROME IS NOW OPEN - Please log in to Upwork")
    print("   1. Complete login in the browser window")
    print("   2. Solve any captcha/challenge if shown")
    print("   3. Come back here and press Enter when ready")
    print("="*60)

    input("Press Enter once you've successfully logged in...")

    # Test access to jobs page
    jobs_url = "https://www.upwork.com/nx/search/jobs/?q=www&sort=recency&page=1&per_page=50"
    print("[Login] Testing access to jobs page...")
    driver.get(jobs_url)
    time.sleep(3)

    # Check if we can see job tiles
    tiles = driver.find_elements(By.XPATH, "//article[@data-test='JobTile'] | //section[contains(@data-test,'job-tile')]")
    if tiles:
        print(f"[Login] ✅ Success! Found {len(tiles)} job tiles")
        return True
    else:
        print(f"[Login] ⚠️  No job tiles found. Current URL: {driver.current_url}")
        print("         You might need to solve a challenge or complete login")
        return False

def human_pause(min_s=1.5, max_s=3.5):
    """Random pause to mimic human behavior"""
    time.sleep(random.uniform(min_s, max_s))

def age_in_hours(date_text):
    """Convert job posting age text to hours"""
    if not date_text:
        return 0.0

    text = date_text.lower()
    if "just now" in text or "second" in text:
        return 0.0

    parts = text.split()
    if not parts:
        return 0.0

    try:
        num = int(parts[0])
    except:
        return 0.0

    if "minute" in text:
        return num / 60.0
    elif "hour" in text:
        return float(num)
    elif "yesterday" in text:
        return 24.0
    elif "day" in text:
        return num * 24.0
    elif "week" in text:
        return num * 24.0 * 7
    elif "month" in text:
        return num * 24.0 * 30

    return 0.0

def get_job_urls(driver, max_pages=3, max_hours=24):
    """Scrape job URLs from search pages"""
    print(f"[Scrape] Looking for jobs posted in last {max_hours} hours...")

    job_urls = []
    consecutive_old_jobs = 0

    for page in range(1, max_pages + 1):
        url = f"https://www.upwork.com/nx/search/jobs/?q=www&sort=recency&page={page}&per_page=50"
        print(f"[Scrape] Page {page}: {url}")

        driver.get(url)
        human_pause(2, 4)

        # Find job cards
        job_cards = driver.find_elements(By.XPATH, "//article[@data-test='JobTile'] | //section[contains(@data-test,'job-tile')]")

        if not job_cards:
            print(f"[Scrape] No job cards found on page {page}")
            break

        print(f"[Scrape] Found {len(job_cards)} jobs on page {page}")

        for card in job_cards:
            # Get job URL
            job_url = None
            try:
                link = card.find_element(By.XPATH, ".//h2//a | .//h4//a")
                job_url = link.get_attribute("href")
            except:
                continue

            if not job_url:
                continue

            # Get posting date
            date_text = None
            try:
                date_elem = card.find_element(By.XPATH, ".//small[contains(@data-test,'date') or contains(@data-test,'published')]//span[last()]")
                date_text = date_elem.text
            except:
                pass

            # Check if job is too old
            hours_old = age_in_hours(date_text)
            if hours_old >= max_hours:
                consecutive_old_jobs += 1
                if consecutive_old_jobs >= 5:  # Stop if we hit 5 old jobs in a row
                    print(f"[Scrape] Hit {consecutive_old_jobs} consecutive old jobs, stopping")
                    return job_urls
                continue

            consecutive_old_jobs = 0
            job_urls.append({"url": job_url, "post_date": date_text})

    print(f"[Scrape] Found {len(job_urls)} recent jobs")
    return job_urls

def scrape_job_details(driver, job_url):
    """Scrape details from a single job page"""
    driver.get(job_url)
    human_pause(1.5, 3)

    details = {}

    # Job title
    try:
        title = driver.find_element(By.XPATH, "//div[contains(@class,'job-details-content')]//h4")
        details["title"] = title.text
    except:
        pass

    # Description
    try:
        desc = driver.find_element(By.XPATH, "//div[@data-test='Description']")
        details["description"] = desc.text
    except:
        pass

    # Location
    try:
        location = driver.find_element(By.XPATH, "//div[@data-test='LocationLabel']//span")
        details["location"] = location.text
    except:
        pass

    # Posted time
    try:
        posted = driver.find_element(By.XPATH, "//div[@data-test='PostedOn']//span")
        details["posted_time"] = posted.text
    except:
        pass

    # External job link
    try:
        link = driver.find_element(By.XPATH, "//div[@data-test='Description']//a")
        details["job_link"] = link.get_attribute("href")
    except:
        pass

    return details

def save_job_to_db(engine, job_data):
    """Save job to database"""
    sql = text("""
        INSERT INTO job_listings (
            job_url, title, description, location, post_date, posted_time, job_link,
            fresh, source, listing_type, created_at, updated_at
        ) VALUES (
            :job_url, :title, :description, :location, :post_date, :posted_time, :job_link,
            :fresh, :source, :listing_type, NOW(), NOW()
        )
        ON CONFLICT (job_url) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            location = EXCLUDED.location,
            post_date = EXCLUDED.post_date,
            posted_time = EXCLUDED.posted_time,
            job_link = EXCLUDED.job_link,
            updated_at = NOW()
    """)

    with engine.begin() as conn:
        conn.execute(sql, job_data)

def main():
    parser = argparse.ArgumentParser(description="Standalone Upwork scraper")
    parser.add_argument("--pages", type=int, default=3, help="Max pages to scrape")
    parser.add_argument("--hours", type=int, default=24, help="Max job age in hours")
    parser.add_argument("--uc", action="store_true", help="Use undetected-chromedriver")
    args = parser.parse_args()

    print("🚀 Starting standalone Upwork scraper...")
    print(f"   Pages: {args.pages}")
    print(f"   Max age: {args.hours} hours")
    print(f"   Driver: {'undetected-chromedriver' if args.uc else 'standard selenium'}")

    # Set up database
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # Set up browser
    driver = setup_driver(use_uc=args.uc)

    try:
        # Login phase
        if not wait_for_login(driver):
            print("❌ Login failed or jobs page not accessible")
            return

        # Get job URLs
        job_urls = get_job_urls(driver, max_pages=args.pages, max_hours=args.hours)

        if not job_urls:
            print("❌ No recent jobs found")
            return

        # Scrape each job
        print(f"\n📝 Scraping {len(job_urls)} jobs...")
        saved_count = 0

        for i, job_info in enumerate(job_urls, 1):
            job_url = job_info["url"]
            print(f"[{i}/{len(job_urls)}] {job_url}")

            try:
                details = scrape_job_details(driver, job_url)

                job_data = {
                    "job_url": job_url,
                    "title": details.get("title"),
                    "description": details.get("description"),
                    "location": details.get("location"),
                    "post_date": job_info.get("post_date"),
                    "posted_time": details.get("posted_time"),
                    "job_link": details.get("job_link"),
                    "fresh": False,
                    "source": "upwork",
                    "listing_type": "job"
                }

                save_job_to_db(engine, job_data)
                saved_count += 1

                title = details.get("title", "Untitled")[:50]
                print(f"     ✅ Saved: {title}")

            except Exception as e:
                print(f"     ❌ Error: {e}")

        print(f"\n🎉 Done! Saved {saved_count}/{len(job_urls)} jobs to database")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        engine.dispose()

if __name__ == "__main__":
    main()