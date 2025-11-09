#!/bin/bash

echo "Dropping existing database..."
psql -U alwayscodedfresh -h localhost -p 5432 -c "DROP DATABASE IF EXISTS upwork_scraper_db;"

echo "Creating new database..."
psql -U alwayscodedfresh -h localhost -p 5432 -c "CREATE DATABASE upwork_scraper_db;"

echo "Running migrations..."
psql -U alwayscodedfresh -h localhost -p 5432 -d upwork_scraper_db -f migrations.sql

echo "Database has been reset."
