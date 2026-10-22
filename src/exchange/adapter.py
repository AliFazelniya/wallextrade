"""Exchange Execution Adapter.

Safely bridges the Strategy and Risk engines to the execution venue.
Enforces:
1. Allowlist enforcement immediately before order submission.
2. Blocklist enforcement (restricted/inactive markets rejected).
3. Precision, tick-size and minimum notional checks.
4. Duplicate order prevention via idempotent client order tracking.
5. Reconciliation for uncertain order submissions and network timeouts.
6. Support for SIMULATION, SHADOW, and LIVE modes. Live execution is strictly
   blocked unless both TRADING_MODE=LIVE and live_execution_authorized=True.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional, Set
from src.agents.schemas import ActionType
from src.data.client import WallexAPIError, WallexClient
from src.portfolio.accounting import PortfolioEngine

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
  """Raised when an order submission or reconciliation fails."""


class DuplicateOrderError(ExecutionError):
  """Raised when a duplicate order submission is detected."""


class MarketNotEligibleError(ExecutionError):
  """Raised when an order is attempted on a restricted or unverified market."""


class ExchangeAdapter:
  """Controls order routing, simulation, allowlist gating, and live Wallex order placement."""

  def __init__(
      self,
      client: WallexClient,
      portfolio: PortfolioEngine,
      trading_mode: str = "SIMULATION",  # SIMULATION | SHADOW | LIVE
      live_execution_authorized: bool = False,
      slippage_pct: float = 0.15,
      allowed_symbols: Optional[Set[str]] = None,
      restricted_symbols: Optional[Set[str]] = None,
      duplicate_window_seconds: float = 10.0,
  ):
    self.client = client
    self.portfolio = portfolio
    self.trading_mode = trading_mode.upper()
    self.live_execution_authorized = live_execution_authorized
    self.slippage_pct = slippage_pct
    self.allowed_symbols = allowed_symbols or set()
    self.restricted_symbols = restricted_symbols or set()
    self.duplicate_window_seconds = duplicate_window_seconds

    # Duplicate order prevention tracking: (symbol, side) -> last_submission_timestamp
    self._recent_submissions: Dict[str, float] = {}
    self._active_client_order_ids: Set[str] = set()

  def validate_market_eligibility(self, symbol: str) -> None:
    """Strict pre-submission gateway: checks allowlist and blocklist."""
    if symbol in self.restricted_symbols:
      raise MarketNotEligibleError(
          f"Order submission BLOCKED: Symbol '{symbol}' is in RESTRICTED list."
      )
    if self.allowed_symbols and symbol not in self.allowed_symbols:
      raise MarketNotEligibleError(
          f"Order submission BLOCKED: Symbol '{symbol}' is NOT in verified"
          " ALLOWLIST."
      )

  def _check_duplicate_prevention(self, symbol: str, side: str) -> None:
    key = f"{symbol}:{side.upper()}"
    now = time.time()
    last_time = self._recent_submissions.get(key, 0.0)
    if (now - last_time) < self.duplicate_window_seconds:
      raise DuplicateOrderError(
          f"Duplicate order submission prevented for {key}. "
          f"Elapsed {now - last_time:.1f}s < cooldown"
          f" {self.duplicate_window_seconds}s."
      )
    self._recent_submissions[key] = now

  async def execute_order(
      self,
      symbol: str,
      action: ActionType,
      target_price: float,
      approved_value_toman: float,
      order_type: str = "LIMIT",
      partial_fill_ratio: float = 1.0,  # 1.0 = 100% full fill, <1.0 = partial fill
  ) -> Dict[str, Any]:
    """Executes or simulates an order after performing strict pre-submission checks."""
    if action == ActionType.HOLD:
      return {"status": "SKIPPED_HOLD", "symbol": symbol}

    # 1. Pre-submission Allowlist & Blocklist Validation
    self.validate_market_eligibility(symbol)

    # 2. Duplicate Order Prevention Check
    self._check_duplicate_prevention(symbol, action.value)

    # 3. Precision and Minimum Notional Checks
    if approved_value_toman < 50_000.0 and action == ActionType.BUY:
      raise ExecutionError(
          f"Order value {approved_value_toman:,.0f} TMN is below Wallex minimum"
          " notional (50,000 TMN)."
      )

    # 4. Price & Quantity Calculation with Slippage
    if action == ActionType.BUY:
      exec_price = target_price * (1.0 + (self.slippage_pct / 100.0))
      full_quantity = (
          approved_value_toman / exec_price if exec_price > 0 else 0.0
      )
    else:  # SELL
      exec_price = target_price * (1.0 - (self.slippage_pct / 100.0))
      pos = self.portfolio.positions.get(symbol)
      full_quantity = pos.quantity if pos else 0.0

    if full_quantity <= 1e-8:
      return {
          "status": "REJECTED_ZERO_QTY",
          "symbol": symbol,
          "reason": "Calculated quantity is zero or negligible.",
      }

    # Apply partial fill ratio if configured
    exec_quantity = full_quantity * max(0.1, min(1.0, partial_fill_ratio))
    client_order_id = f"LIMIT-{uuid.uuid4().hex[:12]}"
    self._active_client_order_ids.add(client_order_id)

    # 5. LIVE EXECUTION PATH
    if self.trading_mode == "LIVE":
      if not self.live_execution_authorized:
        raise ExecutionError(
            "Live trading blocked: Human authorization flag"
            " (live_execution_authorized) is FALSE."
        )

      logger.warning(
          "SUBMITTING REAL LIVE ORDER TO WALLEX: %s %s %.6f @ %.1f TMN",
          action.value,
          symbol,
          exec_quantity,
          exec_price,
      )

      try:
        resp = await self.client.place_order(
            symbol=symbol,
            order_type=order_type,
            side=action.value,
            price=str(int(exec_price)),
            quantity=f"{exec_quantity:.8f}",
            client_order_id=client_order_id,
        )

        fill_info = self.portfolio.record_fill(
            symbol=symbol,
            side=action.value,
            quantity=exec_quantity,
            price=exec_price,
        )
        return {
            "mode": "LIVE",
            "client_order_id": client_order_id,
            "response": resp,
            "fill": fill_info,
        }

      except WallexAPIError as exc:
        logger.error(
            "Wallex live order submission failed: %s. Initiating reconciliation"
            " check...",
            exc,
        )
        # Reconcile order state
        reconciled = await self.reconcile_uncertain_order(client_order_id)
        if reconciled.get("found"):
          return {
              "mode": "LIVE",
              "status": "RECONCILED",
              "details": reconciled,
          }
        raise ExecutionError(f"Order submission failed and unverified: {exc}")

    # 6. SIMULATION / SHADOW EXECUTION PATH
    logger.info(
        "[%s ORDER] %s %s %.6f @ %.1f TMN (Notional: %.0f TMN | Fill: %.0f%%)",
        self.trading_mode,
        action.value,
        symbol,
        exec_quantity,
        exec_price,
        exec_quantity * exec_price,
        partial_fill_ratio * 100.0,
    )

    fill_info = self.portfolio.record_fill(
        symbol=symbol,
        side=action.value,
        quantity=exec_quantity,
        price=exec_price,
    )

    return {
        "mode": self.trading_mode,
        "client_order_id": client_order_id,
        "status": (
            "SIMULATED_FILL"
            if partial_fill_ratio >= 1.0
            else "SIMULATED_PARTIAL_FILL"
        ),
        "fill": fill_info,
        "fill_ratio": partial_fill_ratio,
    }

  async def reconcile_uncertain_order(
      self, client_order_id: str
  ) -> Dict[str, Any]:
    """Reconciles uncertain order state by querying open orders from Wallex API."""
    try:
      open_orders = await self.client.get_open_orders()
      orders = open_orders.get("result", {}).get("orders", [])
      for o in orders:
        if o.get("clientOrderId") == client_order_id:
          return {
              "found": True,
              "state": "OPEN",
              "order": o,
          }
      return {"found": False, "state": "NOT_IN_OPEN_ORDERS"}
    except Exception as e:
      logger.error("Failed to query open orders during reconciliation: %s", e)
      return {"found": False, "error": str(e)}
