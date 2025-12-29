from dataclasses import dataclass
from typing import List, Optional
import pandas as pd


@dataclass
class TradeRecord:
    """
    Tracks a single completed trade.
    pnl_pct is expressed as decimal:
        +0.01 = +1%
        -0.005 = -0.5%
    """
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    pnl_pct: float
    reason: str
    timestamp: pd.Timestamp


class SessionState:
    """
    Tracks the overall results of a backtesting session:
        - equity curve
        - closed trades
        - max drawdown
        - profitability statistics

    Initial equity is normalized to 1.0 (100%),
    so growth is expressed as percentage return.
    """

    def __init__(self, initial_equity: float = 1.0):
        self.initial_equity = initial_equity
        self.equity = initial_equity
        self.equity_curve: List[float] = [initial_equity]
        self.timestamps: List[pd.Timestamp] = []
        self.trades: List[TradeRecord] = []

    # ---------------------------
    # Equity & PnL Tracking
    # ---------------------------

    def record_trade(self, trade: TradeRecord):
        """Add a closed trade and update equity."""
        self.trades.append(trade)
        self.equity *= (1 + trade.pnl_pct)
        self.equity_curve.append(self.equity)
        self.timestamps.append(trade.timestamp)

    def current_drawdown(self) -> float:
        """
        Calculates current drawdown as:
            (current equity - max equity seen) / max equity
        returns negative % drawdown.
        """
        max_equity = max(self.equity_curve)
        return (self.equity - max_equity) / max_equity

    def max_drawdown(self) -> float:
        """
        Max drawdown in session.
        """
        dd = [ (e - max(self.equity_curve[:i+1])) / max(self.equity_curve[:i+1])
               for i, e in enumerate(self.equity_curve) ]
        return min(dd) if dd else 0.0

    # ---------------------------
    # Stats & Results
    # ---------------------------

    def summary(self) -> dict:
        wins = sum(1 for t in self.trades if t.pnl_pct > 0)
        losses = sum(1 for t in self.trades if t.pnl_pct < 0)
        total = len(self.trades)

        avg_win = (sum(t.pnl_pct for t in self.trades if t.pnl_pct > 0) / wins) if wins > 0 else 0
        avg_loss = (sum(t.pnl_pct for t in self.trades if t.pnl_pct < 0) / losses) if losses > 0 else 0

        win_rate = wins / total if total > 0 else 0

        # expectancy per trade (in R terms later)
        expectancy = ((win_rate * avg_win) + ((1 - win_rate) * avg_loss)) if total > 0 else 0

        return {
            "initial_equity": self.initial_equity,
            "final_equity": self.equity,
            "return_pct": (self.equity / self.initial_equity) - 1,
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_win_pct": avg_win,
            "avg_loss_pct": avg_loss,
            "expectancy_pct": expectancy,
            "max_drawdown_pct": self.max_drawdown()
        }

    def print_summary(self):
        s = self.summary()
        print("\n=== Backtest Summary ===")
        print(f"Initial Equity     : {s['initial_equity']:.4f}")
        print(f"Final Equity       : {s['final_equity']:.4f}")
        print(f"Return %           : {s['return_pct']:.2%}")
        print(f"Total Trades       : {s['total_trades']}")
        print(f"Wins / Losses      : {s['wins']} / {s['losses']}")
        print(f"Win Rate           : {s['win_rate']:.2%}")
        print(f"Avg Win %          : {s['avg_win_pct']:.2%}")
        print(f"Avg Loss %         : {s['avg_loss_pct']:.2%}")
        print(f"Expectancy %       : {s['expectancy_pct']:.2%}")
        print(f"Max Drawdown %     : {s['max_drawdown_pct']:.2%}")
        print("========================\n")