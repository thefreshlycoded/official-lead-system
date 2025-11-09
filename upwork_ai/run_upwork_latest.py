#!/usr/bin/env python3
import argparse
import os
import time
import shutil
import random
import platform
import requests
from selenium.webdriver.chrome.options import Options as SeleniumOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium_stealth import stealth
try:
    import undetected_chromedriver as uc  # optional alternative driver
except Exception:
    uc = None
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+pg8000://postgres@localhost:5432/lead_system_development")
# Force pg8000 driver if the URL came without a driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
print(f"[Scraper] Using DATABASE_URL={DATABASE_URL}")

# Behavior toggles
REQUIRE_CONTINUE = os.environ.get("REQUIRE_CONTINUE", "false").lower() in ("1", "true", "yes")
FORCE_LOGIN_PAGE = os.environ.get("FORCE_LOGIN_PAGE", "false").lower() in ("1", "true", "yes")

# Upload destination: 'db' (default) writes directly to Postgres; 'api' posts to Rails API
UPLOAD_DEST = os.environ.get("UPLOAD_DEST", "db").lower()
RAILS_API_URL = os.environ.get("RAILS_API_URL", "http://localhost:3000/api/job_listings")

# Rails communication setup
RAILS_BASE_URL = os.environ.get("RAILS_BASE_URL", "http://localhost:4242")
SCRAPER_ID = os.environ.get("SCRAPER_ID")

def send_to_rails(endpoint, data=None):
    """Send API request to Rails app"""
    if not SCRAPER_ID:
        print(f"[Warning] SCRAPER_ID not set, skipping Rails communication")
        return

    url = f"{RAILS_BASE_URL}/scrapers/{SCRAPER_ID}/{endpoint}"
    try:
        if data:
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.post(url, timeout=10)
        if response.status_code == 200:
            print(f"[Rails] {endpoint} - success")
        else:
            print(f"[Rails] {endpoint} - failed: {response.status_code}")
    except Exception as e:
        print(f"[Rails] {endpoint} - error: {e}")

def wait_for_continue(driver, target_url: str, max_wait_seconds: int = 1800):
    """Wait for explicit Continue signal when running via Rails; otherwise, allow a manual Enter fallback.

    Only after the continue is received (or manual Enter) do we probe the jobs page for accessibility.
    """
    if SCRAPER_ID:
        url = f"{RAILS_BASE_URL}/scrapers/{SCRAPER_ID}/scraper_status"
        print("[Rails] Waiting for continue signal from Rails UI…")
        while True:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if not data.get('waiting_for_continue', False):
                        print("[Rails] Continue signal received!")
                        break
                time.sleep(2)
            except Exception as e:
                print(f"[Rails] Polling error: {e}, retrying…")
                time.sleep(5)
    else:
        # Terminal/standalone use: require an explicit Enter
        try:
            input("Press Enter to continue once you've logged in…")
        except Exception:
            # If stdin is not interactive, wait a generous amount of time but don't auto-probe before the user could finish
            print("[Info] Non-interactive stdin; waiting 5 minutes before proceeding…")
            time.sleep(300)

    # After continue, ensure we can access the jobs page (handles Cloudflare/login redirects)
    print("[Wait] Checking access to jobs page…")
    start_check = time.time()
    while True:
        try:
            driver.get(target_url)
            maybe_human_pause(1.5, 2.5)
            ensure_no_challenge(driver)
            tiles = driver.find_elements(By.XPATH, "//article[@data-test='JobTile'] | //section[contains(@data-test,'job-tile')]")
            if tiles:
                print("[Wait] Jobs page accessible; continuing…")
                break
            try:
                print(f"[Wait] Still blocked; URL={driver.current_url} Title={driver.title}")
            except Exception:
                pass
        except Exception as e:
            print(f"[Wait] Probe error: {e}")
        if time.time() - start_check > max_wait_seconds:
            print("[Wait] Timed out waiting for jobs page; proceeding anyway (scrape may find 0 jobs).")
            break
        time.sleep(5)


def is_on_login_page(driver) -> bool:
    try:
        url = (driver.current_url or "").lower()
        if "/ab/account-security/login" in url:
            return True
        # Heuristic: presence of username/email input on auth page
        try:
            inputs = driver.find_elements(By.XPATH, "//input[@type='email' or @name='login' or @name='username']")
            if inputs:
                return True
        except Exception:
            pass
    except Exception:
        pass
    return False


def wait_for_user_login(driver, timeout_seconds: int = 1800) -> bool:
    """Wait on the current page until the user completes login (no navigation away beforehand)."""
    print("[Wait] Waiting for you to complete login in the browser…")
    start = time.time()
    while True:
        ensure_no_challenge(driver)
        if not is_on_login_page(driver):
            print("[Wait] Login page no longer detected; assuming login succeeded.")
            return True
        if time.time() - start > timeout_seconds:
            print("[Wait] Timed out waiting for login.")
            return False
        time.sleep(2)


def wait_until_jobs_accessible(driver, target_url: str, max_wait_seconds: int = 600) -> bool:
    print("[Wait] Checking access to jobs page…")
    start_check = time.time()
    while True:
        try:
            driver.get(target_url)
            maybe_human_pause(1.5, 2.5)
            ensure_no_challenge(driver)
            tiles = driver.find_elements(By.XPATH, "//article[@data-test='JobTile'] | //section[contains(@data-test,'job-tile')]")
            if tiles:
                print("[Wait] Jobs page accessible; continuing…")
                return True
            try:
                print(f"[Wait] Still blocked; URL={driver.current_url} Title={driver.title}")
            except Exception:
                pass
        except Exception as e:
            print(f"[Wait] Probe error: {e}")
        if time.time() - start_check > max_wait_seconds:
            print("[Wait] Timed out waiting for jobs page.")
            return False
        time.sleep(5)

def log_progress(message):
    """Send progress message to Rails for display"""
    print(f"[Progress] {message}")
    send_to_rails("add_progress", {"message": message})

# Very small, targeted scraper: open Upwork, let user log in, scrape a few pages of 'www' recent jobs,
# then POST minimal fields to Rails API. Avoids detection using undetected-chromedriver.

def find_chrome_binary():
    # Allow override via environment variable
    override = os.environ.get("CHROME_BIN")
    if override and os.path.exists(override):
        return override
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome 2.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/opt/homebrew/bin/chromium",
        "/usr/local/bin/google-chrome",
        "/usr/bin/google-chrome",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def setup_driver(driver_type: str = "selenium"):
    # We'll align UA and UA-CH to the actual Chrome version after driver starts

    # Base directories
    base_dir = os.path.join(os.getcwd(), "upwork_ai")
    os.makedirs(base_dir, exist_ok=True)

    # Stable base profile for persistent login; live in repo workspace
    stable_profile = os.path.join(base_dir, "chrome_profile")
    os.makedirs(stable_profile, exist_ok=True)

    # Create a unique temporary profile per run for fallback
    run_id = f"{int(time.time())}_{os.getpid()}"
    temp_profile = os.path.join(base_dir, f"chrome_profile_tmp_{run_id}")
    if os.path.exists(temp_profile):
        try:
            shutil.rmtree(temp_profile)
        except Exception:
            pass
    os.makedirs(temp_profile, exist_ok=True)

    # Detect if the stable profile is locked by checking Chrome's singleton lock files
    lock_files = [
        os.path.join(stable_profile, "SingletonLock"),
        os.path.join(stable_profile, "SingletonCookie"),
        os.path.join(stable_profile, "SingletonSocket"),
    ]
    use_profile = stable_profile
    waited = 0
    while any(os.path.exists(f) for f in lock_files) and waited < 60:
        if waited == 0:
            print("Stable Chrome profile appears in use; waiting up to 60s…")
        time.sleep(2)
        waited += 2
    if any(os.path.exists(f) for f in lock_files):
        print("Stable profile still locked; falling back to a temporary profile for this run.")
        # Create a brand-new unique temp dir to guarantee no lock contention
        run_id_tmp = f"{int(time.time())}_{os.getpid()}"
        use_profile = os.path.join(base_dir, f"chrome_profile_tmp_{run_id_tmp}")
        try:
            os.makedirs(use_profile, exist_ok=False)
        except Exception:
            pass

    # Set up Selenium options (used by both UC and fallback)
    sel_opts = SeleniumOptions()
    # Avoid passing a static --user-agent; we'll override via CDP to match installed Chrome
    # Keep flags minimal and realistic
    sel_opts.add_argument("--disable-blink-features=AutomationControlled")
    sel_opts.add_argument("--disable-infobars")
    sel_opts.add_argument("--no-first-run")
    sel_opts.add_argument("--no-default-browser-check")
    sel_opts.add_argument("--lang=en-US,en;q=0.9")
    sel_opts.add_argument(f"--user-data-dir={use_profile}")
    sel_opts.add_argument("--profile-directory=Default")
    # Keep browser open if the driver stops unexpectedly (prevents sudden close on edge cases)
    try:
        sel_opts.add_experimental_option("detach", True)
    except Exception:
        pass

    chrome_binary = find_chrome_binary()
    if chrome_binary:
        sel_opts.binary_location = chrome_binary
    else:
        print("Warning: Could not find a Chrome/Chromium binary in common locations. Ensure Google Chrome is installed in /Applications.")

    # Use standard Selenium by default; allow UC if requested
    print(f"[Driver] Using driver type: {driver_type}")
    print(f"[Driver] Using Chrome binary: {chrome_binary or 'auto-managed'}")
    print(f"[Driver] Using user-data-dir: {use_profile}")
    if driver_type == "uc" and uc is not None:
        try:
            try:
                uc_opts = uc.ChromeOptions()
                for arg in sel_opts.arguments:
                    uc_opts.add_argument(arg)
            except Exception:
                uc_opts = sel_opts
            driver = uc.Chrome(
                options=uc_opts,
                user_data_dir=use_profile,
                browser_executable_path=chrome_binary if chrome_binary else None,
                headless=False,
            )
        except Exception as e:
            print(f"[Driver] UC init failed ({e}); falling back to Selenium Chrome")
            driver = webdriver.Chrome(options=sel_opts)
    else:
        driver = webdriver.Chrome(options=sel_opts)

    driver.set_window_size(1280, 900)

    # Stronger stealth: navigator.webdriver, languages, plugins, vendor, platform, WebGL parameters
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": (
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"  # webdriver
                    "window.chrome = { runtime: {} };"  # window.chrome
                    "window.chrome.app = { isInstalled: false };"
                    "window.chrome.webstore = {};"
                    "Object.defineProperty(Notification, 'permission', { get: () => 'default' });"
                    "const originalQuery = window.navigator.permissions.query;"
                    "window.navigator.permissions.query = (parameters) => parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters);"
                    "Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});"  # languages
                    "Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});"  # platform
                    "Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});"  # vendor
                    "Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});"  # plugins length
                    "Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});"
                    "Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});"
                    "Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});"
                    "Object.defineProperty(navigator, 'pdfViewerEnabled', {get: () => true});"
                    "const getParameter = WebGLRenderingContext.prototype.getParameter;"  # WebGL vendor/renderer mask
                    "WebGLRenderingContext.prototype.getParameter = function(param){"
                    "  if (param === 37445) { return 'Intel Inc.'; }"  # UNMASKED_VENDOR_WEBGL
                    "  if (param === 37446) { return 'Intel Iris OpenGL Engine'; }"  # UNMASKED_RENDERER_WEBGL
                    "  return getParameter.call(this, param);"
                    "};"
                )
            },
        )
        # Keep default UA/locale/timezone from the host system; avoid suspicious overrides
    except Exception:
        pass

    # selenium-stealth helper
    try:
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="MacIntel",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except Exception:
        pass

    return driver


def wait_for_login(driver, timeout_seconds: int = 1200) -> bool:
    """
    Navigate to login, signal Rails that login is ready, then wait for continue signal from Rails UI.
    After continue signal, verify access to the protected jobs page, then continue.
    """
    login_url = 'https://www.upwork.com/ab/account-security/login'
    target_url = "https://www.upwork.com/nx/search/jobs/?q=www&sort=recency&page=1&per_page=50"
    driver.get(login_url)

    # Signal to Rails that login page is ready (no-op if SCRAPER_ID not set)
    send_to_rails("signal_login_ready")

    print("Chrome opened with Upwork login page. Please log in via the browser…")

    if REQUIRE_CONTINUE:
        # Explicit gating via Rails UI only
        print("[Mode] REQUIRE_CONTINUE=true — waiting for the Continue button in Rails UI.")
        wait_for_continue(driver, target_url, max_wait_seconds=timeout_seconds)
        return True
    else:
        # Auto-run after login is detected on the login page (no pre-login navigation)
        ok_login = wait_for_user_login(driver, timeout_seconds=timeout_seconds)
        if not ok_login:
            return False
        # Now navigate to jobs and verify access
        ok_access = wait_until_jobs_accessible(driver, target_url, max_wait_seconds=600)
        return ok_access


# removed automated credential-based login per request


def age_in_hours(label: str) -> float:
    s = (label or "").lower()
    if "just now" in s or "second" in s:
        return 0.0
    parts = s.split()
    if not parts:
        return 0.0
    try:
        n = int(parts[0])
    except Exception:
        return 0.0
    if "minute" in s:
        return n / 60.0
    if "hour" in s:
        return float(n)
    if "yesterday" in s:
        return 24.0
    if "day" in s:
        return n * 24.0
    if "week" in s:
        return n * 24.0 * 7
    if "month" in s:
        return n * 24.0 * 30
    return 0.0


def maybe_human_pause(min_s=1.5, max_s=3.5):
    time.sleep(random.uniform(min_s, max_s))


def ensure_no_challenge(driver, max_wait: int = 600):
    try:
        url = (driver.current_url or "").lower()
        title = ""
        try:
            title = (driver.title or "").lower()
        except Exception:
            pass
        challenge_tokens = ["captcha", "challenge", "verify", "cf-challenge", "cloudflare", "just a moment"]
        if any(t in url for t in challenge_tokens) or any(t in title for t in challenge_tokens):
            print("Site challenge detected. Solve it in Chrome; I'll wait…")
            start = time.time()
            while time.time() - start < max_wait:
                time.sleep(3)
                try:
                    url = (driver.current_url or "").lower()
                    title = (driver.title or "").lower()
                except Exception:
                    url = ""
                    title = ""
                if not any(t in url for t in challenge_tokens) and not any(t in title for t in challenge_tokens):
                    print("Challenge cleared; continuing…")
                    break
    except Exception:
        pass


def get_recent_job_urls(driver, max_pages: int, max_hours_old: int):
    results = []
    consecutive_old = 0
    old_limit = 5
    for page in range(1, max_pages + 1):
        url = f"https://www.upwork.com/nx/search/jobs/?q=www&sort=recency&page={page}&per_page=50"
        driver.get(url)
        maybe_human_pause(2.0, 4.0)
        ensure_no_challenge(driver)

        # Collect job tiles robustly
        job_cards = driver.find_elements(By.XPATH, "//article[@data-test='JobTile'] | //section[contains(@data-test,'job-tile')]")
        if not job_cards:
            # Extra diagnostics to help understand why we might see 0 URLs
            try:
                print(f"[Scraper] No job cards on page {page}. URL={driver.current_url} Title={driver.title}")
            except Exception:
                print(f"[Scraper] No job cards on page {page}. (Could not get URL/title)")
            break
        for card in job_cards:
            # Link
            href = None
            for xp_link in [".//h2//a", ".//h4//a", ".//a[@data-test='job-title']/@href"]:
                try:
                    if "@href" in xp_link:
                        el = card.find_element(By.XPATH, xp_link.replace("/@href", ""))
                        href = el.get_attribute("href")
                    else:
                        el = card.find_element(By.XPATH, xp_link)
                        href = el.get_attribute("href")
                    if href:
                        break
                except Exception:
                    continue

            # Date label
            label = None
            for xp_date in [
                ".//small[contains(@data-test,'published-date')]//span[last()]",
                ".//small[contains(@data-test,'pubilshed-date')]//span[last()]",
                ".//small[contains(@data-test,'posted')]//span[last()]",
                ".//small[contains(@data-test,'date')]//span[last()]",
            ]:
                try:
                    el = card.find_element(By.XPATH, xp_date)
                    label = el.text
                    if label:
                        break
                except Exception:
                    continue

            if not href:
                continue

            if age_in_hours(label) >= max_hours_old:
                consecutive_old += 1
                if consecutive_old >= old_limit:
                    return results
                continue
            consecutive_old = 0
            results.append({"url": href, "post_date": label})
        maybe_human_pause(1.5, 2.5)
    return results


def scrape_job_details(driver, job_url: str):
    driver.get(job_url)
    maybe_human_pause(1.7, 3.2)
    ensure_no_challenge(driver)
    data = {}
    try:
        data["title"] = driver.find_element(By.XPATH, "//div[contains(@class,'job-details-content')]//h4").text
    except Exception:
        pass
    try:
        data["posted_time"] = driver.find_element(By.XPATH, "//div[@data-test='PostedOn']//span").text
    except Exception:
        pass
    try:
        data["description"] = driver.find_element(By.XPATH, "//div[@data-test='Description']").text
    except Exception:
        pass
    try:
        data["location"] = driver.find_element(By.XPATH, "//div[@data-test='LocationLabel']//span").text
    except Exception:
        pass
    try:
        link_el = driver.find_element(By.XPATH, "//div[@data-test='Description']//a")
        data["job_link"] = link_el.get_attribute("href")
    except Exception:
        pass
    return data


def upsert_job(engine, job):
    sql = text(
        """
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
            fresh = EXCLUDED.fresh,
            source = EXCLUDED.source,
            listing_type = EXCLUDED.listing_type,
            updated_at = NOW();
        """
    )
    with engine.begin() as conn:
        conn.execute(sql, job)


def post_job_to_api(job):
    """Send a single job listing to the Rails API (/api/job_listings)."""
    payload = {"job_listing": job}
    try:
        resp = requests.post(RAILS_API_URL, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            return True, None
        return False, f"{resp.status_code} {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--pages", type=int, default=3)
    parser.add_argument("--driver", choices=["selenium", "uc"], default=os.environ.get("SCRAPER_DRIVER", "selenium"))
    args = parser.parse_args()

    # Build SQLAlchemy engine only in DB mode
    engine = None
    if UPLOAD_DEST == "db":
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

    driver = setup_driver(args.driver)
    print("Opening Upwork and waiting for login…")
    try:
        # Wait for user to complete login in the Chrome window, then click Continue in Rails UI
        wait_for_login(driver, timeout_seconds=600)
        log_progress("Login completed, starting to collect job URLs...")

        urls = get_recent_job_urls(driver, max_pages=args.pages, max_hours_old=args.hours)
        log_progress(f"Found {len(urls)} job URLs to scrape")

        scraped_count = 0
        for i, item in enumerate(urls, 1):
            log_progress(f"Scraping job {i}/{len(urls)}: {item.get('url', 'Unknown URL')}")

            details = scrape_job_details(driver, item["url"]) or {}
            job = {
                "job_url": item.get("url"),
                "post_date": item.get("post_date"),
                "title": details.get("title"),
                "description": details.get("description"),
                "location": details.get("location"),
                "posted_time": details.get("posted_time"),
                "job_link": details.get("job_link"),
                "fresh": False,
                "source": "upwork",
                "listing_type": "job",
            }
            try:
                if UPLOAD_DEST == "api":
                    ok, err = post_job_to_api(job)
                    if ok:
                        scraped_count += 1
                        job_title = job.get('title', 'Untitled')[:50] + ('...' if len(job.get('title', '')) > 50 else '')
                        log_progress(f"✅ Uploaded: {job_title}")
                        print(f"Uploaded: {job['job_url']}")
                    else:
                        log_progress(f"❌ Failed to upload job: {err}")
                        print(f"API error for {job['job_url']}: {err}")
                else:
                    upsert_job(engine, job)
                    scraped_count += 1
                    job_title = job.get('title', 'Untitled')[:50] + ('...' if len(job.get('title', '')) > 50 else '')
                    log_progress(f"✅ Saved: {job_title}")
                    print(f"Upserted: {job['job_url']}")
            except Exception as e:
                if UPLOAD_DEST == "api":
                    log_progress(f"❌ Failed to upload job: {e}")
                    print(f"API error for {job['job_url']}: {e}")
                else:
                    log_progress(f"❌ Failed to save job: {e}")
                    print(f"DB error for {job['job_url']}: {e}")

        log_progress(f"🎉 Scraping completed! Successfully saved {scraped_count}/{len(urls)} jobs")

        # Done: close the browser cleanly now
        try:
            driver.quit()
        except Exception:
            pass
    except Exception as e:
        # Leave the browser open so you can finish any challenges or inspect; report error to log
        print(f"[Scraper] Error before completion: {e}")
    finally:
        if engine is not None:
            try:
                engine.dispose()
            except Exception:
                pass

if __name__ == "__main__":
    main()
