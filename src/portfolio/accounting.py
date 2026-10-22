"""Portfolio Accounting, Balance Reconciliation, and Liquidation Engine.

Enforces:
1. Accurate Maker (0.25%) vs Taker (0.30%) fee accounting based on verified Wallex schedule.
2. Separate tracking of Gross P&L, Net P&L, and Total Fees Paid.
3. Position tracking with blended cost basis.
4. Account-balance reconciliation against exchange API balance reports.
5. Deterministic End-of-Competition liquidation converting 100% of holdings into TMN.
"""

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
  gross_realized_pnl_toman: float
  net_realized_pnl_toman: float
  unrealized_pnl_toman: float
  total_fees_paid_toman: float
  open_positions_count: int
  exposure_pct: float
  drawdown_pct: float


class PortfolioEngine:
  """Manages Toman cash, crypto holdings, fees, and reconciliation."""

  def __init__(
      self,
      initial_capital_toman: float = 5_000_000.0,
      maker_fee_rate: float = 0.0025,  # 0.25% Level 1 Wallex Maker fee
      taker_fee_rate: float = 0.0030,  # 0.30% Level 1 Wallex Taker fee
  ):
    self.initial_capital_toman = initial_capital_toman
    self.cash_toman = initial_capital_toman
    self.maker_fee_rate = maker_fee_rate
    self.taker_fee_rate = taker_fee_rate

    self.positions: Dict[str, Position] = {}
    self.gross_realized_pnl_toman = 0.0
    self.net_realized_pnl_toman = 0.0
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
      self,
      symbol: str,
      side: str,
      quantity: float,
      price: float,
      is_maker: bool = True,
  ) -> Dict[str, Any]:
    """Records an executed order fill, updates cash, positions, and fees.

    Differentiates maker (0.25%) vs taker (0.30%) fees based on official Wallex
    schedule.
    """
    fee_rate = self.maker_fee_rate if is_maker else self.taker_fee_rate
    notional = quantity * price
    fee = notional * fee_rate
    self.total_fees_paid_toman += fee

    if side.upper() == "BUY":
      total_cost = notional + fee
      if total_cost > (self.cash_toman + 1.0):
        logger.warning(
            "Fill cost (%f) exceeds available cash (%f). Clamping cost.",
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
          "fee_rate": fee_rate,
          "is_maker": is_maker,
      }

    elif side.upper() == "SELL":
      if symbol not in self.positions:
        raise ValueError(
            f"Cannot process SELL fill: no active position for {symbol}."
        )

      pos = self.positions[symbol]
      sell_qty = min(quantity, pos.quantity)
      sell_notional = sell_qty * price
      net_proceeds = sell_notional - fee
      self.cash_toman += net_proceeds

      # Calculate Gross and Net Realized P&L
      cost_basis = sell_qty * pos.avg_entry_price
      gross_gain = sell_notional - cost_basis
      net_gain = gross_gain - fee

      self.gross_realized_pnl_toman += gross_gain
      self.net_realized_pnl_toman += net_gain

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
          "fee_rate": fee_rate,
          "gross_gain": gross_gain,
          "net_gain": net_gain,
          "is_maker": is_maker,
      }

    raise ValueError(f"Invalid order side '{side}'")

  def reconcile_with_exchange(
      self, exchange_balances: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Reconciles internal portfolio balances against live exchange balances."""
    discrepancies = []
    # Check TMN cash
    ex_tmn = float(
        exchange_balances.get("result", {})
        .get("balances", {})
        .get("TMN", {})
        .get("value", self.cash_toman)
    )
    diff = abs(ex_tmn - self.cash_toman)
    if diff > 1000.0:  # > 1,000 TMN discrepancy
      discrepancies.append(
          f"TMN cash mismatch: internal={self.cash_toman:.0f},"
          f" exchange={ex_tmn:.0f}"
      )

    return {
        "reconciled": len(discrepancies) == 0,
        "discrepancies": discrepancies,
    }

  def liquidate_all_to_toman(
      self, current_prices: Dict[str, float], slippage_pct: float = 0.15
  ) -> List[Dict[str, Any]]:
    """Liquidates 100% of crypto positions into Toman before competition ends."""
    liquidations = []
    symbols_to_liquidate = list(self.positions.keys())

    for sym in symbols_to_liquidate:
      pos = self.positions[sym]
      cur_price = current_prices.get(sym, pos.current_price)
      exec_price = cur_price * (1.0 - (slippage_pct / 100.0))

      fill = self.record_fill(
          symbol=sym,
          side="SELL",
          quantity=pos.quantity,
          price=exec_price,
          is_maker=False,  # Emergency liquidation treated as taker
      )
      liquidations.append(fill)

    return liquidations

  def get_total_equity(self) -> float:
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
        gross_realized_pnl_toman=round(self.gross_realized_pnl_toman, 0),
        net_realized_pnl_toman=round(self.net_realized_pnl_toman, 0),
        unrealized_pnl_toman=round(unrealized, 0),
        total_fees_paid_toman=round(self.total_fees_paid_toman, 0),
        open_positions_count=len(self.positions),
        exposure_pct=round(exposure_pct, 2),
        drawdown_pct=round(self.get_drawdown_pct(), 2),
    )

  def export_state(self) -> Dict[str, Any]:
    """Serializes the complete portfolio state for crash recovery."""
    return {
        "initial_capital_toman": self.initial_capital_toman,
        "cash_toman": self.cash_toman,
        "maker_fee_rate": self.maker_fee_rate,
        "taker_fee_rate": self.taker_fee_rate,
        "gross_realized_pnl_toman": self.gross_realized_pnl_toman,
        "net_realized_pnl_toman": self.net_realized_pnl_toman,
        "total_fees_paid_toman": self.total_fees_paid_toman,
        "peak_equity_toman": self.peak_equity_toman,
        "positions": {s: p.model_dump() for s, p in self.positions.items()},
    }

  @classmethod
  def from_state(cls, state: Dict[str, Any]) -> PortfolioEngine:
    """Restores the complete portfolio state after a process crash."""
    engine = cls(
        initial_capital_toman=state.get("initial_capital_toman", 5_000_000.0),
        maker_fee_rate=state.get("maker_fee_rate", 0.0025),
        taker_fee_rate=state.get("taker_fee_rate", 0.0030),
    )
    engine.cash_toman = state.get("cash_toman", engine.initial_capital_toman)
    engine.gross_realized_pnl_toman = state.get(
        "gross_realized_pnl_toman", 0.0
    )
    engine.net_realized_pnl_toman = state.get("net_realized_pnl_toman", 0.0)
    engine.total_fees_paid_toman = state.get("total_fees_paid_toman", 0.0)
    engine.peak_equity_toman = state.get(
        "peak_equity_toman", engine.cash_toman
    )
    engine.positions = {
        s: Position(**p_data)
        for s, p_data in state.get("positions", {}).items()
    }
    return engine
