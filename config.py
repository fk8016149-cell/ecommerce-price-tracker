import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    # MySQL Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "price_tracker_db")

    @classmethod
    def get_db_url(cls, with_db: bool = True) -> str:
        # If with_db is False, connects to MySQL root to create the database if missing
        password_part = f":{cls.DB_PASSWORD}" if cls.DB_PASSWORD else ""
        db_part = f"/{cls.DB_NAME}" if with_db else ""
        return f"mysql+pymysql://{cls.DB_USER}{password_part}@{cls.DB_HOST}:{cls.DB_PORT}{db_part}?charset=utf8mb4"

    # Ethical & Legal Scraping Settings
    SCRAPE_DELAY_SECONDS: float = float(os.getenv("SCRAPE_DELAY_SECONDS", "3.0"))
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "20"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "SmartPriceBot/1.0 (+http://ethical-scraper.local; Price Tracker Bot)"
    )
    ENFORCE_ROBOTS_TXT: bool = os.getenv("ENFORCE_ROBOTS_TXT", "True").lower() in ("true", "1", "yes")

config = Config()

