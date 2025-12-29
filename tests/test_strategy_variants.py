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
