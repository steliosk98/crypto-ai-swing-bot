import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env if present
env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(env_path)

class Config:
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Basic validation
    @staticmethod
    def show_loaded():
        print("Config Loaded:")
        print(f" - Binance Key: {'SET' if Config.BINANCE_API_KEY else 'MISSING'}")
        print(f" - OpenAI Key: {'SET' if Config.OPENAI_API_KEY else 'MISSING'}")