"""
Configuration Management for the Assessment Project
Handles environment setup, paths, and constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Data Files
CSV_FILE = os.getenv('CSV_FILE', 'pico8_games.csv')
CSV_PATH = PROJECT_ROOT / CSV_FILE

# Database
PERSIST_DIR = os.getenv('PERSIST_DIR', './pico8_db')
DB_PATH = PROJECT_ROOT / PERSIST_DIR

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# Scraper Configuration
SCRAPER_CONFIG = {
    'base_url': 'https://www.lexaloffle.com/bbs/?cat=7&carts_tab=1&#sub=2&mode=carts',
    'num_games': 100,
    'page_load_timeout': 10,
    'request_timeout': 10,
    'rate_limit_delay': 2,  # seconds between requests
    'headless': True,
}

# RAG Configuration
RAG_CONFIG = {
    'chunk_size': 1000,
    'chunk_overlap': 100,
    'embeddings_model': 'text-embedding-ada-002',
    'retriever_k': 3,
    'llm_temperature': 0.2,
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
}

# Ensure directories exist
os.makedirs(DB_PATH, exist_ok=True)
os.makedirs(PROJECT_ROOT / 'logs', exist_ok=True)


def validate_setup():
    """Validate project setup and dependencies"""
    import sys
    
    errors = []
    warnings = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        errors.append("Python 3.8+ is required")
    
    # Check API key
    if not OPENAI_API_KEY:
        warnings.append("OPENAI_API_KEY not set. Some features will be limited.")
    
    # Check required packages
    required_packages = [
        'requests', 'beautifulsoup4', 'selenium', 'pandas',
        'langchain', 'chromadb', 'dotenv'
    ]
    
    import importlib
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
        except ImportError:
            errors.append(f"Package '{package}' not installed. Run: pip install -r requirements.txt")
    
    if errors:
        print("\n❌ Setup Errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if warnings:
        print("\n⚠️  Setup Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("\n✅ Setup validation passed!")
    return True


if __name__ == '__main__':
    validate_setup()
