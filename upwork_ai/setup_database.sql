-- Create database
CREATE DATABASE upwork_scraper_db;

-- Connect to the newly created database
\c upwork_scraper_db;

-- Create job_listings table
CREATE TABLE IF NOT EXISTS job_listings (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL
);
