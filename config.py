import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Global configuration central class."""

    # API keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB upload limit

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    DATA_FOLDER = os.path.join(BASE_DIR, "data")
    SAMPLE_NEWS_PATH = os.path.join(DATA_FOLDER, "sample_news.txt")

    # Financial analysis
    YFINANCE_PERIOD = "60d"
    YFINANCE_INTERVAL = "1d"
    SMA_SHORT = 7
    SMA_LONG = 20
    MAX_DAILY_VOLATILITY = 0.05

    # News / NLP
    MAX_NEWS_ARTICLES = 10
    TOP_INSIGHTS = 3
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE = 200
    CHUNK_OVERLAP = 50
    TOP_K_RETRIEVAL = 5

    # Mode flags
    HAS_LLM = bool(OPENAI_API_KEY)
    HAS_NEWS_API = bool(NEWS_API_KEY)

    @classmethod
    def ensure_directories(cls):
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.DATA_FOLDER, exist_ok=True)

Config.ensure_directories()

if __name__ == "__main__":
    print("Testing config.py...")
    print(f"SECRET_KEY loaded: {'Yes' if Config.SECRET_KEY else 'No'}")
    print(f"OPENAI_API_KEY loaded: {'Yes' if Config.OPENAI_API_KEY else 'No (Will use fallback)'}")
    print(f"NEWS_API_KEY loaded: {'Yes' if Config.NEWS_API_KEY else 'No'}")
    print(f"UPLOAD_FOLDER configured: {Config.UPLOAD_FOLDER}")
    print(f"SAMPLE_NEWS_PATH configured: {Config.SAMPLE_NEWS_PATH}")
    print("config.py executed successfully.")
