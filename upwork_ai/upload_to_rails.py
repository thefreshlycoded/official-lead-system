import json
import psycopg2
import requests
from datetime import datetime

# Database connection parameters
DATABASE_CONFIG = {
    'dbname': 'upwork_scraper',
    'user': 'alwayscodedfresh',
    'password': 'Yachtzeex5!',
    'host': 'localhost',
    'port': '5432'
}

# Rails API endpoint URL
RAILS_API_URL = "http://localhost:3000/api/job_listings"

# Helper function to format datetime objects as strings
def format_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value

# Function to fetch job listings from the database and upload to Rails
def fetch_job_listings():
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        # Fetch job listings with only essential fields
        cursor.execute("""
            SELECT id, job_url, title, description, location, post_date, posted_time,
                   job_link, relevance, website_present, website_url, website_type, date_added
            FROM job_listings
            WHERE relevance = TRUE;
        """)
        rows = cursor.fetchall()

        # Loop through each listing and submit to the Rails API
        for row in rows:
            job_listing = {
                "job_url": row[1],
                "title": row[2],
                "description": row[3],
                "location": row[4],
                "post_date": format_datetime(row[5]),
                "posted_time": format_datetime(row[6]),
                "job_link": row[7],
                "relevance": row[8],
                "website_present": row[9],
                "website_url": row[10],
                "website_type": row[11],
                "date_added": format_datetime(row[12])  # Include date_added
            }

            # Send a POST request to the Rails API
            try:
                response = requests.post(RAILS_API_URL, json={"job_listing": job_listing})
                if response.status_code == 201:
                    print(f"Job listing {row[0]} uploaded successfully.")
                else:
                    print(f"Failed to upload job listing {row[0]}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending data for job listing {row[0]}: {e}")

        # Close database connection
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database connection or query error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    fetch_job_listings()
