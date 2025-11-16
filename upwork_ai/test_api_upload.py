#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def test_upload_job_to_api():
    """Test the Rails API upload functionality"""

    api_url = "http://localhost:4200/api/upload_job_listings/upload"

    # Test job data
    test_job = {
        "job": {
            "job_url": "https://www.upwork.com/jobs/~test123",
            "title": "Test API Upload Job",
            "description": "This is a test job to verify the API upload functionality works correctly.",
            "location": "Remote",
            "post_date": datetime.now().isoformat(),
            "posted_time": "5 minutes ago",
            "fresh": True,
            "source": "upwork",
            "listing_type": "job"
        }
    }

    headers = {
        'Content-Type': 'application/json'
    }

    print(f"Testing API upload to: {api_url}")
    print(f"Test payload: {json.dumps(test_job, indent=2)}")

    try:
        response = requests.post(api_url, json=test_job, headers=headers, timeout=30)

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")

        if response.status_code == 200 or response.status_code == 201:
            print("✅ API upload test SUCCESSFUL!")
            return True
        else:
            print("❌ API upload test FAILED!")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the Rails server running on localhost:4200?")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    test_upload_job_to_api()