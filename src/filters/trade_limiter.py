from datetime import date
from utils.logger import log


class TradeLimiter:
    """
    Enforces daily trade discipline:
    - max trades per day
    - daily max loss percentage
    - daily max profit percentage

    The limiter resets automatically at the start of each new UTC day.
    """

    def __init__(
        self,
        max_trades_per_day: int = 3,
        max_daily_loss_pct: float = 0.02,     # -2% loss cap
        max_daily_profit_pct: float = 0.015   # +1.5% profit cap
    ):
        self.max_trades_per_day = max_trades_per_day
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_daily_profit_pct = max_daily_profit_pct

        self.reset_day = date.today()
        self.trades_today = 0
        self.daily_pnl_pct = 0.0  # track cumulative % PnL

    def _reset_if_new_day(self):
        today = date.today()
        if today != self.reset_day:
            log.info("New day detected — resetting trade counters & PnL.")
            self.reset_day = today
            self.trades_today = 0
            self.daily_pnl_pct = 0.0

    def can_trade(self) -> bool:
        """
        True if we are allowed to open a new trade today.
        """
        self._reset_if_new_day()

        # ---- Trade count limit ----
        if self.trades_today >= self.max_trades_per_day:
            log.warning(
                f"Trade limit reached: {self.trades_today}/{self.max_trades_per_day}. "
                "Blocking new trades."
            )
            return False

        # ---- Loss limit ----
        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            log.warning(
                f"Daily loss cap reached ({self.daily_pnl_pct:.2%}). "
                "Blocking new trades."
            )
            return False

        # ---- Profit limit ----
        if self.daily_pnl_pct >= self.max_daily_profit_pct:
            log.info(
                f"Daily profit target reached ({self.daily_pnl_pct:.2%}). "
                "Locking in gains — blocking new trades."
            )
            return False

        return True

    def record_trade_opened(self):
        self.trades_today += 1
        log.info(
            f"Trade opened — now {self.trades_today}/{self.max_trades_per_day} "
            f"and daily PnL {self.daily_pnl_pct:.2%}"
        )

    def record_trade_result(self, pnl_pct: float):
        """
        Record profit or loss after closing a trade.
        pnl_pct is expressed as a decimal:
            +0.01 = +1%
            -0.005 = -0.5%
        """
        self.daily_pnl_pct += pnl_pct
        log.info(
            f"Trade result recorded: {pnl_pct:.2%}. "
            f"Daily PnL now {self.daily_pnl_pct:.2%}"
        )