from data.historical_data import load_historical_ohlcv

def test_historical_loader_fetches_data():
    df = load_historical_ohlcv(
        symbol="BTC/USDT",
        timeframe="1h",
        start="2022-01-01",
        end="2022-01-02"
    )
    assert len(df) > 0