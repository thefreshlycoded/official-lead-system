import psycopg2
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Connect to PostgreSQL database
def connect_db():
    try:
        logging.info("Connecting to the PostgreSQL database...")
        DATABASE_URL = "postgresql://alwayscodedfresh:Yachtzeex5!@localhost:5432/upwork_scraper"
        connection = psycopg2.connect(DATABASE_URL)
        logging.info("Database connection successful.")
        return connection
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise e

# Query the job listings table for records with at least one website URL
def get_job_listings_with_urls():
    try:
        connection = connect_db()
        cursor = connection.cursor()    

        # Check if table has records
        cursor.execute("SELECT COUNT(*) FROM job_listings")
        total_records = cursor.fetchone()[0]
        logging.info(f"Total job listings in the database: {total_records}")

        # Query the job listings with job_link present
        query = """
            SELECT id, title, description, location, post_date, posted_time, job_url, job_link, relevance, website_type, classification_snippet
            FROM job_listings 
            WHERE job_link IS NOT NULL AND job_link != ''
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        logging.info(f"Job listings with website URLs found: {len(rows)}")

        if len(rows) == 0:
            logging.info("No job listings with website URLs found.")
        else:
            for row in rows:
                logging.info(f"ID: {row[0]}")
                logging.info(f"Title: {row[1]}")
                logging.info(f"Description: {row[2]}")
                logging.info(f"Location: {row[3]}")
                logging.info(f"Post Date: {row[4]}")
                logging.info(f"Posted Time: {row[5]}")
                logging.info(f"Job URL: {row[6]}")
                logging.info(f"Website URL: {row[7]}")
                logging.info(f"Relevance: {row[8]}")
                logging.info(f"Website Type: {row[9]}")
                logging.info(f"Classification Snippet: {row[10]}")
                logging.info("-" * 40)
                # Print the website URL for manual checking
                print(f"Website URL: {row[7]}")

        cursor.close()
        connection.close()
    except Exception as e:
        logging.error(f"Error processing job listings: {e}")

# Main function
if __name__ == "__main__":
    get_job_listings_with_urls()
