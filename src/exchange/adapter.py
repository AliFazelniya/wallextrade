"""Exchange Execution Adapter.

Safely bridges the Strategy and Risk engines to the execution venue.
Supports SIMULATION, SHADOW, and LIVE modes. Live execution is strictly disabled
unless both environment flags and explicit operator authorization are present.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional
from src.agents.schemas import ActionType
from src.data.client import WallexClient
from src.portfolio.accounting import PortfolioEngine

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
  """Raised when an order submission or reconciliation fails."""


class ExchangeAdapter:
  """Controls order routing, simulation, and live Wallex order placement."""

  def __init__(
      self,
      client: WallexClient,
      portfolio: PortfolioEngine,
      trading_mode: str = "SIMULATION",  # SIMULATION | SHADOW | LIVE
      live_execution_authorized: bool = False,
      slippage_pct: float = 0.15,
  ):
    self.client = client
    self.portfolio = portfolio
    self.trading_mode = trading_mode.upper()
    self.live_execution_authorized = live_execution_authorized
    self.slippage_pct = slippage_pct

  async def execute_order(
      self,
      symbol: str,
      action: ActionType,
      target_price: float,
      approved_value_toman: float,
      order_type: str = "LIMIT",
  ) -> Dict[str, Any]:
    """Executes or simulates an order based on current trading_mode."""
    client_order_id = f"ORDER-{uuid.uuid4().hex[:12]}"

    if action == ActionType.HOLD:
      return {"status": "SKIPPED_HOLD", "symbol": symbol}

    # Calculate execution price with simulated slippage
    exec_price = target_price
    if action == ActionType.BUY:
      exec_price = target_price * (1.0 + (self.slippage_pct / 100.0))
      quantity = approved_value_toman / exec_price if exec_price > 0 else 0.0
    else:  # SELL
      exec_price = target_price * (1.0 - (self.slippage_pct / 100.0))
      pos = self.portfolio.positions.get(symbol)
      quantity = pos.quantity if pos else 0.0

    if quantity <= 1e-8:
      return {
          "status": "REJECTED_ZERO_QTY",
          "symbol": symbol,
          "reason": "Calculated quantity is zero or negligible.",
      }

    # 1. LIVE TRADING MODE
    if self.trading_mode == "LIVE":
      if not self.live_execution_authorized:
        raise ExecutionError(
            "Live trading blocked: human authorization flag"
            " (live_execution_authorized) is FALSE."
        )

      logger.warning(
          "SUBMITTING REAL LIVE ORDER to Wallex: %s %s %f @ %f",
          action.value,
          symbol,
          quantity,
          exec_price,
      )

      # Send order to Wallex API
      resp = await self.client.place_order(
          symbol=symbol,
          order_type=order_type,
          side=action.value,
          price=str(int(exec_price)),
          quantity=f"{quantity:.8f}",
          client_order_id=client_order_id,
      )

      # Record fill in portfolio
      fill_info = self.portfolio.record_fill(
          symbol=symbol,
          side=action.value,
          quantity=quantity,
          price=exec_price,
      )
      return {
          "mode": "LIVE",
          "client_order_id": client_order_id,
          "response": resp,
          "fill": fill_info,
      }

    # 2. SHADOW / SIMULATION MODE
    logger.info(
        "[%s ORDER] %s %s %.6f @ %.1f TMN (Notional: %.0f TMN)",
        self.trading_mode,
        action.value,
        symbol,
        quantity,
        exec_price,
        quantity * exec_price,
    )

    fill_info = self.portfolio.record_fill(
        symbol=symbol,
        side=action.value,
        quantity=quantity,
        price=exec_price,
    )

    return {
        "mode": self.trading_mode,
        "client_order_id": client_order_id,
        "status": "SIMULATED_FILL",
        "fill": fill_info,
    }
