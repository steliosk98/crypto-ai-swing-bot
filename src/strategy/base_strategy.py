from abc import ABC, abstractmethod
import pandas as pd
from .signal import TradeSignal


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol

    @abstractmethod
    def generate_signal(self, candles: pd.DataFrame) -> TradeSignal:
        """
        Given a DataFrame of candles + indicators,
        return a TradeSignal (LONG / SHORT / FLAT).
        """
        raise NotImplementedError