from strategy.signal import TradeSignal
from .prompt_builder import PromptBuilder
from utils.logger import log


class AIFilter:
    """
    Skeleton for AI-assisted validation of strategy signals.
    Later: use OpenAI API to evaluate quality.
    """

    def __init__(self, model_name: str = "gpt-4.1-mini"):
        self.model_name = model_name

    def evaluate_signal(self, signal: TradeSignal, candles) -> TradeSignal:
        """
        Prepare prompt, (later) call model, parse response,
        and return an updated/filtered TradeSignal.
        """

        if not signal.is_actionable():
            return signal  # No need to evaluate flats or missing signals

        prompt = PromptBuilder.build_trade_evaluation_prompt(signal, candles)
        log.info(f"AI prompt built for evaluation:\n{prompt[:200]}...")

        # ---- Placeholder for real model call ----
        # future:
        #   raw_response = openai.chat.completions.create(...)
        #   parsed = json.loads(raw_response)
        # for now, simulate "MARGINAL"
        mock_decision = {
            "quality": "MARGINAL",
            "confidence": 0.5,
            "note": "AI layer placeholder — no evaluation yet"
        }

        # ---- Modify signal based on quality ----
        quality = mock_decision["quality"]
        conf = mock_decision["confidence"]

        if quality == "BAD":
            return TradeSignal(
                symbol=signal.symbol,
                side="FLAT",
                reason=f"AI rejected: {mock_decision['note']}"
            )

        # Otherwise, adjust confidence and pass through
        signal.confidence *= conf
        signal.reason += f" | AI quality={quality}"
        return signal