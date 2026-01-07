from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math

import ccxt

from utils.config import Config
from utils.logger import log


@dataclass
class LivePosition:
    side: str
    entry_price: float
    amount: float
    stop_loss: float
    take_profit: float


class LiveBroker:
    """
    Live execution for Binance USDⓈ-M futures (USDC perpetuals).
    Places market entries and protective stop/take-profit orders.
    """

    def __init__(self, symbol: str, leverage: int, risk_per_trade: float):
        if not Config.BINANCE_API_KEY or not Config.BINANCE_API_SECRET:
            raise ValueError("Binance API keys are required for live trading.")

        self.symbol = symbol
        self.leverage = leverage
        self.risk_per_trade = risk_per_trade
        self.client = ccxt.binanceusdm({
            "apiKey": Config.BINANCE_API_KEY,
            "secret": Config.BINANCE_API_SECRET,
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        })
        self.client.load_markets()
        self._position: Optional[LivePosition] = None
        self._min_amount = max(self._load_min_amount(), Config.MIN_ORDER_QTY)
        self._amount_step = self._load_amount_step()
        self._set_leverage()

    def _set_leverage(self) -> None:
        try:
            self.client.set_leverage(self.leverage, self.symbol)
            log.info(f"Leverage set to {self.leverage}x for {self.symbol}.")
        except Exception as exc:
            log.warning(f"Could not set leverage: {exc}")

    def _fetch_position(self) -> Optional[dict]:
        try:
            positions = self.client.fetch_positions([self.symbol])
        except Exception as exc:
            log.warning(f"Failed to fetch positions: {exc}")
            return None

        symbol_id = self.symbol.replace("/", "")
        for pos in positions:
            pos_symbol = pos.get("symbol")
            info_symbol = pos.get("info", {}).get("symbol")
            if pos_symbol == self.symbol or info_symbol == symbol_id:
                return pos
        return None

    def has_open_position(self) -> bool:
        pos = self._fetch_position()
        if not pos:
            return False

        contracts = pos.get("contracts")
        if contracts is None:
            contracts = pos.get("info", {}).get("positionAmt")

        try:
            return abs(float(contracts)) > 0
        except (TypeError, ValueError):
            return False

    def _get_equity(self) -> Optional[float]:
        try:
            balance = self.client.fetch_balance()
        except Exception as exc:
            log.warning(f"Failed to fetch balance: {exc}")
            return None

        for currency in ("USDC", "USDT"):
            total_map = balance.get("total", {})
            if currency in total_map:
                return float(total_map[currency])
            if currency in balance:
                total = balance[currency].get("total")
                if total is not None:
                    return float(total)

        log.warning("No USDC/USDT balance found.")
        return None

    def _amount_to_precision(self, amount: float) -> float:
        try:
            return float(self.client.amount_to_precision(self.symbol, amount))
        except Exception:
            return round(amount, 6)

    def _load_amount_step(self) -> float:
        try:
            market = self.client.market(self.symbol)
        except Exception:
            return 0.0

        precision = market.get("precision", {}).get("amount")
        try:
            if precision is None:
                return 0.0
            precision = int(precision)
            if precision <= 0:
                return 0.0
            return 10 ** (-precision)
        except (TypeError, ValueError):
            return 0.0

    def _enforce_min_amount(self, amount: float) -> float:
        if not self._min_amount:
            return amount

        min_amount = self._round_up_amount(self._min_amount)
        amount = self._round_up_amount(amount)
        if amount < min_amount:
            return min_amount
        return amount

    def _round_up_amount(self, amount: float) -> float:
        step = self._amount_step or self._min_amount
        if not step:
            return amount

        return math.ceil(amount / step) * step

    def _compute_order_size(self, entry_price: float, stop_loss: float) -> Optional[float]:
        equity = self._get_equity()
        if equity is None:
            return None

        max_notional = equity * Config.MAX_MARGIN_UTILIZATION * max(self.leverage, 1)
        max_qty = max_notional / entry_price

        if Config.FIXED_NOTIONAL_USDC > 0:
            target_notional = min(Config.FIXED_NOTIONAL_USDC, max_notional)
            qty = target_notional / entry_price
            if self._min_amount and qty < self._min_amount:
                min_notional = self._min_amount * entry_price
                if min_notional <= max_notional:
                    qty = self._min_amount
                else:
                    log.warning(
                        f"Min amount notional {min_notional:.2f} exceeds max allowed "
                        f"{max_notional:.2f} — skipping trade."
                    )
                    return None
        else:
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit <= 0:
                log.warning("Invalid stop distance — cannot size position.")
                return None

            risk_amount = equity * self.risk_per_trade
            qty = risk_amount / risk_per_unit

            qty = min(qty, max_qty)
        min_notional = max(Config.MIN_NOTIONAL_USDC, Config.MIN_ORDER_NOTIONAL_USDC)
        if min_notional > max_notional:
            log.warning(
                f"Min notional {min_notional:.2f} exceeds max allowed "
                f"{max_notional:.2f} — skipping trade."
            )
            return None

        required_qty = min_notional / entry_price
        qty = max(qty, required_qty)
        qty = self._round_up_amount(qty)
        qty = self._enforce_min_amount(qty)
        log.info(
            f"Sizing debug — equity={equity:.2f}, entry={entry_price:.2f}, "
            f"max_notional={max_notional:.2f}, qty={qty:.6f}, "
            f"min_qty={self._min_amount:.6f}, min_notional={min_notional:.2f}, "
            f"required_qty={required_qty:.6f}"
        )

        if qty <= 0:
            return None

        if self._min_amount and qty < self._min_amount:
            log.warning(
                f"Order size {qty:.6f} below min amount {self._min_amount:.6f} — skipping trade."
            )
            return None

        notional = qty * entry_price
        if notional < min_notional:
            log.warning(
                f"Notional {notional:.2f} below min required "
                f"({min_notional:.2f}) — skipping trade."
            )
            return None

        return qty

    @staticmethod
    def _side_to_order(side: str) -> str:
        return "buy" if side == "LONG" else "sell"

    def open_position(self, side: str, entry_price: float, stop_loss: float, take_profit: float) -> bool:
        amount = self._compute_order_size(entry_price, stop_loss)
        if amount is None:
            log.warning("Position size could not be calculated — skipping trade.")
            return False

        order_side = self._side_to_order(side)
        try:
            self.client.create_order(self.symbol, "market", order_side, amount)
            log.info(
                f"Opened {side} {self.symbol} size={amount} entry={entry_price:.2f}"
            )
        except Exception as exc:
            log.error(f"Failed to open position: {exc}")
            return False

        try:
            exit_side = "sell" if order_side == "buy" else "buy"
            self.client.create_order(
                self.symbol,
                "STOP_MARKET",
                exit_side,
                amount,
                None,
                {"stopPrice": stop_loss, "reduceOnly": True},
            )
            self.client.create_order(
                self.symbol,
                "TAKE_PROFIT_MARKET",
                exit_side,
                amount,
                None,
                {"stopPrice": take_profit, "reduceOnly": True},
            )
        except Exception as exc:
            log.warning(f"Failed to place protective orders: {exc}")

        self._position = LivePosition(
            side=side,
            entry_price=entry_price,
            amount=amount,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        return True

    def sync_position(self, trade_limiter=None, mark_price: Optional[float] = None) -> None:
        if self._position is None:
            return

        if self.has_open_position():
            return

        exit_price = mark_price or self._position.entry_price
        pnl_pct = self._estimate_pnl(exit_price)
        if trade_limiter and pnl_pct is not None:
            trade_limiter.record_trade_result(pnl_pct)
        log.info(f"Position closed. Estimated PnL: {pnl_pct:.2%}")
        self._position = None

    def _estimate_pnl(self, exit_price: float) -> Optional[float]:
        if not self._position:
            return None

        entry = self._position.entry_price
        if entry <= 0:
            return None

        if self._position.side == "LONG":
            return (exit_price - entry) / entry
        return (entry - exit_price) / entry
    def _load_min_amount(self) -> float:
        try:
            market = self.client.market(self.symbol)
        except Exception:
            return 0.0

        min_amount = market.get("limits", {}).get("amount", {}).get("min")
        try:
            return float(min_amount) if min_amount is not None else 0.0
        except (TypeError, ValueError):
            return 0.0
