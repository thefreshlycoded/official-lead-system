import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import re
import time
import random
import pdb
import logging

# Configure the logging system
logging.basicConfig(
    level=logging.DEBUG,  # Log everything from DEBUG level and above
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.FileHandler("scraper.log"),  # Save logs to a file
        logging.StreamHandler()  # logger.info logs to the console
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Setting up SQLAlchemy - Connect to Rails database (lead_system_development)
DATABASE_URL = "postgresql://postgres@localhost:5432/lead_system_development"

try:
    Base = declarative_base()
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info(f"Connected to Rails database: {DATABASE_URL}")
except Exception as e:
    logger.error(f"Failed to connect to database {DATABASE_URL}: {e}")
    logger.info("Cannot proceed without database connection")
    Base = declarative_base()
    engine = None
    session = None

# Define JobListing model (mirror of Rails model)
class JobListing(Base):
    __tablename__ = 'job_listings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_url = Column(String, unique=True, nullable=False)  # Ensures unique job URLs
    title = Column(String)
    description = Column(Text)  # Use Text type for large text content (matches Rails schema)
    location = Column(String)
    post_date = Column(String)
    posted_time = Column(String)
    job_link = Column(String)
    fresh = Column(Boolean, default=True)
    source = Column(String, default="upwork")
    listing_type = Column(String, default="job")
    created_at = Column(DateTime, nullable=False, default=datetime.now)  # Rails requires this
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)  # Rails requires this

# Setup the Chrome driver with necessary options
def setup_driver():
    logger.info("Setting up Chrome driver...")
    chrome_options = uc.ChromeOptions()

    # Use modern user agent with realistic Chrome version
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Anti-detection flags
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--lang=en-US,en;q=0.9")

    # Detect Chrome binary
    chrome_binary = os.environ.get("CHROME_BIN")
    if not chrome_binary:
        # Try common locations on macOS
        common_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome 2.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
        for path in common_paths:
            if os.path.exists(path):
                chrome_binary = path
                break

    if chrome_binary:
        chrome_options.binary_location = chrome_binary
        logger.info(f"Using Chrome binary: {chrome_binary}")

    # Use subprocess=False to allow interactive login
    # Pass version parameter to match installed Chrome version (141)
    driver = uc.Chrome(options=chrome_options, use_subprocess=False, version_main=141)
    driver.set_window_size(1920, 1080)

    # Add anti-bot detection JavaScript
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": (
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                    "window.chrome = { runtime: {} };"
                    "Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});"
                    "Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});"
                )
            },
        )
    except Exception as e:
        logger.warning(f"Could not inject anti-detection scripts: {e}")

    logger.info("Chrome driver setup complete.")
    return driver

# Function to manually login and prompt user to continue after completing manual steps
def manual_login(driver):
    upwork_login_url = 'https://www.upwork.com/ab/account-security/login'
    logger.info(f"Navigating to Upwork login page: {upwork_login_url}")
    driver.get(upwork_login_url)

    # Wait for page to load
    time.sleep(3)
    logger.info("Login page loaded. Browser window is open.")
    logger.info("Please manually log in to Upwork in the browser window.")

    # Wait for user to complete login
    input("\n⏳ Once you're logged in and ready, press 'Enter' to continue...")
    logger.info("Manual login completed by the user.")


# Function to randomly wait to simulate human interaction
def human_delay(min_time=2, max_time=5):
    time.sleep(random.uniform(min_time, max_time))

# Function to convert relative time like '1 hour ago' and '2 hours ago' into a datetime object
def parse_post_date(post_date_str):
    now = datetime.now()
    post_date_str = post_date_str.lower()
    logger.debug(f"📅 Parsing date string: '{post_date_str}'")

    try:
        if 'just now' in post_date_str:
            logger.debug("   → Parsed as: just now (current time)")
            return now
        elif 'minute' in post_date_str:
            minutes = int(post_date_str.split()[0])
            result = now - timedelta(minutes=minutes)
            logger.debug(f"   → Parsed as: {minutes} minutes ago = {result}")
            return result
        elif 'hour' in post_date_str:
            hours = int(post_date_str.split()[0])
            result = now - timedelta(hours=hours)
            logger.debug(f"   → Parsed as: {hours} hours ago = {result}")
            return result
        elif 'yesterday' in post_date_str:
            yesterday = now - timedelta(days=1)
            match = re.search(r'\\d{1,2}:\\d{2} [APMapm]{2}', post_date_str)
            if match:
                time_part = datetime.strptime(match.group(), '%I:%M %p').time()
                result = datetime.combine(yesterday.date(), time_part)
                logger.debug(f"   → Parsed as: yesterday {match.group()} = {result}")
                return result
            logger.debug(f"   → Parsed as: yesterday (no time) = {yesterday}")
            return yesterday
        elif 'day' in post_date_str:
            days = int(post_date_str.split()[0])
            result = now - timedelta(days=days)
            logger.debug(f"   → Parsed as: {days} days ago = {result}")
            return result
        elif 'week' in post_date_str:
            weeks = int(post_date_str.split()[0])
            result = now - timedelta(weeks=weeks)
            logger.debug(f"   → Parsed as: {weeks} weeks ago = {result}")
            return result
        elif 'month' in post_date_str:
            months = int(post_date_str.split()[0])
            result = now - timedelta(days=30 * months)
            logger.debug(f"   → Parsed as: {months} months ago = {result}")
            return result

        logger.warning(f"⚠️  Unrecognized date format: {post_date_str}. Defaulting to current time.")
        return now
    except Exception as e:
        logger.error(f"❌ Error parsing post date: {post_date_str}. Exception: {e}")
        return now

def get_job_urls(driver, max_hours_old=72, consecutive_old_limit=5):
    logger.info(f"🎯 Starting job URL collection with parameters:")
    logger.info(f"   → Max job age: {max_hours_old/24:.1f} days ({max_hours_old} hours)")
    logger.info(f"   → Stop after {consecutive_old_limit} consecutive old jobs")

    page_number = 1
    all_job_urls = []
    jobs_url_template = "https://www.upwork.com/nx/search/jobs/?q=www&sort=recency&page={}&per_page=50"
    consecutive_old_count = 0  # Counter for consecutive old posts
    duplicate_count = 0  # Counter for consecutive duplicates
    total_processed = 0
    total_added = 0
    total_duplicates = 0
    total_too_old = 0

    while True:
        jobs_url = jobs_url_template.format(page_number)
        logger.info(f"📄 Scraping page {page_number}: {jobs_url}")
        logger.info(f"   📊 Progress so far: {total_added} jobs added, {total_duplicates} duplicates, {total_too_old} too old")

        try:
            logger.debug(f"   🌐 Navigating to page {page_number}...")
            driver.get(jobs_url)
            logger.debug(f"   ⏳ Waiting for page to load...")
            human_delay(5, 7)

            logger.debug(f"   🔍 Searching for job elements on page {page_number}...")
            job_elements = driver.find_elements(By.XPATH, "//article[@data-test='JobTile']//h2[@class='h5 mb-0 mr-2 job-tile-title']//a")
            date_elements = driver.find_elements(By.XPATH, "//article[@data-test='JobTile']//small[@data-test='job-pubilshed-date']//span[last()]")

            logger.info(f"   ✅ Found {len(job_elements)} job elements and {len(date_elements)} date elements on page {page_number}")

            if len(job_elements) == 0 or len(date_elements) == 0:
                logger.info(f"   ⛔ No more jobs found or date elements are missing on page {page_number}. Stopping pagination.")
                break

            # Filter out None URLs and ensure we have valid job URLs
            job_urls = [job.get_attribute('href') for job in job_elements if job.get_attribute('href') is not None]
            job_dates = [date.text for date in date_elements[:len(job_urls)]]  # Match the length

            logger.debug(f"   📝 Processing {len(job_urls)} valid job URLs from page {page_number}")

            for i, job_url in enumerate(job_urls):
                total_processed += 1
                logger.debug(f"      [{i+1}/{len(job_urls)}] Processing job: {job_url[:80]}...")

                try:
                    # Skip if job_url is None or empty
                    if not job_url or job_url.strip() == '':
                        logger.info(f"      ⚠️  Skipping empty or invalid job URL at index {i}")
                        continue

                    # Check for duplicates first
                    if is_job_in_database(job_url):
                        logger.debug(f"      🔄 Job URL already in database. Skipping.")
                        duplicate_count += 1
                        total_duplicates += 1
                        # If we see too many consecutive duplicates, we might be hitting old content
                        if duplicate_count >= 10:
                            logger.info(f"   ⛔ Found {duplicate_count} consecutive duplicates. Likely hitting old content. Stopping pagination.")
                            logger.info(f"   📊 Final stats: {total_added} jobs added, {total_duplicates} duplicates, {total_too_old} too old, {total_processed} total processed")
                            return all_job_urls
                        continue
                    else:
                        # Reset duplicate counter when we find a new job
                        duplicate_count = 0

                    job_date_str = job_dates[i] if i < len(job_dates) else "Unknown"
                    job_post_date = parse_post_date(job_date_str)
                    job_age_in_hours = (datetime.now() - job_post_date).total_seconds() / 3600
                    job_age_in_days = job_age_in_hours / 24
                    logger.debug(f"      📅 Posted: {job_date_str} | Age: {job_age_in_days:.1f} days ({job_age_in_hours:.1f} hours)")

                    # Check if job is older than 2 days (48 hours)
                    if job_age_in_hours >= max_hours_old:
                        logger.debug(f"      ❌ Job is older than {max_hours_old/24:.1f} days. Skipping.")
                        consecutive_old_count += 1
                        total_too_old += 1
                        # Stop sooner when hitting old content since jobs are sorted by recency
                        if consecutive_old_count >= consecutive_old_limit:
                            logger.info(f"   ⛔ Reached limit of {consecutive_old_limit} consecutive old jobs. Stopping pagination.")
                            logger.info(f"   📊 Final stats: {total_added} jobs added, {total_duplicates} duplicates, {total_too_old} too old, {total_processed} total processed")
                            return all_job_urls
                        continue

                    # Reset consecutive_old_count if a recent job is found
                    consecutive_old_count = 0
                    all_job_urls.append((job_url, job_date_str, job_post_date))
                    total_added += 1
                    logger.debug(f"      ✅ Added job {total_added}: {job_url[:60]}... (Age: {job_age_in_days:.1f}d)")
                except Exception as e:
                    logger.warning(f"      ❌ Error processing job URL {job_url}: {e}")
                    continue

            logger.info(f"   ✅ Page {page_number} complete: {len([url for url, _, _ in all_job_urls if any(url == u for u, _, _ in all_job_urls[-len(job_urls):])])} jobs added from this page")
            page_number += 1

        except Exception as e:
            logger.error(f"   ❌ Error scraping page {page_number}: {e}")
            continue

    logger.info(f"📊 Job URL collection complete! Final stats:")
    logger.info(f"   ✅ {total_added} jobs added to processing queue")
    logger.info(f"   🔄 {total_duplicates} duplicates skipped")
    logger.info(f"   ❌ {total_too_old} jobs too old")
    logger.info(f"   📄 {page_number-1} pages processed")
    logger.info(f"   📈 {total_processed} total jobs examined")
    return all_job_urls



def is_job_in_database(job_url):
    return session.query(JobListing).filter_by(job_url=job_url).first() is not None
# Function to scrape details of each job
def scrape_job_details(driver, job_url):
    logger.debug(f"      🔍 Starting detailed scrape of: {job_url}")
    job_details = {}

    try:
        logger.debug(f"         🌐 Navigating to job page...")
        driver.get(job_url)
        logger.debug(f"         ⏳ Waiting for page to load...")
        human_delay(3, 5)

        # Wait for page to load - look for common Upwork job detail page indicators
        try:
            logger.debug(f"         ⌛ Waiting for page elements to appear...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h4.d-flex span.flex-1"))
            )
            logger.debug(f"         ✅ Page loaded successfully")
        except TimeoutException:
            logger.warning(f"         ⚠️  Job details page did not load for {job_url}")
            return job_details

        # Extract title - try multiple strategies
        logger.debug(f"         📝 Extracting job title...")
        job_details['title'] = None
        try:
            # Strategy 1: h1 tag (primary modern selector)
            try:
                job_title = driver.find_element(By.TAG_NAME, "h1").text.strip()
                if job_title and len(job_title) > 5:
                    job_details['title'] = job_title
                    logger.debug(f"            ✅ Title found via H1 tag: {job_title[:60]}...")
            except:
                logger.debug(f"            ❌ No title found via H1 tag")

            # Strategy 2: h4 with span.flex-1 (Upwork Air3 design system)
            if not job_details['title']:
                try:
                    job_title = driver.find_element(By.CSS_SELECTOR, "h4.d-flex span.flex-1").text.strip()
                    if job_title and len(job_title) > 5:
                        job_details['title'] = job_title
                        logger.debug(f"            ✅ Title found via h4.d-flex > span.flex-1: {job_title[:60]}...")
                except:
                    logger.debug(f"            ❌ No title found via h4.d-flex > span.flex-1")

            # Strategy 3: h2 tag (fallback)
            if not job_details['title']:
                try:
                    job_title = driver.find_element(By.TAG_NAME, "h2").text.strip()
                    if job_title and len(job_title) > 5:
                        job_details['title'] = job_title
                        logger.info(f"✅ Extracted title via H2 tag: {job_title[:60]}...")
                except:
                    pass

            # Strategy 4: data-test attribute
            if not job_details['title']:
                try:
                    job_title = driver.find_element(By.XPATH, "//*[@data-test='JobTitle' or @data-test='job-title']").text.strip()
                    if job_title and len(job_title) > 5:
                        job_details['title'] = job_title
                        logger.info(f"✅ Extracted title via data-test: {job_title[:60]}...")
                except:
                    pass

            # Strategy 5: Any heading tag in main content area
            if not job_details['title']:
                try:
                    headings = driver.find_elements(By.XPATH, "//main//h1 | //main//h2 | //main//h3 | //article//h1 | //article//h2")
                    if headings:
                        job_title = headings[0].text.strip()
                        if job_title and len(job_title) > 5:
                            job_details['title'] = job_title
                            logger.info(f"✅ Extracted title via heading in main: {job_title[:60]}...")
                except:
                    pass

            if not job_details['title']:
                logger.warning(f"            ⚠️  Could not extract title from any selector")
        except Exception as e:
            logger.debug(f"         ❌ Error extracting title: {e}")

        # Extract description - this is the main job posting body text
        logger.debug(f"         📄 Extracting job description...")
        job_details['description'] = None
        try:
            # Strategy 1: Look for article tag (often wraps job description)
            try:
                article = driver.find_element(By.TAG_NAME, "article")
                job_description = article.text.strip()
                if job_description and len(job_description) > 20:
                    job_details['description'] = job_description
                    logger.debug(f"            ✅ Description found via ARTICLE tag ({len(job_description)} chars)")
            except:
                logger.debug(f"            ❌ No description found via ARTICLE tag")

            # Strategy 2: Look for div with data-test="Description" (Upwork Air3 design system)
            if not job_details['description']:
                try:
                    description_elem = driver.find_element(By.XPATH, "//div[@data-test='Description']")
                    job_description = description_elem.text.strip()
                    if job_description and len(job_description) > 20:
                        job_details['description'] = job_description
                        logger.info(f"✅ Extracted description via data-test='Description': {job_description[:100]}...")
                except:
                    pass

            # Strategy 3: Look for description in common div classes
            if not job_details['description']:
                try:
                    description_elem = driver.find_element(By.XPATH, "//div[contains(@class, 'description') or contains(@class, 'job-description') or contains(@class, 'details-section')]")
                    job_description = description_elem.text.strip()
                    if job_description and len(job_description) > 20:
                        job_details['description'] = job_description
                        logger.info(f"✅ Extracted description via div class: {job_description[:100]}...")
                except:
                    pass

            # Strategy 4: Look for main content area and extract largest text block
            if not job_details['description']:
                try:
                    # Find main content sections
                    main_elem = driver.find_element(By.TAG_NAME, "main")
                    # Get all divs with substantial text content
                    divs = main_elem.find_elements(By.TAG_NAME, "div")
                    largest_text = ""
                    for div in divs:
                        text = div.text.strip()
                        # Looking for substantial content (more than 20 chars, less than header/nav noise)
                        if 20 < len(text) < 10000 and len(text) > len(largest_text):
                            largest_text = text
                    if largest_text:
                        job_details['description'] = largest_text
                        logger.info(f"✅ Extracted description via main div search: {largest_text[:100]}...")
                except:
                    pass

            # Strategy 5: Look for p tags and get all text from main content area
            if not job_details['description']:
                try:
                    # Get all paragraphs that are likely job description content
                    paragraphs = driver.find_elements(By.XPATH, "//main//p | //section//p | //article//p")
                    if paragraphs:
                        job_description = "\n".join([p.text.strip() for p in paragraphs if p.text.strip() and len(p.text.strip()) > 10])
                        if len(job_description) > 20:
                            job_details['description'] = job_description
                            logger.info(f"✅ Extracted description via paragraphs: {job_description[:100]}...")
                except:
                    pass

            # Strategy 6: Get text from any section/div with substantial content after the title
            if not job_details['description']:
                try:
                    # This is a last resort - get all text after the title area
                    all_text = driver.find_element(By.TAG_NAME, "body").text
                    # Split and get the bulk of the middle content
                    lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 10]
                    if len(lines) > 5:
                        # Skip first few lines (likely title/nav) and last few (footer)
                        job_description = "\n".join(lines[2:-3]) if len(lines) > 5 else "\n".join(lines)
                        if len(job_description) > 20:
                            job_details['description'] = job_description
                            logger.info(f"✅ Extracted description via body text fallback: {job_description[:100]}...")
                except:
                    pass

            if not job_details['description']:
                logger.warning(f"            ⚠️  Could not extract description from any selector")
        except Exception as e:
            logger.debug(f"         ❌ Error extracting description: {e}")

        # Extract location
        logger.debug(f"         📍 Extracting job location...")
        job_details['location'] = None
        try:
            # Try multiple location selectors - Upwork Air3 design system
            location_xpaths = [
                # Primary: Upwork's standard location element (Air3 design)
                "//div[@class='d-inline-flex align-items-center text-base-sm']//p[@class='text-light-on-muted m-0']",
                # Fallback: Any p tag with light muted text (may catch location)
                "//p[contains(@class, 'text-light-on-muted m-0')]",
                # Old fallback: data-test attribute
                "//*[@data-test='LocationLabel']",
                # Old fallback: div with location class
                "//div[contains(@class, 'location')]/span",
                # Old fallback: Text-based search
                "//*[contains(text(), 'Location')]//following-sibling::*[1]",
            ]

            for xpath in location_xpaths:
                try:
                    location = driver.find_element(By.XPATH, xpath).text.strip()
                    if location and location != "Location" and len(location) > 0:
                        job_details['location'] = location
                        logger.debug(f"            ✅ Location found: {location}")
                        break
                except:
                    continue

            if not job_details['location']:
                logger.debug(f"            ❌ No location found via any selector")
        except Exception as e:
            logger.debug(f"         ❌ Error extracting location: {e}")

        # Extract posted time
        logger.debug(f"         ⏰ Extracting posted time...")
        job_details['posted_time'] = None
        try:
            posted_time_xpaths = [
                # Primary: Upwork Air3 design system - posted line section (gets just the time)
                "//div[@class='posted-on-line']//span",
                # Fallback: div containing "Posted" text then next span
                "//div[contains(text(), 'Posted')]//span",
                # Old fallback: data-test attribute
                "//*[@data-test='PostedOn']",
                # Old fallback: span with Posted text
                "//span[contains(text(), 'Posted')]",
                # Old fallback: time element datetime
                "//time/@datetime"
            ]

            for xpath in posted_time_xpaths:
                try:
                    # Use get_attribute for datetime, otherwise .text
                    if "@" in xpath:
                        posted_time = driver.find_element(By.XPATH, xpath.replace("/@datetime", "")).get_attribute("datetime")
                    else:
                        posted_time = driver.find_element(By.XPATH, xpath).text.strip()

                    if posted_time:
                        job_details['posted_time'] = posted_time
                        logger.debug(f"            ✅ Posted time found: {posted_time}")
                        break
                except:
                    continue

            if not job_details['posted_time']:
                logger.debug(f"            ❌ No posted time found via any selector")
        except Exception as e:
            logger.debug(f"         ❌ Error extracting posted_time: {e}")

        # Extract job link if available
        logger.debug(f"         🔗 Setting job link...")
        job_details['job_link'] = None
        try:
            # Store the current URL as the job link
            job_details['job_link'] = job_url
            logger.debug(f"            ✅ Job link set to current URL")
        except Exception as e:
            logger.debug(f"         ❌ Error setting job_link: {e}")

        # Log what we found - with special attention to title and description
        found_fields = [k for k, v in job_details.items() if v is not None]
        logger.debug(f"      📊 Scraping complete - found {len(found_fields)}/5 fields: {found_fields}")

        # Summary of critical fields
        title_status = "✅" if job_details.get('title') else "❌"
        desc_status = "✅" if job_details.get('description') else "❌"
        logger.debug(f"      🔍 Key fields: Title {title_status} | Description {desc_status}")

        if not job_details.get('title'):
            logger.warning(f"      ⚠️  MISSING TITLE - this may affect lead quality")
        if not job_details.get('description'):
            logger.warning(f"      ⚠️  MISSING DESCRIPTION - this may affect lead quality")

    except TimeoutException:
        logger.warning(f"      ⏰ Timeout while loading job details for {job_url}")
    except Exception as e:
        logger.error(f"      ❌ Scraping error for {job_url}: {e}")

    logger.debug(f"      🏁 Finished scraping job details")
    return job_details

# Function to save job listings to PostgreSQL
def save_job_listings_to_db(job_urls_with_dates):
    logger.info(f"💾 Saving {len(job_urls_with_dates)} job URLs to database...")

    jobs_added = 0
    jobs_skipped = 0

    for i, (job_url, job_date_str, job_post_date) in enumerate(job_urls_with_dates, 1):
        logger.debug(f"   [{i}/{len(job_urls_with_dates)}] Checking job: {job_url[:60]}...")

        existing_listing = session.query(JobListing).filter_by(job_url=job_url).first()
        if not existing_listing:
            now = datetime.now()
            new_job = JobListing(
                job_url=job_url,
                post_date=job_post_date,  # Store parsed datetime instead of raw string
                created_at=now,
                updated_at=now,
                fresh=True,
                source="upwork",
                listing_type="job"
            )
            session.add(new_job)
            jobs_added += 1
            logger.debug(f"      ✅ Added to session: {job_url[:60]}... (post_date: {job_date_str} → {job_post_date})")
        else:
            jobs_skipped += 1
            logger.debug(f"      🔄 Already exists in database, skipping")

    logger.info(f"   📊 Prepared for commit: {jobs_added} new jobs, {jobs_skipped} already existed")

    try:
        session.commit()
        logger.info(f"   ✅ Successfully committed {jobs_added} new jobs to database!")
        if jobs_skipped > 0:
            logger.info(f"   ℹ️  {jobs_skipped} jobs were already in database")
    except Exception as e:
        logger.error(f"   ❌ Error committing to database: {e}")
        session.rollback()
        raise

# Function to debug and inspect a job detail page
def debug_job_page(driver, job_url):
    """Visit a job page and analyze its HTML structure"""
    try:
        logger.info(f"\n{'='*80}")
        logger.info("🔍 DEBUG MODE: Inspecting job detail page")
        logger.info(f"{'='*80}\n")

        logger.info(f"Visiting job page: {job_url}")
        driver.get(job_url)
        human_delay(3, 5)

        # Save HTML to file
        page_html = driver.page_source
        output_file = "debug_job_page.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_html)
        logger.info(f"✅ Saved full HTML to: {output_file}\n")

        # Try to find title with different strategies
        logger.info("--- TITLE DETECTION ---")
        found_title = False

        try:
            h1 = driver.find_element(By.TAG_NAME, "h1")
            logger.info(f"✅ Found H1 tag: {h1.text[:100]}")
            found_title = True
        except:
            logger.info("❌ No H1 tag found")

        try:
            title_elem = driver.find_element(By.XPATH, "//*[@data-test='JobTitle' or @data-test='job-title']")
            logger.info(f"✅ Found data-test JobTitle: {title_elem.text[:100]}")
            found_title = True
        except:
            logger.info("❌ No data-test JobTitle found")

        # Try to find description with different strategies
        logger.info("\n--- DESCRIPTION DETECTION ---")
        found_desc = False

        try:
            article = driver.find_element(By.TAG_NAME, "article")
            logger.info(f"✅ Found ARTICLE tag: {article.text[:150]}")
            found_desc = True
        except:
            logger.info("❌ No ARTICLE tag found")

        try:
            desc_elem = driver.find_element(By.XPATH, "//*[@data-test='JobDescription' or @data-test='job-description']")
            logger.info(f"✅ Found data-test JobDescription: {desc_elem.text[:150]}")
            found_desc = True
        except:
            logger.info("❌ No data-test JobDescription found")

        # List all data-test attributes
        logger.info("\n--- ALL data-test ATTRIBUTES ON PAGE ---")
        data_tests = driver.find_elements(By.XPATH, "//*[@data-test]")
        data_test_values = {}
        for elem in data_tests:
            data_test = elem.get_attribute("data-test")
            text = elem.text.strip()
            if data_test and text and len(text) > 10:
                if data_test not in data_test_values:
                    data_test_values[data_test] = text[:100]

        for dt in sorted(data_test_values.keys()):
            logger.info(f"  - {dt}: {data_test_values[dt]}")

        # Check page structure
        logger.info("\n--- PAGE STRUCTURE ---")
        try:
            main = driver.find_element(By.TAG_NAME, "main")
            logger.info(f"✅ Found MAIN tag")
        except:
            logger.info("❌ No MAIN tag found")

        sections = driver.find_elements(By.TAG_NAME, "section")
        logger.info(f"Found {len(sections)} SECTION tags")

        # Get all divs with significant content
        logger.info("\n--- MAIN CONTENT DIVS ---")
        divs = driver.find_elements(By.TAG_NAME, "div")
        for i, div in enumerate(divs[:20]):
            text = div.text.strip()
            classes = div.get_attribute("class") or ""
            if text and len(text) > 50 and len(text) < 300:
                logger.info(f"DIV[{i}] classes='{classes[:60]}': {text[:80]}")

        logger.info(f"\n{'='*80}")
        logger.info("✅ Debug inspection complete!")
        logger.info(f"Full HTML saved to: {output_file}")
        logger.info(f"Open this file in a browser and inspect the element structure")
        logger.info(f"{'='*80}\n")

        return True

    except Exception as e:
        logger.error(f"Error during debug: {e}")
        return False

# Main function to execute login and scraping with pagination
def main(debug=False):
    start_time = datetime.now()
    logger.info("="*80)
    logger.info("🚀 STARTING UPWORK SCRAPER")
    logger.info(f"   Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   Debug mode: {debug}")
    logger.info("="*80)

    driver = None
    total_jobs_processed = 0
    total_jobs_scraped = 0
    total_jobs_saved = 0

    try:
        logger.info("\n🔧 PHASE 1: BROWSER SETUP")
        logger.info("Setting up Chrome driver...")
        driver = setup_driver()

        logger.info("\n🔐 PHASE 2: AUTHENTICATION")
        manual_login(driver)

        logger.info("\n🔍 PHASE 3: JOB URL COLLECTION")
        # Scrape job URLs - using 24 hours (1 day) for daily runs
        job_urls_with_dates = get_job_urls(driver, max_hours_old=24, consecutive_old_limit=5)
        logger.info(f"✅ Job URL collection complete! Found {len(job_urls_with_dates)} fresh job URLs within 24-hour limit.")

        logger.info("\n💾 PHASE 4: DATABASE INSERTION")
        save_job_listings_to_db(job_urls_with_dates)

        # Debug mode: inspect first job and exit
        if debug:
            logger.info("\n🔍 DEBUG MODE: Inspecting first job and exiting...")
            fresh_jobs = session.query(JobListing).filter_by(fresh=True).limit(1).all()
            if fresh_jobs:
                debug_job_page(driver, fresh_jobs[0].job_url)
            return

        logger.info("\n📄 PHASE 5: DETAILED SCRAPING")
        fresh_jobs = session.query(JobListing).filter_by(fresh=True).all()
        logger.info(f"Processing {len(fresh_jobs)} fresh job listings for detailed data extraction...")

        success_count = 0
        error_count = 0

        for idx, job in enumerate(fresh_jobs, 1):
            total_jobs_processed += 1
            logger.info(f"\n📋 [{idx}/{len(fresh_jobs)}] Processing Job ID {job.id}")
            logger.info(f"   URL: {job.job_url}")
            logger.info(f"   Posted: {job.post_date}")

            try:
                logger.debug(f"   🔍 Starting detailed scraping...")
                job_details = scrape_job_details(driver, job.job_url)
                total_jobs_scraped += 1

                if job_details:
                    try:
                        # Log what we're about to save
                        logger.info(f"   � Updating job with extracted details:")
                        logger.info(f"      - Title: {'✅' if job_details.get('title') else '❌'} {job_details.get('title', 'NOT FOUND')[:50]}{'...' if job_details.get('title') and len(job_details.get('title')) > 50 else ''}")
                        logger.info(f"      - Description: {'✅' if job_details.get('description') else '❌'} {len(job_details.get('description', ''))} chars")
                        logger.info(f"      - Location: {'✅' if job_details.get('location') else '❌'} {job_details.get('location', 'NOT FOUND')}")
                        logger.info(f"      - Posted time: {'✅' if job_details.get('posted_time') else '❌'} {job_details.get('posted_time', 'NOT FOUND')}")

                        job.title = job_details.get('title')
                        job.description = job_details.get('description')
                        job.location = job_details.get('location')
                        job.posted_time = job_details.get('posted_time')
                        job.job_link = job_details.get('job_link')
                        job.fresh = False
                        session.commit()

                        success_count += 1
                        total_jobs_saved += 1
                        logger.info(f"   ✅ SUCCESS: Job ID {job.id} updated in database")

                    except Exception as db_error:
                        error_count += 1
                        logger.error(f"   ❌ DATABASE ERROR for job {job.job_url}: {db_error}")
                        session.rollback()
                        # Mark as not fresh anyway so we don't retry endlessly
                        try:
                            job.fresh = False
                            session.commit()
                        except:
                            session.rollback()
                else:
                    error_count += 1
                    logger.warning(f"   ⚠️  NO DETAILS SCRAPED for {job.job_url}, marking as not fresh")
                    try:
                        job.fresh = False
                        session.commit()
                    except:
                        session.rollback()

                # Progress update every 10 jobs
                if idx % 10 == 0 or idx == len(fresh_jobs):
                    elapsed = datetime.now() - start_time
                    logger.info(f"\n📊 PROGRESS UPDATE [{idx}/{len(fresh_jobs)}]")
                    logger.info(f"   ✅ Successful: {success_count}")
                    logger.info(f"   ❌ Errors: {error_count}")
                    logger.info(f"   ⏱️  Elapsed: {elapsed}")
                    if idx > 0:
                        avg_time = elapsed.total_seconds() / idx
                        remaining = (len(fresh_jobs) - idx) * avg_time
                        logger.info(f"   🔮 ETA: {remaining/60:.1f} minutes remaining")

            except Exception as e:
                error_count += 1
                logger.error(f"   ❌ SCRAPING ERROR for job {job.job_url}: {e}")
                # Try to mark as not fresh to avoid infinite retries
                try:
                    job.fresh = False
                    session.commit()
                except:
                    session.rollback()
                # Continue to next job instead of crashing
                continue

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in main scraping loop: {e}")
    finally:
        end_time = datetime.now()
        total_duration = end_time - start_time

        logger.info("\n" + "="*80)
        logger.info("🏁 SCRAPING SESSION COMPLETE")
        logger.info(f"   Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   Total duration: {total_duration}")
        logger.info(f"   Jobs processed: {total_jobs_processed}")
        logger.info(f"   Jobs scraped: {total_jobs_scraped}")
        logger.info(f"   Jobs saved: {total_jobs_saved}")
        if total_jobs_processed > 0:
            logger.info(f"   Success rate: {(total_jobs_saved/total_jobs_processed)*100:.1f}%")
        logger.info("="*80)

        if driver:
            try:
                driver.quit()
                logger.info("🔧 Chrome driver closed.")
            except:
                logger.warning("⚠️  Error closing Chrome driver")
        if session is not None:
            try:
                session.close()
                logger.info("💾 Database session closed.")
            except:
                logger.warning("⚠️  Error closing database session")


if __name__ == "__main__":
    import sys
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    if debug_mode:
        logger.info("🔍 Running in DEBUG mode - will inspect first job and exit")
    main(debug=debug_mode)
