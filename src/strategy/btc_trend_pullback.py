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
    ATR_PERIOD = 14
    MIN_ATR_PCT = 0.002
    MAX_ATR_PCT = 0.03
    STOP_ATR_MULT = 1.0
    TARGET_ATR_MULT = 1.5

    def __init__(self, symbol: str = "BTC/USDC"):
        super().__init__(symbol)

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if df is None or df.empty or len(df) < 2:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Insufficient data")

        if "ema21" not in df.columns:
            df = add_indicators(df.copy())
        regime = detect_regime(df)
        last = df.iloc[-1]
        prev = df.iloc[-2]

        required = ["ema21", "ema50", "sma200", "close", "atr14"]
        if any(pd.isna(last.get(key)) or pd.isna(prev.get(key)) for key in required):
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Indicators not ready")

        atr = float(last["atr14"])
        atr_pct = atr / float(last["close"]) if last["close"] else 0.0
        if atr_pct < self.MIN_ATR_PCT or atr_pct > self.MAX_ATR_PCT:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Volatility out of range")

        ema21 = float(last["ema21"])
        ema50 = float(last["ema50"])
        ema21_prev = float(prev["ema21"])
        ema21_slope = ema21 - ema21_prev
        ema_spread_pct = abs(ema21 - ema50) / float(last["close"])
        if ema_spread_pct < 0.002:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Trend too weak")

        # ===== Uptrend =====
        if regime == MarketRegime.UPTREND:
            if (
                last["close"] > last["ema21"]
                and prev["close"] < prev["ema21"]
                and ema21_slope > 0
                and last["close"] > prev["close"]
            ):
                entry = float(last["close"])
                stop = entry - (self.STOP_ATR_MULT * atr)
                tp = entry + (self.TARGET_ATR_MULT * atr)
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
            if (
                last["close"] < last["ema21"]
                and prev["close"] > prev["ema21"]
                and ema21_slope < 0
                and last["close"] < prev["close"]
            ):
                entry = float(last["close"])
                stop = entry + (self.STOP_ATR_MULT * atr)
                tp = entry - (self.TARGET_ATR_MULT * atr)
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
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Sideways regime")

        return TradeSignal(symbol=self.symbol, side="FLAT", reason="No setup")
