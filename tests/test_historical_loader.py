import pytest
import ccxt

from data.historical_data import load_historical_ohlcv

def test_historical_loader_fetches_data():
    try:
        df = load_historical_ohlcv(
            symbol="BTC/USDC",
            timeframe="1h",
            start="2024-01-01",
            end="2024-01-02"
        )
    except (ccxt.NetworkError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout):
        pytest.skip("Network unavailable for Binance futures data.")

    assert len(df) > 0
