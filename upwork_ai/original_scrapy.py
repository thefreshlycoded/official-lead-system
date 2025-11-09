import os
import re
import shutil
import subprocess
import spacy
import json
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

# Function to scrape the local HTML and JS files for emails, phones, and social media links
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
    final_result = {
        'emails': set(),
        'phones': set(),
        'social_media': {
            'facebook': set(),
            'twitter': set(),
            'instagram': set(),
            'linkedin': set()
        }
    }

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.html', '.js')):  # Scrape only HTML and JS files
                filepath = os.path.join(root, file)
                result = scrape_local_file(filepath)
                if result:
                    final_result['emails'].update(result['emails'])
                    final_result['phones'].update(result['phones'])
                    for platform, links in result['social_media'].items():
                        if links:
                            final_result['social_media'][platform].update(links)

    # Convert sets back to lists
    final_result['emails'] = list(final_result['emails'])
    final_result['phones'] = list(final_result['phones'])
    for platform in final_result['social_media']:
        final_result['social_media'][platform] = list(final_result['social_media'][platform])

    return final_result

# Function to download the website using wget
def download_website(url, download_dir):
    # Command to download only HTML and JavaScript files
    command = [
        'wget', '--mirror', '--convert-links', '--adjust-extension', '--no-parent',
        '--accept', 'html,js', '--reject', 'jpg,jpeg,png,gif,css', '--timeout=10',
        '--directory-prefix', download_dir, url
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode == 8:  # Exit status 8 indicates some files weren't fetched
            print(f"Warning: Some files couldn't be downloaded from {url}, continuing anyway...")
        elif result.returncode != 0:
            print(f"Error downloading website: {result.stderr}")
            return False
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

# Function to load existing JSON file, or create a new structure if it doesn't exist
def load_existing_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Function to save scraped data to a JSON file, overwriting if it already exists for the URL
def save_results_to_json(data, url, filename='scraped_data.json'):
    # Load existing data
    existing_data = load_existing_json(filename)

    # Add or update the data for the specific URL
    existing_data[url] = data

    # Save the updated data to the JSON file
    try:
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=4)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error saving to {filename}: {e}")

# Main function to download, scrape, save, and delete the website
def main(url, output_json='scraped_data.json'):
    download_dir = './downloaded_site'  # Directory to store downloaded site

    # Handle HTTPS explicitly in case of redirects
    if not url.startswith('https://'):
        url = url.replace('http://', 'https://')

    # Step 1: Download the website
    if not download_website(url, download_dir):
        return

    # Step 2: Scrape the downloaded site
    print("Scraping the downloaded website...")
    scraped_data = scrape_entire_site(download_dir)

    # Step 3: Save the scraped data to JSON, using the website URL as the identifier
    print(f"Saving scraped data from {url} to JSON file...")
    save_results_to_json(scraped_data, url, output_json)

    # Step 4: Delete the downloaded site
    delete_downloaded_site(download_dir)

# Example usage
if __name__ == "__main__":
    url = 'https://alwayscodedfresh.com'  # Replace with the target website URL
    output_json = 'scraped_data.json'  # Output JSON file
    main(url, output_json)
