from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import ccxt
import pandas as pd

from backtesting.session_state import SessionState, TradeRecord
from execution.paper_broker import PaperBroker
from filters.trade_limiter import TradeLimiter
from indicators.indicator_engine import add_indicators
from strategy.variants import MeanReversionStrategy
from utils.config import Config
from utils.logger import log


CACHE_PATH = Path("data/binance_BTCUSDC_1h.csv")


@dataclass(frozen=True)
class SweepConfig:
    rsi_low: float
    rsi_high: float
    atr_mult: float
    min_stretch: float


def _fetch_futures_ohlcv(symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
    exchange = ccxt.binanceusdm({
        "enableRateLimit": True,
        "options": {"defaultType": "future"},
    })

    start_ts = int(pd.Timestamp(start).timestamp() * 1000)
    end_ts = int(pd.Timestamp(end).timestamp() * 1000)
    fetch_ts = start_ts
    rows = []

    while fetch_ts < end_ts:
        batch = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=fetch_ts,
            limit=1500,
        )
        if not batch:
            break
        rows.extend(batch)
        fetch_ts = batch[-1][0] + 1

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df[df["timestamp"] <= pd.Timestamp(end, tz="UTC")]
    return df.reset_index(drop=True)


def _ensure_cache(symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
    if CACHE_PATH.exists():
        df = pd.read_csv(CACHE_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    else:
        df = pd.DataFrame()

    if df.empty or df["timestamp"].min() > pd.Timestamp(start, tz="UTC") or df["timestamp"].max() < pd.Timestamp(end, tz="UTC"):
        log.info("Fetching futures data from Binance to local cache...")
        df = _fetch_futures_ohlcv(symbol, timeframe, start, end)
        if df.empty:
            return df
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(CACHE_PATH, index=False)
        log.info(f"Saved futures cache to {CACHE_PATH}.")

    start_dt = pd.Timestamp(start, tz="UTC")
    end_dt = pd.Timestamp(end, tz="UTC")
    df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]
    return df.reset_index(drop=True)


def _run_backtest(candles: pd.DataFrame, config: SweepConfig) -> dict:
    strategy = MeanReversionStrategy(
        symbol=Config.LIVE_SYMBOL,
        atr_mult=config.atr_mult,
        rsi_low=config.rsi_low,
        rsi_high=config.rsi_high,
        min_stretch=config.min_stretch,
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
        signal = strategy.generate_signal(window)

        if not broker.has_open_position() and limiter.can_trade(now_utc=last["timestamp"]) and signal.is_actionable():
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
                    timestamp=last["timestamp"],
                )
            )
            active_signal = None

    summary = session.summary()
    summary["rsi_low"] = config.rsi_low
    summary["rsi_high"] = config.rsi_high
    summary["atr_mult"] = config.atr_mult
    summary["min_stretch"] = config.min_stretch
    return summary


def _build_sweep_configs() -> Iterable[SweepConfig]:
    rsi_pairs = [(28.0, 72.0), (30.0, 70.0), (35.0, 65.0)]
    atr_mults = [0.8, 1.0, 1.2]
    stretches = [0.004, 0.006]

    for rsi_low, rsi_high in rsi_pairs:
        for atr_mult in atr_mults:
            for min_stretch in stretches:
                yield SweepConfig(
                    rsi_low=rsi_low,
                    rsi_high=rsi_high,
                    atr_mult=atr_mult,
                    min_stretch=min_stretch,
                )


def run_sweep(start: str, end: str) -> pd.DataFrame:
    log.remove()
    log.add(lambda msg: print(msg, end=""), level="WARNING")

    candles = _ensure_cache(Config.LIVE_SYMBOL, Config.LIVE_TIMEFRAME, start, end)
    if candles.empty:
        raise RuntimeError("No candle data available for sweep.")

    candles = add_indicators(candles)
    results = []
    for config in _build_sweep_configs():
        summary = _run_backtest(candles, config)
        results.append(summary)

    df = pd.DataFrame(results).sort_values("return_pct", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    start = "2023-01-01"
    end = "2025-12-01"
    results_df = run_sweep(start, end)
    print("\n=== Sweep Results (Top 10 by Return) ===")
    print(
        results_df[
            [
                "return_pct",
                "max_drawdown_pct",
                "total_trades",
                "win_rate",
                "rsi_low",
                "rsi_high",
                "atr_mult",
                "min_stretch",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )
