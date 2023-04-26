import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://username:password@localhost/dbname")
ELASTIC_SEARCH_FULL_URL_KEY = os.environ.get("ELASTIC_SEARCH_FULL_URL_KEY")