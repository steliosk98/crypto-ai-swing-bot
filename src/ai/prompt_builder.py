from strategy.signal import TradeSignal
import pandas as pd


class PromptBuilder:
    """
    Builds structured prompts for the AI model to evaluate trade signals.
    """

    @staticmethod
    def build_trade_evaluation_prompt(
        signal: TradeSignal,
        candles: pd.DataFrame
    ) -> str:
        """
        Create a textual summary of market state + strategy signal
        for the AI to reason about.
        """

        if candles.empty or not signal:
            return "No candle data or signal provided."

        last = candles.iloc[-1]

        prompt = f"""
You are an assistant that evaluates crypto trade setups.
You do NOT predict price directly.
You rate the quality of a trade setup based on market context.

Current market summary:
- Symbol: {signal.symbol}
- Last close price: {last['close']:.2f}
- RSI14: {last.get('rsi14', 'NA')}
- SMA50: {last.get('sma50', 'NA')}
- SMA200: {last.get('sma200', 'NA')}
- EMA21: {last.get('ema21', 'NA')}
- EMA50: {last.get('ema50', 'NA')}
- MACD line: {last.get('macd_line', 'NA')}
- MACD signal: {last.get('macd_signal', 'NA')}
- Strategy reason: {signal.reason}
- Strategy signal side: {signal.side}

Your task:
1. Evaluate whether this setup looks clean or noisy.
2. Do NOT make predictions.
3. Respond ONLY with:
   - quality: GOOD / MARGINAL / BAD
   - confidence: a number 0-1
   - note: short reasoning for logging

Respond in JSON like:
{{
  "quality": "GOOD|MARGINAL|BAD",
  "confidence": 0.0,
  "note": "short reasoning"
}}
"""
        return prompt.strip()