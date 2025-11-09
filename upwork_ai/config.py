import os

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/lead_system_development')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Chrome configuration
CHROME_BINARY_PATH = '/Applications/Google Chrome 2.app/Contents/MacOS/Google Chrome'

# Logging configuration
LOG_LEVEL = 'INFO'
