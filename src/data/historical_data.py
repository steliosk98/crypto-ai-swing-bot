import ccxt
import pandas as pd
from pathlib import Path
from utils.logger import log


def _load_local_bitstamp_btcusd(
    start: str,
    end: str = None,
    path: Path = Path("data/Bitstamp_BTCUSD_1h.csv"),
) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path, skiprows=1)
    df["timestamp"] = pd.to_datetime(df["date"], utc=True)
    df = df.rename(
        columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "Volume BTC": "volume",
        }
    )
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df = df.sort_values("timestamp")

    start_dt = pd.Timestamp(start, tz="UTC")
    if end:
        end_dt = pd.Timestamp(end, tz="UTC")
        df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]
    else:
        df = df[df["timestamp"] >= start_dt]

    return df.reset_index(drop=True)


def load_historical_ohlcv(
    symbol: str = "BTC/USDC",
    timeframe: str = "1h",
    start: str = "2024-01-01",
    end: str = None,
    limit: int = 1500
):
    """
    Load OHLCV data using Binance USDⓈ-M futures (USDC perpetual).

    Why USDⓈ-M futures?
        Binance USDC perpetuals are listed under USDⓈ-M futures.

    Parameters:
        symbol      - "BTC/USDC"
        timeframe   - "1h", "4h"
        start       - ISO date string
        end         - ISO date string or None = now
        limit       - max candles per fetch
    """

    if symbol == "BTC/USD" and timeframe == "1h":
        local_df = _load_local_bitstamp_btcusd(start, end)
        if not local_df.empty:
            log.info(f"Loaded {len(local_df)} local Bitstamp BTC/USD candles.")
        return local_df

    exchange = ccxt.binanceusdm({
        "enableRateLimit": True,
        "options": {"defaultType": "future"}  # USDⓈ-M futures
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

    start_dt = pd.Timestamp(start)
    if end:
        end_dt = pd.Timestamp(end)
        df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]
    else:
        df = df[df["timestamp"] >= start_dt]

    if df.empty:
        log.error("No futures data retrieved for requested window.")
        return pd.DataFrame()

    log.info(f"Loaded {len(df)} futures candles for {symbol}.")
    return df
