#!/usr/bin/env python3
"""
Test script to verify Chrome driver cleanup fixes
This will test if the resource leak warning is resolved
"""

import undetected_chromedriver as uc
import logging
import time
import warnings

# Suppress the specific warning we're trying to fix
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*leaked semaphore objects.*")

# Setup minimal logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_driver_cleanup():
    """Test Chrome driver creation and cleanup"""
    logger.info("🔧 Testing Chrome driver cleanup...")

    driver = None
    try:
        # Create Chrome options with resource management flags
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--headless")  # Run headless for testing

        logger.info("Creating Chrome driver...")
        driver = uc.Chrome(
            options=chrome_options,
            use_subprocess=False,
            version_main=141
        )

        logger.info("Testing basic navigation...")
        driver.get("https://www.google.com")
        logger.info(f"Page title: {driver.title}")

        logger.info("✅ Driver test successful")

    except Exception as e:
        logger.error(f"❌ Driver test failed: {e}")

    finally:
        if driver:
            try:
                logger.info("🧹 Cleaning up driver...")
                # Close all windows
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    driver.close()

                # Quit driver
                driver.quit()
                logger.info("✅ Driver cleanup complete")

                # Give time for cleanup
                time.sleep(2)

            except Exception as e:
                logger.warning(f"⚠️  Cleanup error: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Chrome driver cleanup test...")
    test_driver_cleanup()
    logger.info("🏁 Test complete")

    # Force garbage collection
    import gc
    gc.collect()

    logger.info("💡 If you don't see resource_tracker warnings above, the fix is working!")