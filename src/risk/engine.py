"""Independent Deterministic Risk Management Engine.

Has absolute veto authority over all AI and algorithmic trade signals.
Enforces limits on order sizes, exposure, drawdown, spread, and market eligibility.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from src.agents.schemas import ActionType, ProposedTradeSignal

logger = logging.getLogger(__name__)


class RiskEvaluationResult(BaseModel):
  """Result of the deterministic risk check."""

  approved: bool
  symbol: str
  action: ActionType
  original_value_toman: float
  approved_value_toman: float
  veto_reasons: List[str] = Field(default_factory=list)
  risk_warnings: List[str] = Field(default_factory=list)


class RiskEngine:
  """Deterministic Gatekeeper. No order can reach the exchange without passing this engine."""

  def __init__(
      self,
      max_single_order_toman: float = 500_000.0,
      max_portfolio_exposure_pct: float = 60.0,
      max_drawdown_pct: float = 5.0,
      max_daily_loss_toman: float = 200_000.0,
      max_open_positions: int = 3,
      max_spread_pct: float = 0.35,
      allowed_symbols: Optional[Set[str]] = None,
      restricted_symbols: Optional[Set[str]] = None,
  ):
    self.max_single_order_toman = max_single_order_toman
    self.max_portfolio_exposure_pct = max_portfolio_exposure_pct
    self.max_drawdown_pct = max_drawdown_pct
    self.max_daily_loss_toman = max_daily_loss_toman
    self.max_open_positions = max_open_positions
    self.max_spread_pct = max_spread_pct
    self.allowed_symbols = allowed_symbols or set()
    self.restricted_symbols = restricted_symbols or set()

    # Dynamic tracking
    self.peak_portfolio_value_toman = 5_000_000.0
    self.consecutive_errors = 0
    self.emergency_halt = False

  def trigger_emergency_halt(self, reason: str) -> None:
    """Immediately stops all order placement system-wide."""
    self.emergency_halt = True
    logger.critical("EMERGENCY TRADING HALT TRIGGERED: %s", reason)

  def reset_emergency_halt(self) -> None:
    self.emergency_halt = False
    self.consecutive_errors = 0
    logger.info("Emergency halt reset by authorized operator.")

  def evaluate_signal(
      self,
      signal: ProposedTradeSignal,
      current_portfolio_value_toman: float,
      current_cash_toman: float,
      current_crypto_exposure_toman: float,
      active_positions: Dict[str, Any],
      current_market_spread_pct: float,
  ) -> RiskEvaluationResult:
    """Evaluates a proposed trade signal against all deterministic risk rules."""
    veto_reasons: List[str] = []
    warnings: List[str] = []

    # 1. Emergency Halt Check
    if self.emergency_halt:
      veto_reasons.append("System is in EMERGENCY HALT state.")

    # 2. Market Eligibility Check
    if signal.symbol in self.restricted_symbols:
      veto_reasons.append(
          f"Symbol '{signal.symbol}' is explicitly listed in RESTRICTED markets."
      )

    if self.allowed_symbols and signal.symbol not in self.allowed_symbols:
      veto_reasons.append(
          f"Symbol '{signal.symbol}' is not present in ALLOWED market universe."
      )

    # 3. Spread Check
    if current_market_spread_pct > self.max_spread_pct:
      veto_reasons.append(
          f"Market spread ({current_market_spread_pct:.3f}%) exceeds maximum"
          f" allowed limit ({self.max_spread_pct:.3f}%)."
      )

    # Update Peak Value
    if current_portfolio_value_toman > self.peak_portfolio_value_toman:
      self.peak_portfolio_value_toman = current_portfolio_value_toman

    # 4. Maximum Drawdown Check
    drawdown_pct = 0.0
    if self.peak_portfolio_value_toman > 0:
      drawdown_pct = (
          (self.peak_portfolio_value_toman - current_portfolio_value_toman)
          / self.peak_portfolio_value_toman
          * 100.0
      )
    if drawdown_pct >= self.max_drawdown_pct:
      veto_reasons.append(
          f"Portfolio drawdown ({drawdown_pct:.2f}%) breached safety threshold"
          f" ({self.max_drawdown_pct:.2f}%)."
      )
      self.trigger_emergency_halt(
          f"Drawdown breach: {drawdown_pct:.2f}% >= {self.max_drawdown_pct:.2f}%"
      )

    # Action-Specific Checks
    approved_value = signal.order_value_toman

    if signal.action == ActionType.BUY:
      # 5. Position Limit Check
      if (
          len(active_positions) >= self.max_open_positions
          and signal.symbol not in active_positions
      ):
        veto_reasons.append(
            f"Active positions ({len(active_positions)}) already at maximum"
            f" capacity ({self.max_open_positions})."
        )

      # 6. Single Order Size Limit
      if approved_value > self.max_single_order_toman:
        warnings.append(
            f"Order size reduced from {approved_value:,.0f} to"
            f" {self.max_single_order_toman:,.0f} TMN."
        )
        approved_value = self.max_single_order_toman

      # 7. Cash Availability Check
      if approved_value > current_cash_toman:
        warnings.append(
            f"Order size constrained by available cash balance"
            f" ({current_cash_toman:,.0f} TMN)."
        )
        approved_value = current_cash_toman

      # 8. Portfolio Exposure Check
      max_allowed_crypto_toman = (
          current_portfolio_value_toman
          * (self.max_portfolio_exposure_pct / 100.0)
      )
      if (current_crypto_exposure_toman + approved_value) > (
          max_allowed_crypto_toman + 1000.0
      ):
        available_room = max(
            0.0, max_allowed_crypto_toman - current_crypto_exposure_toman
        )
        if available_room < 50_000.0:  # Min notional in Wallex is 50,000 TMN
          veto_reasons.append(
              "Portfolio exposure would exceed limit"
              f" ({self.max_portfolio_exposure_pct:.1f}%). Insufficient capacity"
              " for minimum notional."
          )
        else:
          approved_value = min(approved_value, available_room)

      # Minimum Notional Check (Wallex requires >= 50,000 TMN)
      if approved_value < 50_000.0:
        veto_reasons.append(
            f"Approved value ({approved_value:,.0f} TMN) is below Wallex"
            " minimum order notional (50,000 TMN)."
        )

    elif signal.action == ActionType.SELL:
      # Sells are always allowed to de-risk
      if signal.symbol not in active_positions:
        veto_reasons.append(
            f"Cannot SELL {signal.symbol}: no active position exists."
        )

    is_approved = len(veto_reasons) == 0

    return RiskEvaluationResult(
        approved=is_approved,
        symbol=signal.symbol,
        action=signal.action,
        original_value_toman=signal.order_value_toman,
        approved_value_toman=approved_value if is_approved else 0.0,
        veto_reasons=veto_reasons,
        risk_warnings=warnings,
    )
