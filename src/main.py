from utils.logger import log
from data.market_data import MarketData
from strategy.btc_trend_pullback import BTCTrendPullbackStrategy
from filters.trade_limiter import TradeLimiter


SYMBOL = "BTC/USDC"
TIMEFRAME = "1h"
CANDLE_LOOKBACK = 200


def main():
    log.info("=== Live decision cycle — no order execution ===")

    data = MarketData(SYMBOL, timeframe=TIMEFRAME, limit=CANDLE_LOOKBACK)
    candles = data.fetch_ohlcv()
    if candles.empty:
        log.warning("No candle data — skipping cycle.")
        return

    strategy = BTCTrendPullbackStrategy(SYMBOL)
    signal = strategy.generate_signal(candles)

    limiter = TradeLimiter()
    if signal.is_actionable() and limiter.can_trade():
        limiter.record_trade_opened()
    log.info(f"Signal for {SYMBOL}: {signal.side} ({signal.reason})")


if __name__ == "__main__":
    main()
