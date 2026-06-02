from utils.logger import log
from utils.config import Config
from data.historical_data import load_historical_ohlcv
from indicators.indicator_engine import add_indicators
from strategy.variants import MeanReversionStrategy
from strategy.regime import detect_regime
from execution.paper_broker import PaperBroker
from filters.trade_limiter import TradeLimiter
from backtesting.session_state import SessionState, TradeRecord
from backtesting.visualizer import plot_equity_curve, plot_drawdowns


def run_backtest(
    symbol: str = Config.LIVE_SYMBOL,
    timeframe: str = Config.LIVE_TIMEFRAME,
    start: str = "2023-01-01",
    end: str = "2025-01-01"
):
    """
    Execute a full backtest over historical futures data (BTC/USDC).
    Uses:
        - COIN-M futures OHLCV for realistic long + short
        - Trend pullback & breakout strategy
        - Paper execution & session tracking
        - Trade limiting rules
        - Visualization
    """

    log.info(f"=== Starting Futures Backtest for {symbol} ({timeframe}) ===")

    # ---- Load Data ----
    candles = load_historical_ohlcv(symbol, timeframe, start, end)
    if candles.empty:
        log.error("No data retrieved — backtest aborted.")
        return

    # ---- Indicators ----
    candles = add_indicators(candles)

    # ---- Components ----
    strategy = MeanReversionStrategy(
        symbol,
        atr_mult=Config.ATR_MULT,
        rsi_low=Config.RSI_LOW,
        rsi_high=Config.RSI_HIGH,
        min_stretch=Config.MIN_STRETCH,
        min_stretch_atr_mult=Config.MIN_STRETCH_ATR_MULT
    )
    broker = PaperBroker(fee_rate=0.0005)
    limiter = TradeLimiter(
        max_trades_per_day=Config.MAX_TRADES_PER_DAY,
        max_daily_loss_pct=Config.MAX_DAILY_LOSS_PCT,
        max_daily_profit_pct=Config.MAX_DAILY_PROFIT_PCT,
        log_resets=False,
        log_blocks=True
    )
    session = SessionState()
    active_signal = None

    # ---- Backtest Loop ----
    for i in range(300, len(candles)):  # warmup for indicators
        window = candles.iloc[:i]
        last = window.iloc[-1]

        # --- Check exit conditions on open trade ---
        pnl_pct = broker.check_and_close(
            high=last["high"],
            low=last["low"],
            close=last["close"],
            trade_limiter=limiter
        )

        # --- Record closed trades ---
        if pnl_pct is not None and active_signal:
            trade = TradeRecord(
                symbol=symbol,
                side=active_signal.side,
                entry_price=active_signal.entry_price,
                exit_price=broker.last_exit_price,
                pnl_pct=pnl_pct,
                reason=active_signal.reason,
                timestamp=last["timestamp"]
            )
            session.record_trade(trade)
            active_signal = None

        # Strategy + Regime
        signal = strategy.generate_signal(window)
        regime = detect_regime(window)

        # --- Open new trade if allowed ---
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

    # ---- Summary ----
    log.info("=== Backtest Complete ===")
    session.print_summary()

    return session


# ---- Entry Point ----
if __name__ == "__main__":
    run_backtest()
