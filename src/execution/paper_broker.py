from dataclasses import dataclass
from typing import Optional
from utils.logger import log


@dataclass
class Position:
    symbol: str
    side: str             # "LONG" or "SHORT"
    entry_price: float
    stop_loss: float
    take_profit: float


class PaperBroker:
    """
    Simulates trade execution without live orders.
    Handles:
        - opening simulated positions
        - closing on SL/TP hit
        - computing PnL %
        - tracking open position state

    Notes:
        - executes at candle close (backtesting behavior)
        - ignores slippage & fees for now (we will add later)
    """

    def __init__(self):
        self.position: Optional[Position] = None

    # --------------------
    # Position Management
    # --------------------

    def has_open_position(self) -> bool:
        return self.position is not None

    def open_position(self, symbol: str, side: str, entry: float,
                      stop_loss: float, take_profit: float) -> bool:
        if self.position:
            log.warning("Cannot open new position — one already open.")
            return False

        self.position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        log.info(
            f"Opened {side} position on {symbol} @ {entry} | "
            f"SL={stop_loss}, TP={take_profit}"
        )
        return True

    # --------------------
    # Exit Logic
    # --------------------

    def check_and_close(self, high: float, low: float, close: float,
                        trade_limiter=None) -> Optional[float]:
        """
        Check if an open position should close due to:
            - stop loss hit
            - take profit hit
            - OR continue open

        Returns:
            pnl_pct if closed, else None
        """

        if not self.position:
            return None

        pos = self.position
        pnl_pct = None

        # ---- LONG exit ----
        if pos.side == "LONG":
            # SL triggered if low breaches it
            if low <= pos.stop_loss:
                pnl_pct = (pos.stop_loss - pos.entry_price) / pos.entry_price
                log.info(f"LONG stopped out @ {pos.stop_loss} | PnL={pnl_pct:.2%}")

            # TP triggered if high touches it
            elif high >= pos.take_profit:
                pnl_pct = (pos.take_profit - pos.entry_price) / pos.entry_price
                log.info(f"LONG take-profit hit @ {pos.take_profit} | PnL={pnl_pct:.2%}")

        # ---- SHORT exit ----
        elif pos.side == "SHORT":
            # SL triggered if high breaches stop
            if high >= pos.stop_loss:
                pnl_pct = (pos.entry_price - pos.stop_loss) / pos.entry_price
                log.info(f"SHORT stopped out @ {pos.stop_loss} | PnL={pnl_pct:.2%}")

            # TP triggered if low touches it
            elif low <= pos.take_profit:
                pnl_pct = (pos.entry_price - pos.take_profit) / pos.entry_price
                log.info(f"SHORT take-profit hit @ {pos.take_profit} | PnL={pnl_pct:.2%}")

        # ---- If no exit condition met ----
        if pnl_pct is None:
            return None

        # ---- Record closure ----
        self.position = None

        # report to trade limiter if available
        if trade_limiter:
            trade_limiter.record_trade_result(pnl_pct)

        return pnl_pct