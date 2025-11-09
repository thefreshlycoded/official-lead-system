import os
import re
import shutil
import subprocess
import spacy
from bs4 import BeautifulSoup

# Load spaCy model for AI-based extraction
nlp = spacy.load("en_core_web_sm")

# Regex patterns for email, phone, and social media
email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
social_patterns = {
    'facebook': r'facebook\.com/[a-zA-Z0-9\._-]+',
    'twitter': r'twitter\.com/[a-zA-Z0-9\._-]+',
    'instagram': r'instagram\.com/[a-zA-Z0-9\._-]+',
    'linkedin': r'linkedin\.com/in/[a-zA-Z0-9\._-]+',
}

# Function to extract contact info using AI (spaCy NER)
def ai_extract_contact_info(text):
    doc = nlp(text)
    emails = []
    phones = []

    for ent in doc.ents:
        if ent.label_ == "EMAIL":
            emails.append(ent.text)
        elif ent.label_ == "PHONE":
            phones.append(ent.text)
    return {'emails': emails, 'phones': phones}

# Function to scrape the local HTML file for emails, phones, and social media links
def scrape_local_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        page_text = f.read()
    
    soup = BeautifulSoup(page_text, 'html.parser')

    # Scrape for structured data (emails, phones)
    emails = re.findall(email_pattern, soup.text)
    phones = re.findall(phone_pattern, soup.text)

    # Scrape for social media links
    social_media = {}
    for platform, pattern in social_patterns.items():
        links = re.findall(pattern, soup.text)
        social_media[platform] = links if links else None

    # Use AI (spaCy) to analyze unstructured data if necessary
    ai_results = ai_extract_contact_info(soup.text)

    # Combine traditional and AI results, removing duplicates
    combined_emails = list(set(emails + ai_results['emails']))
    combined_phones = list(set(phones + ai_results['phones']))

    return {
        'emails': combined_emails,
        'phones': combined_phones,
        'social_media': social_media
    }

# Function to loop through all files in a directory and scrape each file
def scrape_entire_site(directory):
    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                result = scrape_local_file(filepath)
                if result:
                    results.append(result)
    return results

# Function to download the website using wget
def download_website(url, download_dir):
    # Command to download the website
    command = [
        'wget', '--mirror', '--convert-links', '--adjust-extension', '--page-requisites',
        '--no-parent', '--directory-prefix', download_dir, url
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Website downloaded to {download_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading website: {e}")
        return False
    return True

# Function to delete the downloaded website after processing
def delete_downloaded_site(download_dir):
    try:
        shutil.rmtree(download_dir)
        print(f"Deleted downloaded files in {download_dir}")
    except OSError as e:
        print(f"Error deleting directory {download_dir}: {e}")

# Main function to download, scrape, and delete the website
def main(url):
    download_dir = './downloaded_site'  # Directory to store downloaded site
    
    # Step 1: Download the website
    if not download_website(url, download_dir):
        return

    # Step 2: Scrape the downloaded site
    print("Scraping the downloaded website...")
    scraped_data = scrape_entire_site(download_dir)

    # Output the scraped data
    print(f"Scraped Data from {url}:")
    for data in scraped_data:
        print(data)

    # Step 3: Delete the downloaded site
    delete_downloaded_site(download_dir)

# Example usage
if __name__ == "__main__":
    url = 'http://alwayscodedfresh.com'  # Replace with the target website URL
    main(url)
