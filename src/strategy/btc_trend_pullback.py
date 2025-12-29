import pandas as pd
from typing import Optional

from indicators.indicator_engine import add_indicators
from .base_strategy import BaseStrategy
from .signal import TradeSignal


class BTCTrendPullbackStrategy(BaseStrategy):
    """
    Simple trend-following pullback strategy for BTC/USDT on 1h timeframe.

    - Defines trend using SMA200 + EMA21/EMA50
    - Looks for pullbacks toward EMA21 in an uptrend
    - LONG-only for now (no shorts yet, to keep risk profile simpler)
    """

    def __init__(self, symbol: str = "BTC/USDT"):
        super().__init__(symbol=symbol)

    def generate_signal(self, candles: pd.DataFrame) -> TradeSignal:
        if candles is None or candles.empty:
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="No data")

        # Ensure indicators exist
        candles = add_indicators(candles.copy())

        last = candles.iloc[-1]

        price = float(last["close"])
        sma200 = last.get("sma200")
        ema21 = last.get("ema21")
        ema50 = last.get("ema50")
        rsi14 = last.get("rsi14")

        # If indicators are NaN (too few candles), skip
        if pd.isna(sma200) or pd.isna(ema21) or pd.isna(ema50) or pd.isna(rsi14):
            return TradeSignal(symbol=self.symbol, side="FLAT", reason="Not enough data for indicators")

        # ---- 1) Define uptrend ----
        in_uptrend = price > sma200 and ema21 > ema50

        if not in_uptrend:
            return TradeSignal(
                symbol=self.symbol,
                side="FLAT",
                reason="No clean uptrend (flat/short conditions ignored for now)"
            )

        # ---- 2) Look for pullback toward EMA21 ----
        # Conditions (simple, tweakable later):
        # - Price close to EMA21 (within 0.5% for example)
        # - RSI not overbought (below 60)

        distance_to_ema21 = abs(price - ema21) / ema21

        near_ema21 = distance_to_ema21 < 0.005  # 0.5%
        rsi_ok = rsi14 < 60

        if near_ema21 and rsi_ok:
            # Basic RR assumptions (tweak later, or move to risk module)
            stop_loss = float(ema50)  # below EMA50 as a safety net
            # Example take profit: 2x risk (very simple placeholder)
            risk_per_unit = price - stop_loss if price > stop_loss else price * 0.01
            take_profit = price + 2 * risk_per_unit

            return TradeSignal(
                symbol=self.symbol,
                side="LONG",
                entry_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=0.6,  # base confidence, AI layer will adjust later
                reason="Uptrend + pullback to EMA21 with cooled RSI"
            )

        # No setup
        return TradeSignal(
            symbol=self.symbol,
            side="FLAT",
            reason="No suitable pullback setup"
        )