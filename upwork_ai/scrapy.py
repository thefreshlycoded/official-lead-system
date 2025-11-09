import os
import json
import psycopg2
import openai
import requests
from bs4 import BeautifulSoup
import re
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenAI API key setup
openai.api_key = os.getenv('OPENAI_API_KEY')
client = openai

# Database connection parameters
DATABASE_CONFIG = {
    'dbname': 'upwork_scraper',
    'user': 'alwayscodedfresh',
    'password': 'Yachtzeex5!',
    'host': 'localhost',
    'port': '5432'
}

# Timeout duration for requests (in seconds)
REQUEST_TIMEOUT = 10

# Function to add necessary columns to the job_listings table if they do not exist
def add_contact_fields_if_not_exist(cursor):
    cursor.execute("""
        ALTER TABLE job_listings
        ADD COLUMN IF NOT EXISTS emails TEXT,
        ADD COLUMN IF NOT EXISTS phones TEXT,
        ADD COLUMN IF NOT EXISTS facebook VARCHAR(255),
        ADD COLUMN IF NOT EXISTS twitter VARCHAR(255),
        ADD COLUMN IF NOT EXISTS linkedin VARCHAR(255),
        ADD COLUMN IF NOT EXISTS instagram VARCHAR(255),
        ADD COLUMN IF NOT EXISTS city VARCHAR(100),
        ADD COLUMN IF NOT EXISTS state VARCHAR(100),
        ADD COLUMN IF NOT EXISTS country VARCHAR(100),
        ADD COLUMN IF NOT EXISTS industry VARCHAR(255),
        ADD COLUMN IF NOT EXISTS owner_name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS manual_review BOOLEAN DEFAULT FALSE;
    """)

# Function to ensure URLs have a scheme
def ensure_url_scheme(url):
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

# Function to download a website's content with a timeout
def download_website_content(url):
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Ensure the request was successful

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        with open(temp_file.name, 'w', encoding='utf-8') as file:
            file.write(response.text)

        logging.info(f"Website content downloaded and saved to {temp_file.name}")
        return temp_file.name
    except requests.exceptions.Timeout:
        logging.warning(f"Timeout reached for {url}. Marking for manual review.")
        return 'TIMEOUT'
    except Exception as e:
        logging.error(f"Error downloading website content from {url}: {e}")
        return None

# Function to extract emails and phone numbers from the downloaded file
def extract_emails_and_phones_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', soup.get_text())
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', soup.get_text())

        return list(set(emails)), list(set(phones))
    except Exception as e:
        logging.error(f"Error parsing content from {file_path}: {e}")
        return [], []

# Helper function to extract social media links from the content
def extract_social_links_from_file(file_path):
    social_links = {}
    social_networks = {
        "facebook.com": "facebook",
        "twitter.com": "twitter",
        "linkedin.com": "linkedin",
        "instagram.com": "instagram"
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        for link in soup.find_all('a', href=True):
            for domain, network in social_networks.items():
                if domain in link['href']:
                    social_links[network] = link['href']

        return social_links
    except Exception as e:
        logging.error(f"Error extracting social media links from {file_path}: {e}")
        return {}

# Function to prompt OpenAI for intelligent contact information extraction
def get_openai_guidance_for_contact_info(url):
    prompt = f"""
    Visit the website {url} and provide the following contact information based on actual site content. Do not use placeholders or assumed data. If data is not available, leave the field blank and indicate manual review if necessary.

    Required details:
    - Emails
    - Phone numbers
    - Social media profile URLs (Facebook, Twitter, LinkedIn, Instagram)
    - City, State, Country
    - Industry
    - Owner or primary contact name (leave blank if not explicitly found)

    Format the response as JSON:
    {{
      "website_url": "{url}",
      "emails": ["list of email addresses"],
      "phones": ["list of phone numbers"],
      "social_media": {{
        "facebook": "Facebook URL if available",
        "twitter": "Twitter URL if available",
        "linkedin": "LinkedIn URL if available",
        "instagram": "Instagram URL if available"
      }},
      "location": {{
        "city": "City if available",
        "state": "State if available",
        "country": "Country if available"
      }},
      "industry": "Industry if available",
      "owner_name": "Owner name if explicitly stated",
      "manual_review": true/false
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700
        )
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from OpenAI response.")
        return {"manual_review": True}
    except Exception as e:
        logging.error(f"Error fetching guidance from OpenAI: {e}")
        return {"manual_review": True}

# Function to merge tool-based and GPT-based results with strict validation
def merge_contact_info(tool_info, gpt_info):
    combined_info = {
        "emails": [email for email in tool_info.get("emails", []) + gpt_info.get("emails", []) if email],
        "phones": [phone for phone in tool_info.get("phones", []) + gpt_info.get("phones", []) if phone],
        "social_media": {**tool_info.get("social_media", {}), **gpt_info.get("social_media", {})},
        "location": gpt_info.get("location", {}),
        "industry": gpt_info.get("industry", ""),
        "owner_name": gpt_info.get("owner_name", ""),
        "manual_review": gpt_info.get("manual_review", False)
    }
    return combined_info

# Function to save contact details to the job_listings table
def save_contact_details(cursor, job_id, contact_info, manual_review=False):
    emails = ', '.join(contact_info.get('emails', []))
    phones = ', '.join(contact_info.get('phones', []))
    facebook = contact_info.get('social_media', {}).get('facebook', '')
    twitter = contact_info.get('social_media', {}).get('twitter', '')
    linkedin = contact_info.get('social_media', {}).get('linkedin', '')
    instagram = contact_info.get('social_media', {}).get('instagram', '')
    city = contact_info.get('location', {}).get('city', '')
    state = contact_info.get('location', {}).get('state', '')
    country = contact_info.get('location', {}).get('country', '')
    industry = contact_info.get('industry', '')
    owner_name = contact_info.get('owner_name', '')

    cursor.execute("""
        UPDATE job_listings
        SET emails = %s, phones = %s, facebook = %s, twitter = %s, linkedin = %s, instagram = %s,
            city = %s, state = %s, country = %s, industry = %s, owner_name = %s, manual_review = %s
        WHERE id = %s;
    """, (emails, phones, facebook, twitter, linkedin, instagram, city,
          state, country, industry, owner_name, manual_review, job_id))

    logging.info(f"Contact details saved for job ID {job_id}:")
    logging.info(f"  Emails: {emails}")
    logging.info(f"  Phones: {phones}")
    logging.info(f"  Social Media - Facebook: {facebook}, Twitter: {twitter}, LinkedIn: {linkedin}, Instagram: {instagram}")
    logging.info(f"  Location - City: {city}, State: {state}, Country: {country}")
    logging.info(f"  Industry: {industry}")
    logging.info(f"  Owner Name: {owner_name}")
    logging.info(f"  Manual Review: {manual_review}")

# Main function to fetch URLs from the database and process them
def fetch_urls_and_scrape():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()

    add_contact_fields_if_not_exist(cursor)
    conn.commit()

    cursor.execute("""
        SELECT id, website_url
        FROM job_listings
        WHERE website_url IS NOT NULL
            AND website_url <> ''
            AND relevance = TRUE;
    """)
    rows = cursor.fetchall()

    for row in rows:
        job_id, website_url = row
        website_url = ensure_url_scheme(website_url)
        logging.info(f"Processing job ID {job_id} for URL: {website_url}")

        file_path = download_website_content(website_url)
        if file_path == 'TIMEOUT':
            save_contact_details(cursor, job_id, {}, manual_review=True)
            conn.commit()
            logging.warning(f"Job ID {job_id} marked for manual review due to timeout.")
            continue
        elif not file_path:
            save_contact_details(cursor, job_id, {}, manual_review=True)
            conn.commit()
            logging.warning(f"Job ID {job_id} marked for manual review due to download failure.")
            continue

        emails, phones = extract_emails_and_phones_from_file(file_path)
        social_links = extract_social_links_from_file(file_path)

        tool_contact_info = {
            "emails": emails,
            "phones": phones,
            "social_media": social_links
        }

        gpt_suggestions = get_openai_guidance_for_contact_info(website_url)
        combined_contact_info = merge_contact_info(tool_contact_info, gpt_suggestions)

        if combined_contact_info.get("emails") or combined_contact_info.get("phones"):
            save_contact_details(cursor, job_id, combined_contact_info)
            conn.commit()
            logging.info(f"Contact info saved for job ID {job_id}")
        else:
            save_contact_details(cursor, job_id, {"manual_review": True})
            conn.commit()
            logging.warning(f"No contact info found for job ID {job_id}. Marked for manual review.")

        try:
            os.remove(file_path)
            logging.info(f"Temporary file {file_path} deleted.")
        except Exception as e:
            logging.error(f"Error deleting temporary file {file_path}: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    fetch_urls_and_scrape()
