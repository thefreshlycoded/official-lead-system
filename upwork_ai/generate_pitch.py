import os
import json
import psycopg2
import openai

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

# Function to ensure necessary columns exist
def add_columns_if_not_exist(cursor):
    cursor.execute("""
        ALTER TABLE job_listings
        ADD COLUMN IF NOT EXISTS email_pitch TEXT,
        ADD COLUMN IF NOT EXISTS sms_pitch TEXT,
        ADD COLUMN IF NOT EXISTS emails TEXT,
        ADD COLUMN IF NOT EXISTS phones TEXT;
    """)

# Function to generate pitch using OpenAI
def generate_pitch(contact_info, job_title, job_description):
    prompt = f"""
    You are an expert marketing assistant. Generate an email and an SMS pitch for the following job listing:

    Job Title: {job_title}
    Job Description: {job_description}
    Contact Emails: {contact_info.get('emails', [])}
    Contact Phones: {contact_info.get('phones', [])}

    The email pitch should be professional, addressing the client's needs and explaining why our services would be a good fit. Keep the email well-formatted with line breaks.

    The SMS pitch should be concise and highlight the key value points to catch the client's attention.

    Return the result in JSON format with the following fields:
    {{
        "email_pitch": "The generated email pitch...",
        "sms_pitch": "The generated SMS pitch..."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        print("Error decoding JSON from OpenAI response.")
        return None
    except Exception as e:
        print(f"Error generating pitch from OpenAI: {e}")
        return None

# Main function to fetch job listings and generate email and SMS pitches
def generate_pitches_for_contacts():
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()

    # Ensure the necessary fields exist
    add_columns_if_not_exist(cursor)
    conn.commit()

    # Fetch job listings with emails or phones
    cursor.execute("""
        SELECT id, title, description, emails, phones
        FROM job_listings
        WHERE emails IS NOT NULL OR phones IS NOT NULL;
    """)
    rows = cursor.fetchall()

    # Loop through each job listing and generate a pitch
    for row in rows:
        job_id, job_title, job_description, emails, phones = row

        # Prepare contact information dictionary
        contact_info = {
            "emails": emails.split(',') if emails else [],
            "phones": phones.split(',') if phones else []
        }

        print(f"\nGenerating pitches for job ID {job_id}: {job_title}")

        # Generate pitch using OpenAI
        pitch = generate_pitch(contact_info, job_title, job_description)

        if pitch:
            # Format the email pitch for readability with line breaks
            email_pitch = pitch['email_pitch'].replace("\\n", "\n")

            # Log the generated pitches to the terminal
            print("Generated Email Pitch:\n", email_pitch)
            print("Generated SMS Pitch:\n", pitch['sms_pitch'])

            try:
                # Update job listing with formatted pitches
                cursor.execute("""
                    UPDATE job_listings
                    SET email_pitch = %s,
                        sms_pitch = %s
                    WHERE id = %s
                """, (email_pitch, pitch['sms_pitch'], job_id))
                conn.commit()
                print(f"Pitches saved for job ID {job_id}")
            except Exception as e:
                print(f"Error saving pitches for job ID {job_id}: {e}")
                conn.rollback()

    # Close database connection
    cursor.close()
    conn.close()

if __name__ == "__main__":
    generate_pitches_for_contacts()
