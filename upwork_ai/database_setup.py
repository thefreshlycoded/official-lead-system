from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alwayscodedfresh:Yachtzeex5!@localhost:5432/upwork_scraper")

# Define the SQLAlchemy Base
Base = declarative_base()

# Define the JobListing model
class JobListing(Base):
    __tablename__ = 'job_listings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_url = Column(String, unique=True, nullable=False)  # Unique job URLs
    title = Column(String)
    description = Column(String)
    location = Column(String)
    post_date = Column(String)
    posted_time = Column(String)
    job_link = Column(String)
    source = Column(String, default='upwork')  # Specify source (e.g., 'upwork', 'craigslist')
    type = Column(String, default='job')       # Specify type (e.g., 'job', 'gig', etc.)
    relevance = Column(Boolean, default=None) # AI classification: is the post relevant?
    website_present = Column(Boolean, default=None)
    website_url = Column(String, default=None)
    website_type = Column(String, default=None)
    classification_snippet = Column(String, default=None)
    fresh = Column(Boolean, default=True)     # Is this post fresh?
    date_added = Column(DateTime, default=datetime.now)
    date_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# Setup the database engine
engine = create_engine(DATABASE_URL)

def drop_and_create_tables():
    """
    Drops all tables and recreates them.
    This is only safe to run in development or testing environments.
    """
    confirm_env = os.getenv("ENVIRONMENT", "development")  # Default to 'development'

    if confirm_env.lower() == "production":
        print("Abort: This script should not run in a production environment.")
        return

    print(f"Environment: {confirm_env}. Dropping and recreating tables...")
    Base.metadata.drop_all(engine)  # Drop all existing tables
    print("All tables dropped.")
    Base.metadata.create_all(engine)  # Recreate tables
    print("Database tables recreated successfully!")

if __name__ == "__main__":
    drop_and_create_tables()
