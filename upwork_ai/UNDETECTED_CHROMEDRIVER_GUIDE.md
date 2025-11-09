# Undetected ChromeDriver Setup Guide

## Overview
Your project now uses **undetected-chromedriver 3.5.5+** with comprehensive anti-detection measures to scrape Upwork while avoiding bot detection.

## What is Undetected ChromeDriver?

`undetected-chromedriver` (UC) is a Python library that:
- ✅ Automatically patches ChromeDriver to avoid detection
- ✅ Bypasses Cloudflare, bot detection, and anti-scraping measures
- ✅ Works seamlessly with Selenium 4.x
- ✅ Handles user-agent spoofing and fingerprint masking
- ✅ Manages browser profiles and authentication persistence

## Installation

Dependencies are already configured in `requirements.txt`:
```
undetected-chromedriver>=3.5.5
selenium>=4.0.0
selenium-stealth
```

Install/upgrade:
```bash
cd upwork_ai
pip install -r requirements.txt --upgrade
```

## Project Files Using UC

### 1. **main.py** - Primary Scraper
- Uses `uc.Chrome()` with subprocess isolation
- Anti-detection JavaScript injection via CDP
- Modern user-agent (Chrome 120+)
- Human-like delays and browsing patterns

**Key features:**
```python
import undetected_chromedriver as uc

chrome_options = uc.ChromeOptions()
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = uc.Chrome(options=chrome_options, use_subprocess=True)
```

### 2. **run_upwork_latest.py** - Advanced Scraper with Rails Integration
- Dual-mode: Standard Selenium + UC fallback
- Rails UI integration for manual login workflows
- Chrome profile persistence (stable + temporary)
- Advanced stealth measures via CDP and selenium-stealth

**Key features:**
```python
if driver_type == "uc" and uc is not None:
    driver = uc.Chrome(
        options=uc_opts,
        user_data_dir=use_profile,
        browser_executable_path=chrome_binary,
        headless=False
    )
```

### 3. **run_standalone.py** - Standalone Version
- Optional `--uc` flag for undetected-chromedriver
- Fallback to standard Selenium if UC fails
- Profile management and login persistence

## Anti-Detection Techniques

### 1. **Navigator Masking** (via CDP)
```javascript
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
```

### 2. **Chrome Extensions Spoofing**
```javascript
window.chrome = { runtime: {} };
Object.defineProperty(Notification, 'permission', { get: () => 'default' });
```

### 3. **User-Agent & Headers**
- Modern Chrome 120 user-agent with correct platform
- Realistic language/timezone preferences
- WebGL renderer/vendor masking

### 4. **Browser Arguments**
```
--disable-blink-features=AutomationControlled
--disable-infobars
--no-first-run
--detach (keeps browser open)
```

### 5. **Selenium-Stealth Integration**
```python
from selenium_stealth import stealth
stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", ...)
```

## Usage Examples

### Basic Usage (main.py)
```bash
cd upwork_ai
python main.py
```

### With Rails Integration (run_upwork_latest.py)
```bash
# Set environment variables
export RAILS_BASE_URL="http://localhost:3000"
export SCRAPER_ID="123"
export UPLOAD_DEST="api"

python run_upwork_latest.py
```

### Standalone with Options (run_standalone.py)
```bash
# Use undetected-chromedriver
python run_standalone.py --uc

# Use standard Selenium
python run_standalone.py
```

## Chrome Profile Management

### Profile Locations
- **Stable Profile**: `upwork_ai/chrome_profile/` - Persistent across runs
- **Temp Profile**: `upwork_ai/chrome_profile_tmp_<timestamp>_<pid>/` - Per-run isolation

### Lock Handling
The scraper automatically:
1. Detects if the stable profile is in use
2. Waits up to 60 seconds for the lock to clear
3. Falls back to a temporary profile if locked

```python
# From run_upwork_latest.py
lock_files = [
    os.path.join(stable_profile, "SingletonLock"),
    os.path.join(stable_profile, "SingletonCookie"),
]
```

## Troubleshooting

### Issue: "Chrome binary not found"
**Solution**: Ensure Chrome is installed:
```bash
# macOS
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome

# Or set manually
export CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

### Issue: "Port already in use"
**Solution**: UC randomizes port allocation, but if conflicts occur:
```bash
# Kill existing Chrome processes
killall -9 chromedriver
killall -9 "Google Chrome"
```

### Issue: "Profile is locked"
**Solution**: Wait for the lock to clear or manually remove:
```bash
rm -rf upwork_ai/chrome_profile/SingletonLock
```

### Issue: "Detected as bot"
**Solution**:
1. Update user-agent to current Chrome version
2. Increase human delays: `time.sleep(random.uniform(3, 8))`
3. Use temporary profiles instead of persistent ones
4. Rotate through multiple IP addresses (if needed)

## Best Practices

### 1. **Always Use Human Delays**
```python
import time
import random

time.sleep(random.uniform(2, 5))  # Random delay between actions
```

### 2. **Respect Rate Limits**
- 2-5 seconds between page loads
- 5-10 seconds between searches
- 60+ seconds between scraping sessions

### 3. **Handle Headless Mode Carefully**
- Avoid `--headless` flag (detectable)
- Use `headless=False` in UC
- The browser window can be minimized instead

### 4. **Update User-Agent Regularly**
```python
# Check latest Chrome version at https://chromedriver.chromium.org/
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
```

### 5. **Monitor Logs**
```bash
# View scraper logs
tail -f upwork_ai/scraper.log

# Search for errors
grep -i error upwork_ai/scraper.log
```

## Performance Tips

### 1. **Use Subprocess Mode**
```python
driver = uc.Chrome(options=chrome_options, use_subprocess=True)
# Prevents memory leaks and process hangs
```

### 2. **Set Window Size Early**
```python
driver.set_window_size(1920, 1080)
# Improves page rendering and JavaScript execution
```

### 3. **Use Explicit Waits**
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.ID, "job-tile")))
```

### 4. **Batch Profile Cleanup**
```bash
# Remove old temp profiles
find upwork_ai/chrome_profile_tmp_* -mtime +7 -delete
```

## Security Considerations

### 1. **Never Commit Credentials**
- `chrome_profile/` may contain saved passwords
- Add to `.gitignore`:
  ```
  upwork_ai/chrome_profile/
  upwork_ai/chrome_profile_tmp_*/
  ```

### 2. **Use Environment Variables**
```bash
export DATABASE_URL="postgresql+pg8000://user:pass@localhost/db"
export RAILS_API_KEY="your-secret-key"
```

### 3. **Rotate User-Agents**
For large-scale scraping, rotate between realistic user-agents from different OS/browser versions.

## Version History

### 3.5.5 (Current)
- ✅ Full Selenium 4.x compatibility
- ✅ Improved subprocess isolation
- ✅ Better Cloudflare handling
- ✅ Modern fingerprint masking

### Migration from Older Versions
If upgrading from UC 3.x:
1. Update `requirements.txt`: `undetected-chromedriver>=3.5.5`
2. Replace `Options()` imports with `uc.ChromeOptions()`
3. Test profile compatibility

## Additional Resources

- **Official Docs**: https://github.com/ultrafunkamsterdam/undetected-chromedriver
- **Selenium Docs**: https://selenium.dev/documentation/
- **Selenium-Stealth**: https://github.com/diprajpatra/selenium-stealth
- **CDP Commands**: https://chromedevtools.github.io/devtools-protocol/

## Support

For issues:
1. Check logs: `upwork_ai/scraper.log`
2. Update dependencies: `pip install -r requirements.txt --upgrade`
3. Clear profiles: `rm -rf upwork_ai/chrome_profile_tmp_*`
4. Restart Docker if using containers: `docker-compose restart`

---

**Last Updated**: October 30, 2025
**Status**: ✅ Production Ready
