#!/usr/bin/env python
"""
Debug script to inspect job detail pages and figure out correct CSS/XPath selectors
"""

import logging
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the upwork_ai directory to path so we can import from main.py
sys.path.insert(0, '/Users/antonioirizarry/Desktop/Projects/lead_system/upwork_ai')
from main import JobListing, Base, setup_driver, manual_login

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "postgresql://postgres@localhost:5432/lead_system_development"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

def inspect_job_page(driver, job_url, output_file):
    """Visit a job page and save the HTML for inspection"""
    try:
        logger.info(f"Visiting job page: {job_url}")
        driver.get(job_url)
        time.sleep(5)  # Let page load

        # Get full page HTML
        page_html = driver.page_source

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_html)

        logger.info(f"✅ Saved HTML to {output_file}")

        # Try to find and print key elements
        logger.info("\n=== ELEMENT INSPECTION ===\n")

        # Try to find title
        logger.info("--- LOOKING FOR TITLE ---")
        try:
            h1 = driver.find_element(By.TAG_NAME, "h1")
            logger.info(f"✅ Found H1: {h1.text[:100]}")
        except:
            logger.info("❌ No H1 found")

        try:
            data_test_title = driver.find_element(By.XPATH, "//*[@data-test='JobTitle' or @data-test='job-title']")
            logger.info(f"✅ Found data-test JobTitle: {data_test_title.text[:100]}")
        except:
            logger.info("❌ No data-test JobTitle found")

        # Try to find description
        logger.info("\n--- LOOKING FOR DESCRIPTION ---")
        try:
            article = driver.find_element(By.TAG_NAME, "article")
            logger.info(f"✅ Found ARTICLE tag: {article.text[:200]}")
        except:
            logger.info("❌ No ARTICLE tag found")

        try:
            data_test_desc = driver.find_element(By.XPATH, "//*[@data-test='JobDescription' or @data-test='job-description']")
            logger.info(f"✅ Found data-test JobDescription: {data_test_desc.text[:200]}")
        except:
            logger.info("❌ No data-test JobDescription found")

        try:
            desc_div = driver.find_element(By.XPATH, "//div[contains(@class, 'description')]")
            logger.info(f"✅ Found description div: {desc_div.text[:200]}")
        except:
            logger.info("❌ No description div found")

        # List all data-test attributes on page
        logger.info("\n--- ALL data-test ATTRIBUTES ON PAGE ---")
        data_tests = driver.find_elements(By.XPATH, "//*[@data-test]")
        data_test_values = set()
        for elem in data_tests:
            data_test = elem.get_attribute("data-test")
            if data_test and len(elem.text.strip()) > 0:
                data_test_values.add(data_test)

        for dt in sorted(data_test_values):
            logger.info(f"  - {dt}")

        # List main structure
        logger.info("\n--- PAGE STRUCTURE ---")
        try:
            main = driver.find_element(By.TAG_NAME, "main")
            logger.info(f"✅ Found MAIN tag")
        except:
            logger.info("❌ No MAIN tag found")

        try:
            sections = driver.find_elements(By.TAG_NAME, "section")
            logger.info(f"✅ Found {len(sections)} SECTION tags")
        except:
            logger.info("❌ No SECTION tags found")

        # Get list of all text content areas
        logger.info("\n--- TEXT CONTENT AREAS (first 500 chars each) ---")
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        logger.info(f"Found {len(paragraphs)} paragraph tags")
        for i, p in enumerate(paragraphs[:5]):
            text = p.text.strip()
            if text:
                logger.info(f"P[{i}]: {text[:150]}")

        return True

    except Exception as e:
        logger.error(f"Error inspecting page: {e}")
        return False


def main():
    driver = None
    try:
        driver = setup_driver()

        # Navigate to login page
        logger.info("Navigating to Upwork login page...")
        driver.get("https://www.upwork.com/ab/account-security/login")
        time.sleep(3)

        # Wait for manual login
        manual_login(driver)

        # Get a job from database
        fresh_job = session.query(JobListing).filter(JobListing.job_url != None).first()

        if not fresh_job:
            logger.error("No jobs found in database!")
            return

        logger.info(f"Inspecting job: {fresh_job.job_url}")

        output_file = "/Users/antonioirizarry/Desktop/Projects/lead_system/debug_job_page.html"
        inspect_job_page(driver, fresh_job.job_url, output_file)

        logger.info(f"\n✅ HTML saved to: {output_file}")
        logger.info("You can now open this file in a browser and inspect the structure!")

    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if driver:
            logger.info("Closing driver...")
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()
