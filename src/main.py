import time

from data.market_data import MarketData
from execution.live_broker import LiveBroker
from filters.trade_limiter import TradeLimiter
from strategy.variants import MeanReversionStrategy
from utils.config import Config
from utils.logger import log


def main():
    if not Config.ENABLE_LIVE_TRADING:
        log.error("ENABLE_LIVE_TRADING=false. Set to true in .env to place live orders.")
        return

    log.info("=== Live trading loop (auto execution enabled) ===")

    data = MarketData(
        Config.LIVE_SYMBOL,
        timeframe=Config.LIVE_TIMEFRAME,
        limit=Config.LIVE_CANDLE_LOOKBACK
    )
    strategy = MeanReversionStrategy(
        Config.LIVE_SYMBOL,
        atr_mult=Config.ATR_MULT,
        rsi_low=Config.RSI_LOW,
        rsi_high=Config.RSI_HIGH,
        min_stretch=Config.MIN_STRETCH,
        min_stretch_atr_mult=Config.MIN_STRETCH_ATR_MULT
    )
    limiter = TradeLimiter(
        max_trades_per_day=Config.MAX_TRADES_PER_DAY,
        max_daily_loss_pct=Config.MAX_DAILY_LOSS_PCT,
        max_daily_profit_pct=Config.MAX_DAILY_PROFIT_PCT
    )
    try:
        broker = LiveBroker(
            symbol=Config.LIVE_SYMBOL,
            leverage=Config.LIVE_LEVERAGE,
            risk_per_trade=Config.RISK_PER_TRADE
        )
    except ValueError as exc:
        log.error(str(exc))
        return

    last_candle_ts = None

    while True:
        candles = data.fetch_ohlcv()
        if candles.empty:
            log.warning("No candle data — retrying.")
            time.sleep(Config.LIVE_POLL_SECONDS)
            continue

        last = candles.iloc[-1]
        last_ts = last["timestamp"]

        if last_candle_ts is not None and last_ts <= last_candle_ts:
            broker.sync_position(mark_price=float(last["close"]), trade_limiter=limiter)
            time.sleep(Config.LIVE_POLL_SECONDS)
            continue

        last_candle_ts = last_ts
        signal = strategy.generate_signal(candles)

        broker.sync_position(mark_price=float(last["close"]), trade_limiter=limiter)

        if signal.is_actionable() and limiter.can_trade(now_utc=last_ts):
            if not broker.has_open_position():
                opened = broker.open_position(
                    side=signal.side,
                    entry_price=float(signal.entry_price),
                    stop_loss=float(signal.stop_loss),
                    take_profit=float(signal.take_profit)
                )
                if opened:
                    limiter.record_trade_opened()

        log.info(f"Signal for {Config.LIVE_SYMBOL}: {signal.side} ({signal.reason})")
        time.sleep(Config.LIVE_POLL_SECONDS)


if __name__ == "__main__":
    main()
