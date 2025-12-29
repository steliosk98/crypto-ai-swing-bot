from dataclasses import dataclass
from typing import Optional


@dataclass
class TradeSignal:
    """
    Standardized trade signal produced by strategies.

    side:
        "LONG"  -> open a long
        "SHORT" -> open a short
        "FLAT"  -> no trade / close positions
    """
    symbol: str
    side: str                 # "LONG", "SHORT", "FLAT"
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = 0.0   # 0.0 - 1.0
    reason: str = ""          # human-readable explanation

    def is_actionable(self) -> bool:
        """Return True if this signal suggests opening a position."""
        return self.side in ("LONG", "SHORT") and self.entry_price is not None