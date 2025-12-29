from enum import Enum
import pandas as pd
import numpy as np


class MarketRegime(Enum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    SIDEWAYS = "SIDEWAYS"
    UNKNOWN = "UNKNOWN"


def detect_regime(candles: pd.DataFrame) -> MarketRegime:
    """
    Classify the current market regime based on price structure & indicators.
    Logic is deliberately simple and rule-based so it's backtestable.

    Conditions (initial version):
    - Uptrend: price > SMA200 and EMA21 > EMA50
    - Downtrend: price < SMA200 and EMA21 < EMA50
    - Sideways: otherwise
    """

    if candles is None or candles.empty:
        return MarketRegime.UNKNOWN

    last = candles.iloc[-1]

    # Must have indicators for regime detection
    required = ["sma200", "ema21", "ema50", "close"]
    if any(key not in last or pd.isna(last[key]) for key in required):
        return MarketRegime.UNKNOWN

    price = float(last["close"])
    sma200 = float(last["sma200"])
    ema21 = float(last["ema21"])
    ema50 = float(last["ema50"])

    # ---- Uptrend ----
    if price > sma200 and ema21 > ema50:
        return MarketRegime.UPTREND

    # ---- Downtrend ----
    if price < sma200 and ema21 < ema50:
        return MarketRegime.DOWNTREND

    # ---- Sideways ----
    return MarketRegime.SIDEWAYS