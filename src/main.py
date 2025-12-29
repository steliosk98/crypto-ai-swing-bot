from time import sleep

from utils.logger import log
from utils.config import Config

from data.market_data import fetch_ohlcv
from indicators.indicator_engine import add_indicators

from strategy.btc_trend_pullback import BTCTrendPullbackStrategy
from strategy.regime import detect_regime, MarketRegime

from ai.ai_filter import AIFilter
from filters.trade_limiter import TradeLimiter


# --- Configurable parameters ---
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
CANDLE_LOOKBACK = 300  # how many candles to pull

# Instantiate modules
strategy = BTCTrendPullbackStrategy(symbol=SYMBOL)
ai_filter = AIFilter(model_name="gpt-4.1-mini")   # placeholder until API enabled
trade_limiter = TradeLimiter(
    max_trades_per_day=3,
    max_daily_loss_pct=0.02,
    max_daily_profit_pct=0.015
)


def run_cycle():
    log.info(f"=== Running bot cycle for {SYMBOL} on {TIMEFRAME} ===")

    # --- Fetch market data ---
    candles = fetch_ohlcv(SYMBOL, TIMEFRAME, limit=CANDLE_LOOKBACK)
    if candles.empty:
        log.warning("No candle data — skipping cycle.")
        return

    # --- Add indicators ---
    candles = add_indicators(candles)

    # --- Detect regime ---
    regime = detect_regime(candles)
    log.info(f"Market regime detected: {regime.value}")

    # --- Generate raw strategy signal ---
    raw_signal = strategy.generate_signal(candles)
    log.info(f"Strategy signal: {raw_signal.side} | Reason: {raw_signal.reason}")

    # --- Apply AI filter ---
    filtered_signal = ai_filter.evaluate_signal(raw_signal, candles)
    log.info(f"Post-AI signal: {filtered_signal.side} | Conf={filtered_signal.confidence:.2f}")

    # --- Check trade limits ---
    if not trade_limiter.can_trade():
        log.info("Trade limiter blocking new trades.")
        return

    # --- Final decision ---
    if filtered_signal.is_actionable():
        log.success(
            f"FINAL DECISION: OPEN {filtered_signal.side} at {filtered_signal.entry_price}"
            f" | SL {filtered_signal.stop_loss} | TP {filtered_signal.take_profit}"
            f" | Reason: {filtered_signal.reason}"
        )
        # execution placeholder
        # record trade open in limiter
        trade_limiter.record_trade_opened()

    else:
        log.info("FINAL DECISION: NO TRADE")


def main():
    log.info("=== Crypto AI Swing Bot starting ===")
    Config.show_loaded()

    # Single execution for now — scheduler comes next
    run_cycle()

    log.info("=== Bot cycle complete ===")


if __name__ == "__main__":
    main()