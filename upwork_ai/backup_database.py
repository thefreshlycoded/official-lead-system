import subprocess
import datetime

def backup_database():
    # Define the backup filename with a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"upwork_scraper_backup_{timestamp}.sql"

    # Command to back up the database
    command = [
        "pg_dump",
        "--dbname=postgresql://alwayscodedfresh:Yachtzeex5!@localhost:5432/upwork_scraper",
        "-F", "c",  # Format as custom
        "-f", backup_file
    ]

    try:
        # Run the backup command
        subprocess.run(command, check=True)
        print(f"Database backup created successfully: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating database backup: {e}")

# Call the backup function before making any changes
backup_database()
