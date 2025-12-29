import pandas as pd

def detect_range(candles: pd.DataFrame, lookback: int = 50):
    """
    Identify the recent trading range by looking back N candles.
    Returns (range_low, range_high) as floats.
    """
    recent = candles.tail(lookback)
    range_low = float(recent["low"].min())
    range_high = float(recent["high"].max())
    return range_low, range_high