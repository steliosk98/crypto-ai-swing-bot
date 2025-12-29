import pandas as pd
from indicators.indicator_engine import add_indicators
from strategy.regime import detect_regime, MarketRegime

def test_regime_detection_trending_up():
    prices = list(range(1, 401))  # strong uptrend
    df = pd.DataFrame({
        "timestamp": pd.date_range("2022-01-01", periods=400, freq="H"),
        "open": prices,
        "high": prices,
        "low": prices,
        "close": prices,
        "volume": [1]*400
    })

    df = add_indicators(df)
    regime = detect_regime(df)
    assert regime == MarketRegime.UPTREND