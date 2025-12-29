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
        max_daily_profit_pct: float = 0.015,  # +1.5% daily profit target
        log_resets: bool = True,
        log_blocks: bool = True
    ):
        self.max_trades_per_day = max_trades_per_day
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_daily_profit_pct = max_daily_profit_pct
        
        self.trades_today = 0
        self.daily_pnl_pct = 0.0
        self._last_block_reason = None
        self.log_resets = log_resets
        self.log_blocks = log_blocks
        
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

    def _normalize_time(self, now_utc: datetime = None) -> datetime:
        if now_utc is None:
            return datetime.now(pytz.UTC)

        if hasattr(now_utc, "to_pydatetime"):
            now_utc = now_utc.to_pydatetime()

        if now_utc.tzinfo is None:
            return pytz.UTC.localize(now_utc)

        return now_utc.astimezone(pytz.UTC)

    def _reset_if_needed(self, now_utc: datetime = None):
        """Resets daily counters at next US market open."""
        now_utc = self._normalize_time(now_utc)
        # Align reset schedule when backtesting past data.
        if now_utc < self.next_reset_ts:
            self.next_reset_ts = self._calculate_next_us_open(now_utc)
        if now_utc >= self.next_reset_ts:
            if self.log_resets:
                log.info("US Market Open — resetting daily trade limits.")
            self.trades_today = 0
            self.daily_pnl_pct = 0.0
            self.next_reset_ts = self._calculate_next_us_open(now_utc)
            self._last_block_reason = None

    def _log_block_once(self, reason_key: str, message: str, level: str = "info"):
        """Avoid spamming the log when a daily block is already active."""
        if not self.log_blocks:
            return
        if self._last_block_reason == reason_key:
            return
        self._last_block_reason = reason_key
        getattr(log, level)(message)

    # -------------------------------------------------------
    # Exposure / Rule Enforcement
    # -------------------------------------------------------

    def can_trade(self, now_utc: datetime = None) -> bool:
        """Determines if a new trade is allowed."""
        self._reset_if_needed(now_utc)

        if self.trades_today >= self.max_trades_per_day:
            self._log_block_once(
                "trade_limit",
                "Trade limit reached — no new trades today.",
                level="warning"
            )
            return False

        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            self._log_block_once(
                "daily_loss",
                f"Daily loss cap reached ({self.daily_pnl_pct:.2%}). "
                f"Stopping trading until next US open.",
                level="warning"
            )
            return False

        if self.daily_pnl_pct >= self.max_daily_profit_pct:
            self._log_block_once(
                "daily_profit",
                f"Daily profit target reached ({self.daily_pnl_pct:.2%}). "
                f"Locking in profits — no more trades today.",
                level="info"
            )
            return False

        self._last_block_reason = None
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
