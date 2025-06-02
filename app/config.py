from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your_gemini_api_key')

DATABASE_URL = os.getenv("GCP_DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")