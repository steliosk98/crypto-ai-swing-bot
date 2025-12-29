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

    LIVE_SYMBOL = os.getenv("LIVE_SYMBOL", "BTC/USDC")
    LIVE_TIMEFRAME = os.getenv("LIVE_TIMEFRAME", "1h")
    LIVE_CANDLE_LOOKBACK = int(os.getenv("LIVE_CANDLE_LOOKBACK", "200"))
    LIVE_POLL_SECONDS = int(os.getenv("LIVE_POLL_SECONDS", "60"))
    LIVE_LEVERAGE = int(os.getenv("LIVE_LEVERAGE", "1"))
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.01"))
    MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "5"))
    MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.02"))
    MAX_DAILY_PROFIT_PCT = float(os.getenv("MAX_DAILY_PROFIT_PCT", "0.015"))
    ENABLE_LIVE_TRADING = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"

    # Basic validation
    @staticmethod
    def show_loaded():
        print("Config Loaded:")
        print(f" - Binance Key: {'SET' if Config.BINANCE_API_KEY else 'MISSING'}")
        print(f" - OpenAI Key: {'SET' if Config.OPENAI_API_KEY else 'MISSING'}")
