from time import sleep

from utils.logger import log
from utils.config import Config
from data.market_data import fetch_ohlcv


SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
LIMIT = 100


def run_cycle():
    """
    Single bot cycle:
    - Fetch recent candles for BTC/USDT
    - (Later) Generate signals, call AI, manage trades
    """
    log.info(f"Starting cycle for {SYMBOL} on {TIMEFRAME} timeframe")

    candles = fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=LIMIT)
    if candles.empty:
        log.warning("No candles received, skipping cycle.")
        return

    last_row = candles.iloc[-1]
    log.info(
        f"Latest candle — time: {last_row['timestamp']}, "
        f"open: {last_row['open']}, high: {last_row['high']}, "
        f"low: {last_row['low']}, close: {last_row['close']}, "
        f"volume: {last_row['volume']}"
    )

    # Placeholder: here is where strategy + AI + execution will go
    # e.g. signal = strategy.generate_signal(candles)
    #       decision = ai_filter.evaluate(signal, context)
    #       execution.execute(decision)


def main():
    log.info("=== Crypto AI Swing Bot starting up ===")

    # Basic config check (keys can be missing for now; public data still works)
    Config.show_loaded()

    # For now, just run a single cycle and exit.
    # Later we'll replace this with a scheduler loop.
    run_cycle()

    log.info("=== Bot cycle complete (single-run mode) ===")


if __name__ == "__main__":
    main()