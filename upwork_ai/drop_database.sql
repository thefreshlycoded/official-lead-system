-- Disconnect active connections to the database (forcibly disconnect users)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'upwork_scraper_db'
  AND pid <> pg_backend_pid();

-- Drop the database
DROP DATABASE IF EXISTS upwork_scraper_db;
