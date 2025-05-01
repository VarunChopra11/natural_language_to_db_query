from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv('POSTGRESDB_NAME', 'yourdbname'),
    'user': os.getenv('POSTGRESDB_USER', 'yourusername'),
    'password': os.getenv('POSTGRESDB_PASSWORD', 'yourpassword'),
    'host': os.getenv('POSTGRESDB_HOST', 'localhost'),
    'port': os.getenv('POSTGRESDB_PORT', '5432')
}

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your_gemini_api_key')
