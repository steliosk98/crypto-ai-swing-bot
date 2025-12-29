import pandas as pd
from utils.logger import log

from data.historical_data import load_historical_ohlcv
from indicators.indicator_engine import add_indicators

from strategy.btc_trend_pullback import BTCTrendPullbackStrategy
from strategy.regime import detect_regime
from execution.paper_broker import PaperBroker
from filters.trade_limiter import TradeLimiter
from backtesting.session_state import SessionState, TradeRecord


def run_backtest(
    symbol="BTC/USDT",
    timeframe="1h",
    start="2021-01-01",
    end="2022-01-01"
):
    log.info(f"=== Starting Backtest for {symbol} ({timeframe}) ===")

    # Load historical candles
    candles = load_historical_ohlcv(symbol, timeframe, start, end)
    if candles.empty:
        log.error("No historical data — cannot run backtest.")
        return

    # Add indicators once (we slice progressively inside loop)
    candles = add_indicators(candles)

    # instantiate modules
    strategy = BTCTrendPullbackStrategy(symbol)
    broker = PaperBroker()
    trade_limiter = TradeLimiter()
    session = SessionState()

    # iterate through candles one-by-one, starting after indicator warmup
    for i in range(300, len(candles)):  # ensure indicators exist
        window = candles.iloc[:i]       # slice up to current candle
        last = window.iloc[-1]

        # 1) detect regime (for logging only here — strategy uses internally)
        regime = detect_regime(window)

        # 2) generate strategy signal
        signal = strategy.generate_signal(window)

        # NOTE — during backtesting phase A, we skip AI filtering.
        # future: import AI filter and apply here as second stage.

        # 3) evaluate new trade (ONLY if no open position)
        if not broker.has_open_position():
            if trade_limiter.can_trade() and signal.is_actionable():
                opened = broker.open_position(
                    symbol,
                    signal.side,
                    signal.entry_price,
                    signal.stop_loss,
                    signal.take_profit
                )
                if opened:
                    trade_limiter.record_trade_opened()

        # 4) check open position for exit triggers
        pnl_pct = broker.check_and_close(
            high=last["high"],
            low=last["low"],
            close=last["close"],
            trade_limiter=trade_limiter
        )

        # 5) record closing trades into session state
        if pnl_pct is not None:
            exit_price = (
                signal.take_profit if pnl_pct > 0 else signal.stop_loss
            )
            trade = TradeRecord(
                symbol=symbol,
                side=signal.side,
                entry_price=signal.entry_price,
                exit_price=exit_price,
                pnl_pct=pnl_pct,
                reason=signal.reason,
                timestamp=last["timestamp"]
            )
            session.record_trade(trade)

    log.info("=== Backtest Complete ===")
    session.print_summary()
    return session


if __name__ == "__main__":
    # UPDATE THESE DATES TO TEST DIFFERENT PERIODS
    run_backtest(
        symbol="BTC/USDT",
        timeframe="1h",
        start="2021-01-01",
        end="2022-01-01"
    )