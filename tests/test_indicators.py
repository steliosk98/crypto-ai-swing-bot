import pandas as pd
from indicators.indicator_engine import add_indicators

def test_indicator_engine_basic():
    # minimal fake data: 300 candles ascending
    df = pd.DataFrame({
        "timestamp": pd.date_range("2022-01-01", periods=300, freq="H"),
        "open": range(300),
        "high": range(1, 301),
        "low": range(0, 300),
        "close": range(1, 301),
        "volume": [1]*300
    })

    df = add_indicators(df)
    last = df.iloc[-1]

    assert not last["ema21"] is None
    assert not last["ema50"] is None
    assert not last["sma200"] is None
    assert not last["rsi14"] is None
    assert not last["atr14"] is None


def test_rsi_preserves_source_index():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2022-01-01", periods=40, freq="H"),
            "open": range(40),
            "high": range(1, 41),
            "low": range(40),
            "close": range(1, 41),
            "volume": [1] * 40,
        },
        index=range(100, 140),
    )

    df = add_indicators(df)
    assert df["rsi14"].index.equals(df.index)
    assert not pd.isna(df.iloc[-1]["rsi14"])
