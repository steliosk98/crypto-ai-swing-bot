from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional

import pandas as pd

from backtesting.session_state import SessionState, TradeRecord
from data.historical_data import load_historical_ohlcv
from execution.paper_broker import PaperBroker
from filters.trade_limiter import TradeLimiter
from indicators.indicator_engine import add_indicators
from strategy.regime import MarketRegime
from strategy.variants import MeanReversionStrategy
from utils.config import Config
from utils.logger import log


@dataclass(frozen=True)
class SweepConfig:
    rsi_low: float
    rsi_high: float
    atr_mult: float
    min_stretch: float
    min_stretch_atr_mult: Optional[float]
    allowed_regimes: Optional[Iterable[MarketRegime]]
    allowed_utc_hours: Optional[Iterable[int]]


def _run_window(
    candles: pd.DataFrame,
    config: SweepConfig,
    trade_start: pd.Timestamp,
) -> SessionState:
    strategy = MeanReversionStrategy(
        symbol=Config.LIVE_SYMBOL,
        atr_mult=config.atr_mult,
        rsi_low=config.rsi_low,
        rsi_high=config.rsi_high,
        min_stretch=config.min_stretch,
        min_stretch_atr_mult=config.min_stretch_atr_mult,
        allowed_regimes=config.allowed_regimes,
        allowed_utc_hours=config.allowed_utc_hours,
    )
    broker = PaperBroker(fee_rate=0.0005)
    limiter = TradeLimiter(
        max_trades_per_day=Config.MAX_TRADES_PER_DAY,
        max_daily_loss_pct=Config.MAX_DAILY_LOSS_PCT,
        max_daily_profit_pct=Config.MAX_DAILY_PROFIT_PCT,
        log_resets=False,
        log_blocks=False,
    )
    session = SessionState()
    active_signal = None

    for i in range(300, len(candles)):
        window = candles.iloc[:i]
        last = window.iloc[-1]
        last_ts = last["timestamp"]
        if last_ts < trade_start:
            continue

        signal = strategy.generate_signal(window)

        if not broker.has_open_position() and limiter.can_trade(now_utc=last_ts) and signal.is_actionable():
            if broker.open_position(
                symbol=Config.LIVE_SYMBOL,
                side=signal.side,
                entry=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
            ):
                limiter.record_trade_opened()
                active_signal = signal

        pnl_pct = broker.check_and_close(
            high=last["high"],
            low=last["low"],
            close=last["close"],
            trade_limiter=limiter,
        )

        if pnl_pct is not None and active_signal:
            exit_price = active_signal.take_profit if pnl_pct > 0 else active_signal.stop_loss
            session.record_trade(
                TradeRecord(
                    symbol=Config.LIVE_SYMBOL,
                    side=active_signal.side,
                    entry_price=active_signal.entry_price,
                    exit_price=exit_price,
                    pnl_pct=pnl_pct,
                    reason=active_signal.reason,
                    timestamp=last_ts,
                )
            )
            active_signal = None

    return session


def _year_windows(start_year: int, end_year: int, end: str) -> list[tuple[int, pd.Timestamp, pd.Timestamp]]:
    windows = []
    for year in range(start_year, end_year + 1):
        year_start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        year_end = pd.Timestamp(f"{year}-12-31", tz="UTC")
        if year == end_year:
            year_end = pd.Timestamp(end, tz="UTC")
        windows.append((year, year_start, year_end))
    return windows


def _build_configs() -> Iterable[SweepConfig]:
    rsi_pairs = [(28.0, 72.0), (32.0, 68.0)]
    atr_mults = [0.9, 1.0]
    stretch_vals = [0.004, 0.006]
    stretch_atr = [None, 0.75]
    regimes = [
        None,
        (MarketRegime.SIDEWAYS,),
    ]
    hours = [None]

    for rsi_low, rsi_high in rsi_pairs:
        for atr_mult in atr_mults:
            for min_stretch in stretch_vals:
                for min_stretch_atr_mult in stretch_atr:
                    for allowed_regimes in regimes:
                        for allowed_utc_hours in hours:
                            yield SweepConfig(
                                rsi_low=rsi_low,
                                rsi_high=rsi_high,
                                atr_mult=atr_mult,
                                min_stretch=min_stretch,
                                min_stretch_atr_mult=min_stretch_atr_mult,
                                allowed_regimes=allowed_regimes,
                                allowed_utc_hours=allowed_utc_hours,
                            )


def run_consistency_sweep(start: str, end: str) -> pd.DataFrame:
    log.remove()
    log.add(lambda msg: print(msg, end=""), level="WARNING")

    candles = load_historical_ohlcv("BTC/USD", "1h", start, end)
    if candles.empty:
        raise RuntimeError("Local BTC/USD data not found for sweep.")

    candles = add_indicators(candles)
    results = []

    start_year = pd.Timestamp(start, tz="UTC").year
    end_year = pd.Timestamp(end, tz="UTC").year
    windows = _year_windows(start_year, end_year, end)

    for config in _build_configs():
        yearly_returns = []
        for year, year_start, year_end in windows:
            warmup_start = year_start - pd.Timedelta(hours=300)
            year_slice = candles[(candles["timestamp"] >= warmup_start) & (candles["timestamp"] <= year_end)]
            if year_slice.empty:
                continue
            session = _run_window(year_slice, config, year_start)
            yearly_returns.append(session.summary()["return_pct"])

        if not yearly_returns:
            continue

        results.append({
            "median_yearly_return": median(yearly_returns),
            "worst_year_return": min(yearly_returns),
            "best_year_return": max(yearly_returns),
            "avg_yearly_return": sum(yearly_returns) / len(yearly_returns),
            "rsi_low": config.rsi_low,
            "rsi_high": config.rsi_high,
            "atr_mult": config.atr_mult,
            "min_stretch": config.min_stretch,
            "min_stretch_atr_mult": config.min_stretch_atr_mult or 0.0,
            "allowed_regimes": "all" if config.allowed_regimes is None else "+".join(r.name for r in config.allowed_regimes),
            "allowed_utc_hours": "all" if config.allowed_utc_hours is None else "US",
        })

    df = pd.DataFrame(results).sort_values("median_yearly_return", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    start = "2018-05-15"
    end = "2025-12-01"
    results_df = run_consistency_sweep(start, end)
    print("\n=== Consistency Sweep (Top 10 by Median Yearly Return) ===")
    print(
        results_df[
            [
                "median_yearly_return",
                "worst_year_return",
                "avg_yearly_return",
                "rsi_low",
                "rsi_high",
                "atr_mult",
                "min_stretch",
                "min_stretch_atr_mult",
                "allowed_regimes",
                "allowed_utc_hours",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )
