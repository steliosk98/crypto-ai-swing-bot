from dataclasses import dataclass
from typing import Callable, List

from loguru import logger

from backtesting.session_state import SessionState, TradeRecord
from data.historical_data import load_historical_ohlcv
from indicators.indicator_engine import add_indicators
from execution.paper_broker import PaperBroker
from filters.trade_limiter import TradeLimiter
from strategy.btc_trend_pullback import BTCTrendPullbackStrategy
from strategy.variants import (
    TrendBreakoutStrategy,
    MeanReversionStrategy,
    MomentumCrossoverStrategy,
)


@dataclass
class StrategyResult:
    name: str
    session: SessionState


def _run_strategy_loop(strategy, candles, symbol: str) -> SessionState:
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

        if pnl_pct is not None:
            if active_signal:
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


def run_batch_backtest(
    symbol: str = "BTC/USDC",
    timeframe: str = "1h",
    start: str = "2023-01-01",
    end: str = "2025-01-01",
) -> List[StrategyResult]:
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")

    candles = load_historical_ohlcv(symbol, timeframe, start, end)
    if candles.empty:
        print("No data retrieved — batch backtest aborted.")
        return []

    candles = add_indicators(candles)

    strategies = [
        ("TrendPullback", BTCTrendPullbackStrategy(symbol)),
        ("TrendBreakout", TrendBreakoutStrategy(symbol)),
        ("MomentumCrossover", MomentumCrossoverStrategy(symbol)),
        ("MeanRev_base", MeanReversionStrategy(symbol)),
        ("MeanRev_tight", MeanReversionStrategy(symbol, atr_mult=0.8, rsi_low=28, rsi_high=72, min_stretch=0.006)),
        ("MeanRev_wide", MeanReversionStrategy(symbol, atr_mult=1.2, rsi_low=25, rsi_high=75, min_stretch=0.007)),
    ]

    results: List[StrategyResult] = []
    for name, strat in strategies:
        session = _run_strategy_loop(strat, candles, symbol)
        results.append(StrategyResult(name=name, session=session))

    results.sort(key=lambda r: r.session.summary()["return_pct"], reverse=True)
    return results


if __name__ == "__main__":
    results = run_batch_backtest()
    print("\n=== Batch Backtest Results ===")
    for r in results:
        s = r.session.summary()
        print(
            f"{r.name:>16} | Return {s['return_pct']:.2%} | "
            f"Trades {s['total_trades']} | Win {s['win_rate']:.2%} | "
            f"MaxDD {s['max_drawdown_pct']:.2%}"
        )
