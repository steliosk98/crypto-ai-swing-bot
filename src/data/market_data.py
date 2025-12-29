import ccxt
import pandas as pd
from datetime import datetime
from utils.logger import log
from utils.config import Config


def _init_client():
    """Initialize the CCXT Binance client with API keys."""
    if not Config.BINANCE_API_KEY or not Config.BINANCE_API_SECRET:
        log.warning("Binance API keys not set — reading public market data only.")

    return ccxt.binance({
        'apiKey': Config.BINANCE_API_KEY,
        'secret': Config.BINANCE_API_SECRET,
        'enableRateLimit': True
    })


client = _init_client()


def fetch_ohlcv(symbol: str, timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV candles and return as pandas DataFrame.
    
    Columns: timestamp, open, high, low, close, volume
    """
    log.info(f"Fetching {limit} {timeframe} candles for {symbol}...")

    try:
        data = client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception as e:
        log.error(f"Error fetching candles: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    log.info(f"Fetched {len(df)} rows for {symbol}")
    return df


if __name__ == "__main__":
    # Test run
    candles = fetch_ohlcv("BTC/USDT", timeframe="1h", limit=10)
    print(candles.tail())