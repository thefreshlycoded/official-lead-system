- make API


- AI Services go out to






# Standalone Upwork Scraper

This is a simplified, standalone Python scraper that:
- Opens Chrome to Upwork login page
- Waits for you to log in manually
- Scrapes recent "www" jobs
- Saves directly to PostgreSQL database
- No Rails integration required





## Quick Start

```bash
# From the upwork_ai directory
./run_scraper.sh --pages 3 --hours 24
```

## Setup Requirements

1. **Chrome**: Install Google Chrome in `/Applications/`
2. **PostgreSQL**: Running database (default: `lead_system_development`)
3. **Python 3**: With pip

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql+pg8000://postgres@localhost:5432/lead_system_development`)
- `CHROME_BIN`: Path to Chrome binary (auto-detected)

## Usage Examples

```bash
# Basic run - scrape 3 pages of jobs from last 24 hours
./run_scraper.sh

# Scrape more pages and older jobs
./run_scraper.sh --pages 5 --hours 48

# Use undetected-chromedriver for extra stealth
./run_scraper.sh --uc --pages 3 --hours 24

# Custom database
DATABASE_URL="postgresql+pg8000://user:pass@host:5432/mydb" ./run_scraper.sh
```

## How It Works

1. **Setup**: Creates virtual environment, installs packages
2. **Chrome**: Opens to Upwork login page
3. **Manual Login**: You log in and solve any captcha
4. **Scraping**: Automatically searches for recent "www" jobs
5. **Saving**: Saves job details to PostgreSQL with upsert (no duplicates)

## Fields Saved

- `job_url` (unique)
- `title`
- `description`
- `location`
- `post_date`
- `posted_time`
- `job_link` (external website if present)
- `source` = "upwork"
- `listing_type` = "job"

## Troubleshooting

- **No jobs found**: Solve any Cloudflare challenge in the browser
- **Chrome not found**: Install Google Chrome in `/Applications/`
- **Database errors**: Check your PostgreSQL connection and credentials
- **Detection issues**: Try the `--uc` flag for undetected-chromedriver

---

## Legacy AI Scraper — Overview and Runbook

This app automates lead generation from Upwork job listings, enriches them with AI, extracts contact info from employer websites, generates tailored outreach (email + SMS), and can sync results into a Rails backend.

High level pipeline:
- main.py: Manual Upwork login → scrape recent job listing URLs and details → store in Postgres.
- ai_job_category_checker.py: Use OpenAI to classify relevance, detect website presence, and capture website_url and metadata.
- scrapy.py: Download the poster’s website, extract emails/phones/social links and location info; use GPT to refine; save back to DB.
- generate_pitch.py: Use OpenAI to create an email and SMS pitch for listings with contact details; save to DB.
- upload_to_rails.py: POST relevant listings to a Rails API at http://localhost:3000/api/job_listings.


## Repository structure (key files)

- main.py — Upwork scraping, pagination, job details extraction, saves to Postgres.
- ai_job_category_checker.py — AI classification (relevance + website fields) via OpenAI Chat Completions.
- scrapy.py — Website downloader + BeautifulSoup regex extraction + OpenAI assist; writes contact fields.
- generate_pitch.py — Generates email_pitch and sms_pitch via OpenAI.
- upload_to_rails.py — Sends relevant jobs to a Rails API endpoint.
- database_setup.py — SQLAlchemy model and helper for (re)creating tables.
- requirements.txt — Python deps (selenium, undetected-chromedriver, SQLAlchemy, psycopg2-binary, bs4, spacy, wget, openai).
- setup_database.sql, migrations.sql — Legacy examples (use DB name upwork_scraper; see notes below).
- run_all.sh — Legacy runner (paths don’t match this repo; prefer running scripts manually as below).
- scraped_data/, downloaded_site*/ — Artifacts from contact scraping.


## Data model (important columns in job_listings)

Created by SQLAlchemy in main.py and later extended dynamically by scripts via ALTER TABLE:

- Core: id, job_url (unique), title, description, location, post_date, posted_time, job_link, fresh, date_added, date_updated
- AI classification: relevance (bool), website_present (bool), website_url (text), website_type (text), classification_snippet (text)
- Contact enrichment: emails, phones, facebook, twitter, linkedin, instagram, city, state, country, industry, owner_name, manual_review
- Outreach: email_pitch, sms_pitch


## Prerequisites

- macOS, zsh
- PostgreSQL running locally
- Python 3.9+ recommended
- Chrome installed (undetected-chromedriver downloads its own driver)


## Quick start

1) Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv upwork_scraper_env
source upwork_scraper_env/bin/activate
pip install -r requirements.txt
```

2) Set environment variables (recommended) and ensure the database exists. Copy .env.example to .env and fill in values, or export directly in your shell.

Database defaults in code point to: postgresql://alwayscodedfresh:YOUR_PASSWORD@localhost:5432/upwork_scraper

To create the DB (psql):

```sql
-- From psql connected to postgres
CREATE DATABASE upwork_scraper;
```

3) Run the pipeline step-by-step (manual login required in step 1):

```bash
# 1) Scrape recent Upwork jobs (prompts you to login manually)
python main.py

# 2) Classify relevance and website fields with OpenAI
python ai_job_category_checker.py

# 3) Download poster sites and extract contact details
python scrapy.py

# 4) Generate tailored email + SMS pitches
python generate_pitch.py

# 5) Optional: Upload relevant listings to a local Rails API
python upload_to_rails.py
```


## Operational notes

- Manual Upwork login: main.py opens an undetected Chrome instance, navigates to Upwork login, and waits for you to press Enter after logging in.
- Recency filter: main.py only collects postings ~24 hours old by default and paginates until a run of older posts is reached.
- Idempotency: main.py won’t insert duplicate job_url values (unique constraint). ai_job_category_checker.py currently reprocesses a LIMIT 300 window each run; consider filtering only unclassified rows to reduce token use.
- Network timeouts: scrapy.py treats website download timeouts as manual_review = true.
- Rails API: upload_to_rails.py posts to http://localhost:3000/api/job_listings; adjust RAILS_API_URL if your endpoint differs.


## Security and configuration

Important: Don’t commit secrets. Several scripts currently hardcode database credentials and an OpenAI API key. You should:

- Rotate any exposed OpenAI keys immediately and use environment variables (OPENAI_API_KEY) going forward.
- Prefer a DATABASE_URL env var instead of hardcoded credentials.
- Optionally centralize settings in config.py and have all scripts import from it.

See .env.example for suggested variables.


## Known gaps and improvements

- Paths in run_all.sh refer to a different folder; update or remove in favor of the explicit steps above.
- setup_database.sql and migrations.sql use upwork_scraper_db, while the app uses upwork_scraper. For consistency, keep using upwork_scraper unless you update all code.
- ai_job_category_checker.py uses a LIMIT 300 and doesn’t filter already-classified rows; refine the query.
- Consolidate database model definitions (main.py vs database_setup.py) to a single source of truth.
- Move all credentials to env vars and load them in one place.
- Add unit tests and smoke tests for each stage.


## Troubleshooting

- Chromedriver issues: If undetected-chromedriver caching misbehaves, try removing its cache:
  rm -rf ~/.cache/undetected_chromedriver

- SSL or network errors when downloading sites: scrapy.py marks entries manual_review = true; you can retry later.

- Database not found: Create the upwork_scraper DB as shown above or change DATABASE_URL to match your setup.


## Commands reference (optional)

List databases and tables in psql:

```sql
\l
\dt
SELECT * FROM job_listings LIMIT 10;
```

Restore from backup (example):

```bash
pg_restore -U <user> -h localhost -d upwork_scraper upwork_scraper_backup_YYYYMMDD_HHMMSS.sql
```

Rotate OpenAI API key and set it without committing to git:

```bash
export OPENAI_API_KEY="sk-..."
```

That’s it—use the Quick start to run the full pipeline end-to-end.




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::: NEW PROMPT :::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



Prompt:

You are an experienced professional with over 15 years of expertise in web development, graphic design, and digital solutions. Your company, Always Coded Fresh (www.alwayscodedfresh.com), has worked with clients globally, providing high-quality and creative web design services that effectively convey each client's brand story. You are now looking to tailor a pitch to a potential client on Upwork.

Use the information provided below about the job listing to create a customized email and SMS message pitch. The pitch should highlight your experience, emphasize relevant skills or services that match the job posting (e.g., if it's about UI/UX, emphasize your UI/UX expertise; if it's about software development, highlight your software services). Mention that your approach focuses on strategic design, excellent user experience, and cutting-edge technology. Ensure that both the email and SMS are engaging, concise, and directly address the client's needs as outlined in the job posting.

Job Listing Information:
Job Title: {job_title}
Job Description: {job_description}
Expected Response:
A tailored email pitch introducing yourself (Antonio from Always Coded Fresh), briefly describing your company and relevant experience, and explaining how your services align with the client's needs.
A concise SMS version of the pitch that captures the key points for a quick introduction.
Output both the email and SMS in a structured JSON format:

json

{
  "job_listing_id": "{job_listing_id}",
  "email_pitch": "{full_email_pitch_here}",
  "sms_pitch": "{short_sms_pitch_here}"
}








::::: QUERY Grab website_urls that are not null or empty


SELECT website_url, job_url
FROM job_listings
WHERE website_url IS NOT NULL AND website_url <> '';


SELECT id, website_url, job_url, classification_snippet, website_type, emails, phones, facebook, twitter, linkedin, instagram
FROM job_listings
WHERE website_url IS NOT NULL
    AND website_url <> ''
    AND website_type = 'third_party'
    AND relevance = TRUE;



:::: CREATED 36 Hours AGO
        SELECT id, website_url, job_url, classification_snippet, website_type, emails, phones, facebook, twitter, linkedin, instagram
        FROM job_listings
        WHERE website_url IS NOT NULL
            AND website_url <> ''
            AND website_type = 'third_party'
            AND relevance = TRUE
            AND phones <> ''
            AND phones IS NOT NULL
            AND created_at >= NOW() - INTERVAL '36 hours';



SELECT id, website_url, job_url, classification_snippet, website_type, emails, phones, facebook, twitter, linkedin, instagram
FROM job_listings
WHERE website_url IS NOT NULL
    AND website_url <> ''
    AND website_type = 'third_party'
    AND relevance = TRUE
    AND phones <> ''
    AND phones IS NOT NULL;


















upwork_scraper=# \d job_listings

                                              Table "public.job_listings"
         Column         |            Type             | Collation | Nullable |                 Default
------------------------+-----------------------------+-----------+----------+------------------------------------------
 id                     | integer                     |           | not null | nextval('job_listings_id_seq'::regclass)
 job_url                | character varying           |           | not null |
 title                  | character varying           |           |          |
 description            | character varying           |           |          |
 location               | character varying           |           |          |
 post_date              | character varying           |           |          |
 posted_time            | character varying           |           |          |
 job_link               | character varying           |           |          |
 fresh                  | boolean                     |           |          |
 date_added             | timestamp without time zone |           |          |
 date_updated           | timestamp without time zone |           |          |
 relevance              | boolean                     |           |          |
 website_present        | boolean                     |           |          |
 website_url            | text                        |           |          |
 website_type           | character varying(255)      |           |          |
 classification_snippet | text                        |           |          |
Indexes:
    "job_listings_pkey" PRIMARY KEY, btree (id)
    "job_listings_job_url_key" UNIQUE CONSTRAINT, btree (job_url)










:::::::::: Invest in Upwork Credits ::::::::::
https://sandiego.craigslist.org/csd/web/d/san-diego-web-developer-with-design/7803221564.html
https://sfbay.craigslist.org/eby/web/d/san-pablo-web-developer-need/7811337836.html
