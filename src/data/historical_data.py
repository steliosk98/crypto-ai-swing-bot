import ccxt
import pandas as pd
from datetime import datetime, timedelta
from utils.logger import log


def load_historical_ohlcv(
    symbol: str,
    timeframe: str = "1h",
    start: str = "2021-01-01",
    end: str = None,
    limit: int = 1000
) -> pd.DataFrame:
    """
    Load historical candles by iterating CCXT fetch_ohlcv in time batches.
    Returns a DataFrame identical to fetch_ohlcv output.
    
    Parameters:
        symbol: e.g. "BTC/USDT"
        timeframe: e.g. "1h"
        start: e.g. "2021-01-01"
        end: e.g. "2023-01-01" or None (default = now)
        limit: max candles per fetch_ohlcv call
        
    Notes:
        - CCXT returns timestamps in ms since epoch
        - This function loops until end time is reached
    """

    exchange = ccxt.binance({
        "enableRateLimit": True
    })

    start_ts = int(pd.Timestamp(start).timestamp() * 1000)
    end_ts = int(pd.Timestamp(end).timestamp() * 1000) if end else None

    all_data = []
    fetch_ts = start_ts

    log.info(f"Loading historical {symbol} {timeframe} from {start} to {end or 'now'}")

    while True:
        data = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=fetch_ts,
            limit=limit
        )

        if not data:
            break

        all_data.extend(data)

        # move forward in time
        last_ts = data[-1][0]
        fetch_ts = last_ts + 1

        # stop if passed end time
        if end_ts and fetch_ts >= end_ts:
            break

    if not all_data:
        log.error("No historical data retrieved.")
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    
    log.info(f"Loaded {len(df)} candles of historical data.")
    return df