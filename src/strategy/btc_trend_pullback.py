import pandas as pd

from indicators.indicator_engine import add_indicators
from strategy.base_strategy import BaseStrategy
from strategy.regime import MarketRegime, detect_regime
from strategy.signal import TradeSignal


class BTCTrendPullbackStrategy(BaseStrategy):
    """
    Pullback & breakout strategy for BTC/USDC futures.
    Supports LONG, SHORT, and FLAT depending on market regime.
    """

    def __init__(self, symbol: str = "BTC/USDC"):
        super().__init__(symbol)

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if df is None or df.empty or len(df) < 2:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Insufficient data")

        df = add_indicators(df.copy())
        regime = detect_regime(df)
        last = df.iloc[-1]
        prev = df.iloc[-2]

        required = ["ema21", "sma200", "close"]
        if any(pd.isna(last.get(key)) or pd.isna(prev.get(key)) for key in required):
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Indicators not ready")

        # ===== Uptrend =====
        if regime == MarketRegime.UPTREND:
            if last["close"] > last["ema21"] and prev["close"] < prev["ema21"]:
                entry = last["close"]
                stop = entry * 0.99
                tp = entry * 1.02
                return TradeSignal(
                    symbol=self.symbol,
                    side="LONG",
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit=tp,
                    confidence=0.6,
                    reason="Uptrend pullback long"
                )

        # ===== Downtrend =====
        if regime == MarketRegime.DOWNTREND:
            if last["close"] < last["ema21"] and prev["close"] > prev["ema21"]:
                entry = last["close"]
                stop = entry * 1.01
                tp = entry * 0.98
                return TradeSignal(
                    symbol=self.symbol,
                    side="SHORT",
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit=tp,
                    confidence=0.6,
                    reason="Downtrend pullback short"
                )

        # ===== Sideways =====
        if regime == MarketRegime.SIDEWAYS:
            if last["close"] > last["sma200"]:
                entry = last["close"]
                stop = entry * 0.99
                tp = entry * 1.02
                return TradeSignal(
                    symbol=self.symbol,
                    side="LONG",
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit=tp,
                    confidence=0.5,
                    reason="Sideways breakout long"
                )
            else:
                entry = last["close"]
                stop = entry * 1.01
                tp = entry * 0.98
                return TradeSignal(
                    symbol=self.symbol,
                    side="SHORT",
                    entry_price=entry,
                    stop_loss=stop,
                    take_profit=tp,
                    confidence=0.5,
                    reason="Sideways breakdown short"
                )

        return TradeSignal(symbol=self.symbol, side="FLAT", reason="No setup")
