#!/usr/bin/env python3
"""
Contact Information Analyzer for Job Listings
Analyzes job descriptions to extract business contact information
"""

import re
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("contact_analyzer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres@localhost:5432/lead_system_development"

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info(f"Connected to database: {DATABASE_URL}")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    sys.exit(1)

class ContactInfoAnalyzer:
    def __init__(self):
        # Email patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*\[\s*at\s*\]\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*\(\s*at\s*\)\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]

        # Phone patterns (US focused but includes international)
        self.phone_patterns = [
            r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            r'\b(?:\+?1[-.\s]?)?([0-9]{3})[-.\s]([0-9]{3})[-.\s]([0-9]{4})\b',
            r'\b\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}\b'
        ]

        # Website/domain patterns
        self.website_patterns = [
            r'\b(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            r'\b([a-zA-Z0-9.-]+\.(?:com|net|org|edu|gov|co|io|ly|me|us|ca|uk))\b'
        ]

        # Company name indicators
        self.company_indicators = [
            r'\b(?:company|corp|corporation|inc|llc|ltd|limited|group|solutions|services|consulting|agency|firm)\b',
            r'\b(?:we are|our company|our team|our organization|our business|our agency)\b',
            r'\b(?:founded|established|started|launched)\b',
            r'\b(?:ceo|founder|owner|director|manager|president)\b'
        ]

    def extract_emails(self, text):
        """Extract email addresses from text"""
        emails = set()
        for pattern in self.email_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    email = ''.join(match)
                else:
                    email = match
                # Clean up email
                email = re.sub(r'\s*\[\s*at\s*\]\s*', '@', email)
                email = re.sub(r'\s*\(\s*at\s*\)\s*', '@', email)
                email = re.sub(r'\s+', '', email)
                if '@' in email and '.' in email:
                    emails.add(email.lower())
        return list(emails)

    def extract_phones(self, text):
        """Extract phone numbers from text"""
        phones = set()
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Format as (XXX) XXX-XXXX for US numbers
                    if len(match) == 3 and all(len(part) in [3, 4] for part in match):
                        phone = f"({match[0]}) {match[1]}-{match[2]}"
                    else:
                        phone = '-'.join(match)
                else:
                    phone = match
                phones.add(phone)
        return list(phones)

    def extract_websites(self, text):
        """Extract website URLs from text"""
        websites = set()
        for pattern in self.website_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                website = match.lower()
                # Skip common non-business domains
                skip_domains = ['upwork.com', 'freelancer.com', 'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
                if not any(skip in website for skip in skip_domains):
                    if not website.startswith('http'):
                        website = 'https://' + website
                    websites.add(website)
        return list(websites)

    def detect_company_mentions(self, text):
        """Detect if text mentions company/business information"""
        company_score = 0
        text_lower = text.lower()

        for pattern in self.company_indicators:
            matches = re.findall(pattern, text_lower)
            company_score += len(matches)

        return company_score > 0

    def extract_company_name(self, text):
        """Try to extract company name from text"""
        # Look for patterns like "We are XYZ Company" or "XYZ Inc is looking for"
        patterns = [
            r'(?:we are|our company is|our business is|our agency is)\s+([A-Z][A-Za-z\s&]+?)(?:\.|,|\s+(?:and|is|was|has|looking|seeking))',
            r'([A-Z][A-Za-z\s&]+?)\s+(?:inc|llc|ltd|corp|corporation|company|group|solutions|services|consulting|agency)\b',
            r'(?:at|for|from)\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:inc|llc|ltd|corp|corporation|company|group)|\.|,)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return first reasonable match (not too short/long)
                for match in matches:
                    if 2 <= len(match.split()) <= 4:
                        return match.strip()
        return None

    def analyze_job_description(self, description, title=""):
        """Analyze a job description for contact information"""
        if not description:
            return {
                'has_contact_info': False,
                'emails': [],
                'phones': [],
                'websites': [],
                'company_name': None,
                'analysis_summary': 'No description to analyze'
            }

        full_text = f"{title} {description}"

        # Extract contact information
        emails = self.extract_emails(full_text)
        phones = self.extract_phones(full_text)
        websites = self.extract_websites(full_text)
        company_name = self.extract_company_name(full_text)
        has_company_mentions = self.detect_company_mentions(full_text)

        # Determine if this has useful contact info
        has_contact_info = bool(emails or phones or websites or company_name)

        # Create summary
        summary_parts = []
        if emails:
            summary_parts.append(f"{len(emails)} email(s)")
        if phones:
            summary_parts.append(f"{len(phones)} phone(s)")
        if websites:
            summary_parts.append(f"{len(websites)} website(s)")
        if company_name:
            summary_parts.append(f"company: {company_name}")
        elif has_company_mentions:
            summary_parts.append("company mentions detected")

        analysis_summary = "; ".join(summary_parts) if summary_parts else "No contact info found"

        return {
            'has_contact_info': has_contact_info,
            'emails': emails,
            'phones': phones,
            'websites': websites,
            'company_name': company_name,
            'analysis_summary': analysis_summary,
            'company_mentions_detected': has_company_mentions
        }

def analyze_job_listings(limit=None, job_id=None):
    """Analyze job listings for contact information"""
    analyzer = ContactInfoAnalyzer()

    # Build query
    if job_id:
        query = "SELECT id, title, description, job_url FROM job_listings WHERE id = :job_id"
        result = session.execute(text(query), {"job_id": job_id})
    else:
        query = """
        SELECT id, title, description, job_url
        FROM job_listings
        WHERE scanned_for_company_details IS NOT TRUE
        AND description IS NOT NULL
        ORDER BY created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        result = session.execute(text(query))

    jobs = result.fetchall()
    logger.info(f"Found {len(jobs)} job listings to analyze")

    analyzed_count = 0
    updated_count = 0

    for job in jobs:
        try:
            logger.info(f"Analyzing job {job.id}: {job.title[:50]}...")

            # Analyze the job description
            analysis = analyzer.analyze_job_description(job.description, job.title)

            # Update database with results
            update_query = """
            UPDATE job_listings
            SET
                emails = :emails,
                phones = :phones,
                website_url = :website_url,
                company_name = :company_name,
                scanned_for_company_details = true,
                viable_post = :viable_post,
                classification_snippet = :analysis_summary,
                updated_at = NOW()
            WHERE id = :job_id
            """

            # Determine if this is a viable post (has contact info)
            viable_post = analysis['has_contact_info']

            session.execute(text(update_query), {
                "job_id": job.id,
                "emails": json.dumps(analysis['emails']),
                "phones": json.dumps(analysis['phones']),
                "website_url": analysis['websites'][0] if analysis['websites'] else None,
                "company_name": analysis['company_name'],
                "viable_post": viable_post,
                "analysis_summary": analysis['analysis_summary']
            })

            analyzed_count += 1
            if analysis['has_contact_info']:
                updated_count += 1
                logger.info(f"  ✅ Found contact info: {analysis['analysis_summary']}")
            else:
                logger.info(f"  ❌ No contact info found")

        except Exception as e:
            logger.error(f"Error analyzing job {job.id}: {e}")
            continue

    try:
        session.commit()
        logger.info(f"✅ Analysis complete! Analyzed {analyzed_count} jobs, found contact info in {updated_count} jobs")
    except Exception as e:
        logger.error(f"Error committing to database: {e}")
        session.rollback()

def main():
    parser = argparse.ArgumentParser(description='Analyze job listings for contact information')
    parser.add_argument('--limit', type=int, help='Limit number of jobs to analyze')
    parser.add_argument('--job-id', type=int, help='Analyze specific job by ID')

    args = parser.parse_args()

    try:
        analyze_job_listings(limit=args.limit, job_id=args.job_id)
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()