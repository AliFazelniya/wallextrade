"""Portfolio Accounting & Position Tracking Engine."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Position(BaseModel):
  symbol: str
  quantity: float
  avg_entry_price: float
  current_price: float
  market_value_toman: float = 0.0
  unrealized_pnl_toman: float = 0.0
  unrealized_pnl_pct: float = 0.0


class PortfolioSnapshot(BaseModel):
  timestamp: str
  cash_toman: float
  crypto_value_toman: float
  total_equity_toman: float
  realized_pnl_toman: float
  unrealized_pnl_toman: float
  total_fees_paid_toman: float
  open_positions_count: int
  exposure_pct: float
  drawdown_pct: float


class PortfolioEngine:
  """Manages Toman cash, crypto holdings, trade fee deductions, and liquidation."""

  def __init__(
      self,
      initial_capital_toman: float = 5_000_000.0,
      fee_rate: float = 0.0025,
  ):
    self.initial_capital_toman = initial_capital_toman
    self.cash_toman = initial_capital_toman
    self.fee_rate = fee_rate

    self.positions: Dict[str, Position] = {}
    self.realized_pnl_toman = 0.0
    self.total_fees_paid_toman = 0.0
    self.peak_equity_toman = initial_capital_toman

  def update_market_price(self, symbol: str, current_price: float) -> None:
    """Updates valuation of an existing position."""
    if symbol in self.positions:
      pos = self.positions[symbol]
      pos.current_price = current_price
      pos.market_value_toman = pos.quantity * current_price
      pos.unrealized_pnl_toman = (
          current_price - pos.avg_entry_price
      ) * pos.quantity
      if pos.avg_entry_price > 0:
        pos.unrealized_pnl_pct = (
            (current_price - pos.avg_entry_price) / pos.avg_entry_price * 100.0
        )

  def record_fill(
      self, symbol: str, side: str, quantity: float, price: float
  ) -> Dict[str, Any]:
    """Records an executed order fill, updates balances, fees, and positions."""
    notional = quantity * price
    fee = notional * self.fee_rate
    self.total_fees_paid_toman += fee

    if side.upper() == "BUY":
      total_cost = notional + fee
      if total_cost > (self.cash_toman + 1.0):
        logger.warning(
            "Fill exceeds cash (%f > %f). Clamping cost.",
            total_cost,
            self.cash_toman,
        )
      self.cash_toman = max(0.0, self.cash_toman - total_cost)

      if symbol in self.positions:
        existing = self.positions[symbol]
        new_qty = existing.quantity + quantity
        new_cost = (
            existing.quantity * existing.avg_entry_price
        ) + notional  # blended entry
        existing.avg_entry_price = new_cost / new_qty if new_qty > 0 else 0.0
        existing.quantity = new_qty
        existing.current_price = price
        existing.market_value_toman = new_qty * price
      else:
        self.positions[symbol] = Position(
            symbol=symbol,
            quantity=quantity,
            avg_entry_price=price,
            current_price=price,
            market_value_toman=notional,
            unrealized_pnl_toman=0.0,
            unrealized_pnl_pct=0.0,
        )

      return {
          "status": "FILLED_BUY",
          "symbol": symbol,
          "quantity": quantity,
          "price": price,
          "notional": notional,
          "fee": fee,
      }

    elif side.upper() == "SELL":
      if symbol not in self.positions:
        raise ValueError(
            f"Cannot process SELL fill: no position for {symbol} exists."
        )

      pos = self.positions[symbol]
      sell_qty = min(quantity, pos.quantity)
      sell_notional = sell_qty * price
      net_proceeds = sell_notional - fee
      self.cash_toman += net_proceeds

      # Calculate realized P&L
      cost_basis = sell_qty * pos.avg_entry_price
      realized_gain = sell_notional - cost_basis - fee
      self.realized_pnl_toman += realized_gain

      pos.quantity -= sell_qty
      if pos.quantity <= 1e-9:
        del self.positions[symbol]
      else:
        pos.market_value_toman = pos.quantity * price
        pos.current_price = price
        pos.unrealized_pnl_toman = (price - pos.avg_entry_price) * pos.quantity

      return {
          "status": "FILLED_SELL",
          "symbol": symbol,
          "quantity": sell_qty,
          "price": price,
          "notional": sell_notional,
          "fee": fee,
          "realized_gain": realized_gain,
      }

    raise ValueError(f"Invalid order side '{side}'")

  def get_total_equity(self) -> float:
    """Returns cash + sum of all position market values."""
    crypto_val = sum(p.market_value_toman for p in self.positions.values())
    equity = self.cash_toman + crypto_val
    if equity > self.peak_equity_toman:
      self.peak_equity_toman = equity
    return equity

  def get_drawdown_pct(self) -> float:
    equity = self.get_total_equity()
    if self.peak_equity_toman <= 0:
      return 0.0
    return max(
        0.0,
        (self.peak_equity_toman - equity) / self.peak_equity_toman * 100.0,
    )

  def get_snapshot(self, timestamp: str) -> PortfolioSnapshot:
    equity = self.get_total_equity()
    crypto_val = sum(p.market_value_toman for p in self.positions.values())
    unrealized = sum(p.unrealized_pnl_toman for p in self.positions.values())
    exposure_pct = (crypto_val / equity * 100.0) if equity > 0 else 0.0

    return PortfolioSnapshot(
        timestamp=timestamp,
        cash_toman=round(self.cash_toman, 0),
        crypto_value_toman=round(crypto_val, 0),
        total_equity_toman=round(equity, 0),
        realized_pnl_toman=round(self.realized_pnl_toman, 0),
        unrealized_pnl_toman=round(unrealized, 0),
        total_fees_paid_toman=round(self.total_fees_paid_toman, 0),
        open_positions_count=len(self.positions),
        exposure_pct=round(exposure_pct, 2),
        drawdown_pct=round(self.get_drawdown_pct(), 2),
    )
