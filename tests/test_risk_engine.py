"""Unit tests for the Independent Risk Engine."""

import pytest
from src.agents.schemas import ActionType, MarketRegime, ProposedTradeSignal
from src.risk.engine import RiskEngine


def test_order_size_exceeding_limit_is_reduced_or_vetoed():
  engine = RiskEngine(
      max_single_order_toman=500_000.0,
      max_portfolio_exposure_pct=60.0,
      allowed_symbols={"BTCTMN"},
  )

  # Signal with order value > 500,000 TMN
  signal = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=22_000_000_000.0,
      order_value_toman=800_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
      rationale="Test bullish signal",
      timestamp="2026-10-22T10:00:00Z",
  )

  res = engine.evaluate_signal(
      signal=signal,
      current_portfolio_value_toman=5_000_000.0,
      current_cash_toman=5_000_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.05,
  )

  assert res.approved is True
  # Value must be capped at 500,000 TMN
  assert res.approved_value_toman == 500_000.0
  assert any("reduced" in w for w in res.risk_warnings)


def test_restricted_market_is_strictly_vetoed():
  engine = RiskEngine(
      restricted_symbols={"DOGETMN"},
      allowed_symbols={"BTCTMN", "ETHTMN"},
  )

  signal = ProposedTradeSignal(
      symbol="DOGETMN",
      action=ActionType.BUY,
      target_price_toman=21000.0,
      order_value_toman=300_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.90,
      rationale="Test",
      timestamp="2026-10-22T10:00:00Z",
  )

  res = engine.evaluate_signal(
      signal=signal,
      current_portfolio_value_toman=5_000_000.0,
      current_cash_toman=5_000_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.05,
  )

  assert res.approved is False
  assert any("RESTRICTED" in r for r in res.veto_reasons)


def test_drawdown_limit_triggers_halt():
  engine = RiskEngine(
      max_drawdown_pct=5.0,
      allowed_symbols={"BTCTMN"},
  )
  engine.peak_portfolio_value_toman = 5_000_000.0

  # Portfolio has dropped to 4,700,000 (6% drawdown)
  signal = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=22_000_000_000.0,
      order_value_toman=200_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
      rationale="Test",
      timestamp="2026-10-22T10:00:00Z",
  )

  res = engine.evaluate_signal(
      signal=signal,
      current_portfolio_value_toman=4_700_000.0,
      current_cash_toman=4_700_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.05,
  )

  assert res.approved is False
  assert engine.emergency_halt is True
  assert any("drawdown" in r.lower() for r in res.veto_reasons)


def test_wide_spread_is_vetoed():
  engine = RiskEngine(
      max_spread_pct=0.35,
      allowed_symbols={"BTCTMN"},
  )

  signal = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=22_000_000_000.0,
      order_value_toman=300_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
      rationale="Test",
      timestamp="2026-10-22T10:00:00Z",
  )

  # Spread is 0.50% (exceeds 0.35%)
  res = engine.evaluate_signal(
      signal=signal,
      current_portfolio_value_toman=5_000_000.0,
      current_cash_toman=5_000_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.50,
  )

  assert res.approved is False
  assert any("spread" in r.lower() for r in res.veto_reasons)
