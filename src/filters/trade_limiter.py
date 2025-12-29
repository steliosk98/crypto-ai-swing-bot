from datetime import datetime, timedelta, time
import pytz
from utils.logger import log

"""
TradeLimiter with US Market Open Reset

Resets once per day at:
    9:30 AM Eastern Time (NYSE Open)

Behavior:
- Tracks trades & daily PnL
- Blocks new trades after limits hit
- Resets counters at next US market open
"""

class TradeLimiter:
    def __init__(
        self,
        max_trades_per_day: int = 3,
        max_daily_loss_pct: float = 0.02,    # -2% daily max loss
        max_daily_profit_pct: float = 0.015  # +1.5% daily profit target
    ):
        self.max_trades_per_day = max_trades_per_day
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_daily_profit_pct = max_daily_profit_pct
        
        self.trades_today = 0
        self.daily_pnl_pct = 0.0
        
        # next reset timestamp (first initialization)
        self.next_reset_ts = self._calculate_next_us_open()

    # -------------------------------------------------------
    # Time / Reset Management
    # -------------------------------------------------------

    @staticmethod
    def _calculate_next_us_open(now_utc: datetime = None) -> datetime:
        """
        Returns the next occurrence of 9:30 AM ET in UTC.
        Automatically handles EST/EDT via pytz.
        """
        eastern = pytz.timezone("America/New_York")
        utc = pytz.UTC
        now_utc = now_utc or datetime.now(utc)

        # convert now to Eastern
        now_est = now_utc.astimezone(eastern)
        us_open_today_est = now_est.replace(
            hour=9, minute=30, second=0, microsecond=0
        )

        # If open time already passed, move to next day
        if now_est >= us_open_today_est:
            us_open_today_est += timedelta(days=1)

        # Convert back to UTC for comparison
        return us_open_today_est.astimezone(utc)

    def _reset_if_needed(self):
        """Resets daily counters at next US market open."""
        now_utc = datetime.now(pytz.UTC)
        if now_utc >= self.next_reset_ts:
            log.info(f"US Market Open — resetting daily trade limits.")
            self.trades_today = 0
            self.daily_pnl_pct = 0.0
            self.next_reset_ts = self._calculate_next_us_open(now_utc)

    # -------------------------------------------------------
    # Exposure / Rule Enforcement
    # -------------------------------------------------------

    def can_trade(self) -> bool:
        """Determines if a new trade is allowed."""
        self._reset_if_needed()

        if self.trades_today >= self.max_trades_per_day:
            log.warning("Trade limit reached — no new trades today.")
            return False

        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            log.warning(
                f"Daily loss cap reached ({self.daily_pnl_pct:.2%}). "
                f"Stopping trading until next US open."
            )
            return False

        if self.daily_pnl_pct >= self.max_daily_profit_pct:
            log.info(
                f"Daily profit target reached ({self.daily_pnl_pct:.2%}). "
                f"Locking in profits — no more trades today."
            )
            return False

        return True

    def record_trade_opened(self):
        self.trades_today += 1
        log.info(
            f"Trade opened — {self.trades_today}/{self.max_trades_per_day}, "
            f"PnL: {self.daily_pnl_pct:.2%}"
        )

    def record_trade_result(self, pnl_pct: float):
        """
        Track PnL after a trade closes.
        pnl_pct example:
            +0.01 = +1%
            -0.005 = -0.5%
        """
        self.daily_pnl_pct += pnl_pct
        log.info(
            f"Trade result recorded: {pnl_pct:.2%}. "
            f"Daily PnL now {self.daily_pnl_pct:.2%}"
        )