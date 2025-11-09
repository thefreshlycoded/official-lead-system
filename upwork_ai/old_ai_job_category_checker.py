import openai
import psycopg2
import json
import os

# Hardcoding the API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Database connection setup
conn = psycopg2.connect(
    dbname="upwork_scraper",
    user="alwayscodedfresh",
    password="Yachtzeex5!",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Function to add columns to the table if they don't exist
def add_columns_if_not_exist():
    try:
        cur.execute("ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS relevance BOOLEAN")
        cur.execute("ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS website_present BOOLEAN")
        cur.execute("ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS website_url TEXT")
        cur.execute("ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS website_type VARCHAR(255)")
        cur.execute("ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS classification_snippet TEXT")
        conn.commit()
        print("Checked and added missing columns to the job_listings table if necessary.")
    except psycopg2.Error as e:
        print(f"Error adding columns: {e}")
        conn.rollback()

# Call the function to add columns if they don't exist
add_columns_if_not_exist()

# Query job listings
cur.execute("SELECT id, title, description FROM job_listings LIMIT 300")
rows = cur.fetchall()

# Create the OpenAI client object for GPT-4
client = openai

# Iterate over each listing and call OpenAI API
for row in rows:
    job_id = row[0]
    job_title = row[1]
    job_description = row[2]

    # Creating the prompt to classify job listings
    prompt = (
        f"Job Title: {job_title}\n"
        f"Job Description: {job_description}\n"
        "Is this job listing related to digital marketing, web design, branding, UI/UX, software, mobile development, website monetization, or blockchain? "
        "Additionally, check if there is a website mentioned in the job listing. If there is, classify if the website is the poster's own website or a third-party service. "
        "Return your result in JSON format with the following fields:\n"
        "- job_listing_id\n"
        "- relevance (yes/no)\n"
        "- website_present (true/false)\n"
        "- website_url (if present)\n"
        "- website_type ('poster_website' or 'third_party')\n"
        "- snippet (text that led to classification)"
    )

    # Make the request to OpenAI using the original working method
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )

        # Correctly access the content from the response
        relevance_json = response.choices[0].message.content.strip()

        # Parse the response and update the database
        try:
            result = json.loads(relevance_json)  # Parse the response as JSON
            relevance = result.get("relevance", "no") == "yes"
            website_present = result.get("website_present", "false") == "true"
            website_url = result.get("website_url", None)
            website_type = result.get("website_type", None)
            classification_snippet = result.get("snippet", None)

            # Update the job listing with the classification results
            cur.execute("""
                UPDATE job_listings
                SET relevance = %s,
                    website_present = %s,
                    website_url = %s,
                    website_type = %s,
                    classification_snippet = %s
                WHERE id = %s
            """, (relevance, website_present, website_url, website_type, classification_snippet, job_id))
            conn.commit()
            print(f"Updated job ID {job_id} with classification results.")
        except json.JSONDecodeError:
            print(f"Error parsing JSON for job ID {job_id}")
    except Exception as e:
        print(f"Error processing job ID {job_id}: {e}")
        conn.rollback()

# Close database connection
cur.close()
conn.close()

# Confirm that the script has finished execution
print("Script execution completed.")