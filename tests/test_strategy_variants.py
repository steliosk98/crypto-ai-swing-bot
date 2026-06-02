import pandas as pd

from strategy.variants import MeanReversionStrategy


def test_mean_reversion_insufficient_data_flat():
    strategy = MeanReversionStrategy()
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="H"),
            "open": range(10),
            "high": range(10),
            "low": range(10),
            "close": range(10),
            "volume": [1] * 10,
        }
    )
    signal = strategy.generate_signal(df)
    assert signal.side == "FLAT"


def test_mean_reversion_downtrend_long_or_flat():
    strategy = MeanReversionStrategy()
    prices = list(range(200, 140, -1))
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=len(prices), freq="H"),
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "volume": [1] * len(prices),
        }
    )
    signal = strategy.generate_signal(df)
    assert signal.side in ("LONG", "FLAT")


def test_mean_reversion_long_requires_price_below_ema():
    strategy = MeanReversionStrategy()
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=50, freq="H"),
            "open": [100] * 50,
            "high": [102] * 50,
            "low": [99] * 50,
            "close": [101] * 50,
            "volume": [1] * 50,
            "ema21": [100] * 50,
            "rsi14": [25] * 50,
            "atr14": [1] * 50,
        }
    )

    signal = strategy.generate_signal(df)
    assert signal.side == "FLAT"

    df.loc[df.index[-1], "close"] = 99
    signal = strategy.generate_signal(df)
    assert signal.side == "LONG"


def test_mean_reversion_short_requires_price_above_ema():
    strategy = MeanReversionStrategy()
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=50, freq="H"),
            "open": [100] * 50,
            "high": [101] * 50,
            "low": [98] * 50,
            "close": [99] * 50,
            "volume": [1] * 50,
            "ema21": [100] * 50,
            "rsi14": [75] * 50,
            "atr14": [1] * 50,
        }
    )

    signal = strategy.generate_signal(df)
    assert signal.side == "FLAT"

    df.loc[df.index[-1], "close"] = 101
    signal = strategy.generate_signal(df)
    assert signal.side == "SHORT"
