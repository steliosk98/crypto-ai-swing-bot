import pandas as pd

from indicators.indicator_engine import add_indicators
from .base_strategy import BaseStrategy
from .signal import TradeSignal
from strategy.regime import MarketRegime, detect_regime
from strategy.sideways import detect_range


class BTCTrendPullbackStrategy(BaseStrategy):
    """
    Trend-following pullback strategy for BTC/USDT on the 1h timeframe.

    Behavior by regime:

    UPTREND:
        - price > sma200
        - ema21 > ema50
        - look for pullback toward ema21
        - RSI cooled below 60
        → LONG setups

    DOWNTREND:
        - price < sma200
        - ema21 < ema50
        - look for rally up toward ema21
        - RSI above 40 to avoid bottom-chasing
        → SHORT setups

    SIDEWAYS:
        - low directional conviction
        - WAIT through chop
        - trigger breakout setups only when price exits range
        → LONG if break up, SHORT if break down
    """

    def __init__(self, symbol: str = "BTC/USDT"):
        super().__init__(symbol=symbol)

    def generate_signal(self, candles: pd.DataFrame) -> TradeSignal:
        if candles is None or candles.empty:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="No data provided")

        # Compute indicators
        candles = add_indicators(candles.copy())
        last = candles.iloc[-1]

        price = float(last["close"])
        sma200 = last.get("sma200")
        ema21 = last.get("ema21")
        ema50 = last.get("ema50")
        rsi14 = last.get("rsi14")

        # If indicator data is missing or NaN, skip
        if any(pd.isna(v) for v in [sma200, ema21, ema50, rsi14]):
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Not enough indicator history")

        # ---- Determine regime ----
        regime = detect_regime(candles)

        # Common metric — "near" pullback value
        distance_to_ema21 = abs(price - ema21) / ema21
        near_ema21 = distance_to_ema21 < 0.005  # within 0.5% of EMA21

        # ==============================
        # UPTREND → LONG on pullback
        # ==============================
        if regime == MarketRegime.UPTREND:
            if near_ema21 and rsi14 < 60:
                stop_loss = float(ema50)
                risk = max(price - stop_loss, price * 0.01)
                take_profit = price + 2 * risk

                return TradeSignal(
                    symbol=self.symbol,
                    side="LONG",
                    entry_price=price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.6,  # base confidence; AI filter may adjust
                    reason="Uptrend pullback: long opportunity"
                )

            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Uptrend: waiting for clean pullback")

        # ==============================
        # DOWNTREND → SHORT on rally
        # ==============================
        if regime == MarketRegime.DOWNTREND:
            if near_ema21 and rsi14 > 40:
                stop_loss = float(ema50)
                risk = max(stop_loss - price, price * 0.01)
                take_profit = price - 2 * risk

                return TradeSignal(
                    symbol=self.symbol,
                    side="SHORT",
                    entry_price=price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.6,
                    reason="Downtrend pullback: short opportunity"
                )

            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Downtrend: waiting for clean rally")

        # ==============================
        # SIDEWAYS → breakout mode only
        # ==============================
        if regime == MarketRegime.SIDEWAYS:
            range_low, range_high = detect_range(candles)

            # Breakout LONG
            if price > range_high and rsi14 < 70:
                stop_loss = float(ema50)
                risk = max(price - stop_loss, price * 0.01)
                take_profit = price + 2 * risk

                return TradeSignal(
                    symbol=self.symbol,
                    side="LONG",
                    entry_price=price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.5,
                    reason="Sideways breakout to upside: long entry"
                )

            # Breakout SHORT
            if price < range_low and rsi14 > 30:
                stop_loss = float(ema50)
                risk = max(stop_loss - price, price * 0.01)
                take_profit = price - 2 * risk

                return TradeSignal(
                    symbol=self.symbol,
                    side="SHORT",
                    entry_price=price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=0.5,
                    reason="Sideways breakout to downside: short entry"
                )

            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Sideways: waiting for definitive breakout")

        # ==============================
        # Fallback
        # ==============================
        return TradeSignal(symbol=self.symbol, side="FLAT", reason="Regime not clear — staying flat")