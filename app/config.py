from dotenv import load_dotenv
import os

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

DATABASE_URL = os.getenv("GCP_DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

ZAPPER_API_KEY = os.getenv("ZAPPER_API_KEY")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-east5")
CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3-5-haiku@20241022")

SA_INFO = os.getenv("SA_INFO")
