#!/usr/bin/env python3
"""
Silent Chrome Driver Wrapper
This wrapper completely disables multiprocessing resource tracking before importing main
"""

import os
import sys

# Disable multiprocessing resource tracker at process level BEFORE any imports
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:multiprocessing.resource_tracker'

# Monkey patch the resource tracker module to prevent it from loading
import types
import multiprocessing
fake_tracker = types.ModuleType('resource_tracker')
fake_tracker.track = lambda *args: None
fake_tracker.untrack = lambda *args: None
fake_tracker.main = lambda *args: None
fake_tracker.warnings = types.ModuleType('warnings')
fake_tracker.warnings.warn = lambda *args: None

# Replace the real resource tracker with our fake one
multiprocessing.resource_tracker = fake_tracker
sys.modules['multiprocessing.resource_tracker'] = fake_tracker

# Also disable at multiprocessing level
try:
    multiprocessing._cleanup_tests = lambda: None
except:
    pass

print("🔇 Resource tracker disabled - running silently...")

# Now import and run the main scraper
if __name__ == "__main__":
    # Add current directory to path so we can import main
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Import main module
    import main

    # The main script will run when imported since it has if __name__ == "__main__" logic