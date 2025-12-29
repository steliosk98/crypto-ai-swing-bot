import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    MACD indicator:
    - MACD line
    - Signal line
    - Histogram (difference)
    """
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a standardized set of indicators to a candle DataFrame.
    These will feed strategy & AI filtering later.
    """
    close = df["close"]

    df["sma50"] = sma(close, 50)
    df["sma200"] = sma(close, 200)

    df["ema21"] = ema(close, 21)
    df["ema50"] = ema(close, 50)

    df["rsi14"] = rsi(close, 14)

    df["macd_line"], df["macd_signal"], df["macd_hist"] = macd(close)

    return df