import pandas as pd
from indicators.indicator_engine import add_indicators
from strategy.btc_trend_pullback import BTCTrendPullbackStrategy

def test_strategy_generates_long_in_uptrend():
    strategy = BTCTrendPullbackStrategy()

    # synthetic uptrend
    prices = list(range(1, 401))
    df = pd.DataFrame({
        "timestamp": pd.date_range("2022-01-01", periods=400, freq="H"),
        "open": prices,
        "high": prices,
        "low": prices,
        "close": prices,
        "volume": [1]*400
    })

    df = add_indicators(df)
    signal = strategy.generate_signal(df)
    
    # in a strong uptrend we expect a long or flat (never a short)
    assert signal.side in ("LONG", "FLAT")