import pandas as pd

from indicators.indicator_engine import add_indicators
from strategy.base_strategy import BaseStrategy
from strategy.regime import MarketRegime, detect_regime
from strategy.signal import TradeSignal


class TrendBreakoutStrategy(BaseStrategy):
    """
    Trend breakout strategy:
    - only trade in clear up/down trend
    - break above/below recent range
    """

    def __init__(self, symbol: str = "BTC/USDC", lookback: int = 50, atr_mult: float = 1.0):
        super().__init__(symbol)
        self.lookback = lookback
        self.atr_mult = atr_mult

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if df is None or df.empty or len(df) < self.lookback + 2:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Insufficient data")

        if "ema21" not in df.columns:
            df = add_indicators(df.copy())

        last = df.iloc[-1]
        prev = df.iloc[-2]
        if pd.isna(last.get("atr14")) or pd.isna(last.get("close")):
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Indicators not ready")

        regime = detect_regime(df)
        atr = float(last["atr14"])
        close = float(last["close"])
        recent = df.tail(self.lookback)
        range_high = float(recent["high"].max())
        range_low = float(recent["low"].min())

        if regime == MarketRegime.UPTREND and close > range_high:
            entry = close
            stop = entry - (self.atr_mult * atr)
            tp = entry + (1.5 * self.atr_mult * atr)
            return TradeSignal(
                symbol=self.symbol,
                side="LONG",
                entry_price=entry,
                stop_loss=stop,
                take_profit=tp,
                confidence=0.6,
                reason="Uptrend breakout"
            )

        if regime == MarketRegime.DOWNTREND and close < range_low:
            entry = close
            stop = entry + (self.atr_mult * atr)
            tp = entry - (1.5 * self.atr_mult * atr)
            return TradeSignal(
                symbol=self.symbol,
                side="SHORT",
                entry_price=entry,
                stop_loss=stop,
                take_profit=tp,
                confidence=0.6,
                reason="Downtrend breakdown"
            )

        return TradeSignal(symbol=self.symbol, side="FLAT", reason="No breakout")


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy:
    - trade against extreme RSI when price is stretched from EMA21
    """

    def __init__(
        self,
        symbol: str = "BTC/USDC",
        atr_mult: float = 1.0,
        rsi_low: float = 30.0,
        rsi_high: float = 70.0,
        min_stretch: float = 0.005
    ):
        super().__init__(symbol)
        self.atr_mult = atr_mult
        self.rsi_low = rsi_low
        self.rsi_high = rsi_high
        self.min_stretch = min_stretch

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if df is None or df.empty or len(df) < 50:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Insufficient data")

        if "rsi14" not in df.columns:
            df = add_indicators(df.copy())

        last = df.iloc[-1]
        if pd.isna(last.get("atr14")) or pd.isna(last.get("rsi14")):
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Indicators not ready")

        rsi = float(last["rsi14"])
        close = float(last["close"])
        ema21 = float(last["ema21"])
        atr = float(last["atr14"])

        stretch = abs(close - ema21) / close
        if rsi < self.rsi_low and stretch > self.min_stretch:
            entry = close
            stop = entry - (self.atr_mult * atr)
            tp = entry + (1.0 * self.atr_mult * atr)
            return TradeSignal(
                symbol=self.symbol,
                side="LONG",
                entry_price=entry,
                stop_loss=stop,
                take_profit=tp,
                confidence=0.4,
                reason="Mean reversion long"
            )

        if rsi > self.rsi_high and stretch > self.min_stretch:
            entry = close
            stop = entry + (self.atr_mult * atr)
            tp = entry - (1.0 * self.atr_mult * atr)
            return TradeSignal(
                symbol=self.symbol,
                side="SHORT",
                entry_price=entry,
                stop_loss=stop,
                take_profit=tp,
                confidence=0.4,
                reason="Mean reversion short"
            )

        return TradeSignal(symbol=self.symbol, side="FLAT", reason="No mean reversion")


class MomentumCrossoverStrategy(BaseStrategy):
    """
    Momentum crossover strategy:
    - trade EMA21/EMA50 cross with SMA200 trend filter
    """

    def __init__(self, symbol: str = "BTC/USDC", atr_mult: float = 1.0):
        super().__init__(symbol)
        self.atr_mult = atr_mult

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if df is None or df.empty or len(df) < 200:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Insufficient data")

        if "ema21" not in df.columns:
            df = add_indicators(df.copy())

        last = df.iloc[-1]
        prev = df.iloc[-2]
        if pd.isna(last.get("atr14")):
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Indicators not ready")

        ema21 = float(last["ema21"])
        ema50 = float(last["ema50"])
        ema21_prev = float(prev["ema21"])
        ema50_prev = float(prev["ema50"])
        close = float(last["close"])
        sma200 = float(last["sma200"])
        atr = float(last["atr14"])

        bullish_cross = ema21 > ema50 and ema21_prev <= ema50_prev
        bearish_cross = ema21 < ema50 and ema21_prev >= ema50_prev

        if bullish_cross and close > sma200:
            entry = close
            stop = entry - (self.atr_mult * atr)
            tp = entry + (1.5 * self.atr_mult * atr)
            return TradeSignal(
                symbol=self.symbol,
                side="LONG",
                entry_price=entry,
                stop_loss=stop,
                take_profit=tp,
                confidence=0.5,
                reason="Bullish EMA crossover"
            )

        if bearish_cross and close < sma200:
            entry = close
            stop = entry + (self.atr_mult * atr)
            tp = entry - (1.5 * self.atr_mult * atr)
            return TradeSignal(
                symbol=self.symbol,
                side="SHORT",
                entry_price=entry,
                stop_loss=stop,
                take_profit=tp,
                confidence=0.5,
                reason="Bearish EMA crossover"
            )

        return TradeSignal(symbol=self.symbol, side="FLAT", reason="No crossover")
