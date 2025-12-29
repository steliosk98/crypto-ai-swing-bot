import ccxt
import pandas as pd
from utils.logger import log


def load_historical_ohlcv(
    symbol: str = "BTC/USDC",
    timeframe: str = "1h",
    start: str = "2024-01-01",
    end: str = None,
    limit: int = 1500
):
    """
    Load OHLCV data using Binance COIN-M futures (USDC-margined contracts).

    Why COIN-M futures?
        Binance USDC-margined futures are provided under this market type.
        This enables realistic long/short execution on USDC collateral.

    Parameters:
        symbol      - "BTC/USDC"
        timeframe   - "1h", "4h"
        start       - ISO date string
        end         - ISO date string or None = now
        limit       - max candles per fetch
    """

    exchange = ccxt.binancecoinm({
        "enableRateLimit": True,
        "options": {"defaultType": "delivery"}  # COIN-M futures
    })

    start_ts = int(pd.Timestamp(start).timestamp() * 1000)
    end_ts = int(pd.Timestamp(end).timestamp() * 1000) if end else None

    all_data = []
    fetch_ts = start_ts

    log.info(f"Loading futures OHLCV {symbol} {timeframe} from {start} to {end or 'now'}")

    while True:
        batch = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=fetch_ts,
            limit=limit
        )

        if not batch:
            break

        all_data.extend(batch)
        last_ts = batch[-1][0]
        fetch_ts = last_ts + 1

        if end_ts and fetch_ts >= end_ts:
            break

    if not all_data:
        log.error("No futures data retrieved.")
        return pd.DataFrame()

    df = pd.DataFrame(
        all_data,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    log.info(f"Loaded {len(df)} futures candles for {symbol}.")
    return df