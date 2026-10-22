"""Comprehensive Unit Tests for Independent Risk Engine."""

import pytest
from src.agents.schemas import ActionType, MarketRegime, ProposedTradeSignal
from src.risk.engine import RiskEngine


def test_order_size_exceeding_limit_is_capped():
  engine = RiskEngine(
      max_single_order_toman=500_000.0,
      max_portfolio_exposure_pct=60.0,
      allowed_symbols={"BTCTMN"},
  )

  signal = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=22_000_000_000.0,
      order_value_toman=850_000.0,  # Exceeds 500k limit
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
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

  assert res.approved is True
  assert res.approved_value_toman == 500_000.0
  assert any("reduced" in w for w in res.risk_warnings)


def test_inactive_and_restricted_market_strictly_vetoed():
  engine = RiskEngine(
      restricted_symbols={"DOGETMN", "KITETMN", "AMZNXTMN", "TSLAXTMN"},
      allowed_symbols={"BTCTMN", "ETHTMN"},
  )

  for restricted_sym in ["DOGETMN", "KITETMN", "AMZNXTMN"]:
    signal = ProposedTradeSignal(
        symbol=restricted_sym,
        action=ActionType.BUY,
        target_price_toman=1000.0,
        order_value_toman=100_000.0,
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


def test_unverified_market_not_in_allowlist_vetoed():
  engine = RiskEngine(
      allowed_symbols={"BTCTMN", "ETHTMN"},
      restricted_symbols=set(),
  )

  signal = ProposedTradeSignal(
      symbol="UNKNOWN_COIN",
      action=ActionType.BUY,
      target_price_toman=500.0,
      order_value_toman=100_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
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
  assert any("ALLOWED" in r for r in res.veto_reasons)


def test_drawdown_limit_triggers_system_halt():
  engine = RiskEngine(
      max_drawdown_pct=5.0,
      allowed_symbols={"BTCTMN"},
  )
  engine.peak_portfolio_value_toman = 5_000_000.0

  # Portfolio dropped to 4,700,000 (6% drawdown)
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


def test_emergency_halt_vetoes_subsequent_orders():
  engine = RiskEngine(allowed_symbols={"BTCTMN"})
  engine.trigger_emergency_halt("Manual safety trigger")

  signal = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=22_000_000_000.0,
      order_value_toman=100_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.99,
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
  assert any("EMERGENCY HALT" in r for r in res.veto_reasons)


def test_max_concurrent_positions_limit():
  engine = RiskEngine(max_open_positions=2, allowed_symbols={"SOLTMN"})

  # Already have 2 active positions
  active_positions = {
      "BTCTMN": {"qty": 0.01},
      "ETHTMN": {"qty": 0.1},
  }

  signal = ProposedTradeSignal(
      symbol="SOLTMN",
      action=ActionType.BUY,
      target_price_toman=30_000_000.0,
      order_value_toman=200_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
      rationale="Test",
      timestamp="2026-10-22T10:00:00Z",
  )

  res = engine.evaluate_signal(
      signal=signal,
      current_portfolio_value_toman=5_000_000.0,
      current_cash_toman=2_000_000.0,
      current_crypto_exposure_toman=3_000_000.0,
      active_positions=active_positions,
      current_market_spread_pct=0.05,
  )

  assert res.approved is False
  assert any("maximum capacity" in r for r in res.veto_reasons)


def test_minimum_notional_rejection():
  engine = RiskEngine(allowed_symbols={"BTCTMN"})

  # Order below 50,000 TMN
  signal = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=22_000_000_000.0,
      order_value_toman=25_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
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
  assert any("minimum order notional" in r for r in res.veto_reasons)
