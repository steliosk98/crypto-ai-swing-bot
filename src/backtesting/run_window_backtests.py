from datetime import datetime
import os

from backtesting.session_state import SessionState, TradeRecord
from backtesting.visualizer import plot_equity_curve
from data.historical_data import load_historical_ohlcv
from indicators.indicator_engine import add_indicators
from execution.paper_broker import PaperBroker
from filters.trade_limiter import TradeLimiter
from strategy.variants import MeanReversionStrategy
from utils.config import Config
from utils.logger import log


def _run_window(
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
) -> SessionState | None:
    candles = load_historical_ohlcv(symbol, timeframe, start, end)
    if candles.empty:
        log.warning(f"No data for window {start} → {end}.")
        return None

    print(
        f"Data range: {candles['timestamp'].iloc[0].date()} → "
        f"{candles['timestamp'].iloc[-1].date()} | Rows: {len(candles)}"
    )
    candles = add_indicators(candles)
    strategy = MeanReversionStrategy(
        symbol,
        atr_mult=Config.ATR_MULT,
        rsi_low=Config.RSI_LOW,
        rsi_high=Config.RSI_HIGH,
        min_stretch=Config.MIN_STRETCH,
        min_stretch_atr_mult=Config.MIN_STRETCH_ATR_MULT
    )
    broker = PaperBroker(fee_rate=0.0005)
    limiter = TradeLimiter(log_resets=False, log_blocks=False)
    session = SessionState()
    active_signal = None

    for i in range(300, len(candles)):
        window = candles.iloc[:i]
        last = window.iloc[-1]
        signal = strategy.generate_signal(window)

        if not broker.has_open_position() and limiter.can_trade(now_utc=last["timestamp"]) and signal.is_actionable():
            if broker.open_position(
                symbol=symbol,
                side=signal.side,
                entry=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            ):
                limiter.record_trade_opened()
                active_signal = signal

        pnl_pct = broker.check_and_close(
            high=last["high"],
            low=last["low"],
            close=last["close"],
            trade_limiter=limiter
        )

        if pnl_pct is not None and active_signal:
            exit_price = (
                active_signal.take_profit if pnl_pct > 0 else active_signal.stop_loss
            )
            session.record_trade(
                TradeRecord(
                    symbol=symbol,
                    side=active_signal.side,
                    entry_price=active_signal.entry_price,
                    exit_price=exit_price,
                    pnl_pct=pnl_pct,
                    reason=active_signal.reason,
                    timestamp=last["timestamp"]
                )
            )
            active_signal = None

    return session


def run_multi_window_backtests(
    symbol: str = "BTC/USD",
    timeframe: str = "1h",
    start: str = "2016-01-01",
    end: str = "2025-12-01",
) -> None:
    # Reduce noisy per-trade logs for long multi-window runs.
    log.remove()
    log.add(lambda msg: print(msg, end=""), level="WARNING")

    print(f"=== Backtest Window: {start} → {end} ===")
    full_session = _run_window(symbol, timeframe, start, end)
    if full_session:
        full_session.print_summary()
        os.makedirs("logs", exist_ok=True)
        output_path = os.path.join("logs", "equity_curve_full.png")
        plot_equity_curve(full_session, save_path=output_path, show=False)
        print(f"Saved equity curve to {output_path}")

    start_year = datetime.fromisoformat(start).year
    end_year = datetime.fromisoformat(end).year

    for year in range(start_year, end_year + 1):
        year_start = f"{year}-01-01"
        year_end = f"{year}-12-31"
        if year == end_year:
            year_end = end

        print(f"=== Yearly Backtest: {year_start} → {year_end} ===")
        session = _run_window(symbol, timeframe, year_start, year_end)
        if session:
            print(f"--- Summary for {year} ---")
            session.print_summary()


if __name__ == "__main__":
    run_multi_window_backtests()
