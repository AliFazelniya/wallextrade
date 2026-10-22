"""Unit tests for Portfolio Accounting and Positions."""

import pytest
from src.portfolio.accounting import PortfolioEngine


def test_initial_portfolio_balance():
  engine = PortfolioEngine(initial_capital_toman=5_000_000.0)
  assert engine.cash_toman == 5_000_000.0
  assert engine.get_total_equity() == 5_000_000.0
  assert len(engine.positions) == 0


def test_buy_fill_records_fee_and_updates_cash():
  engine = PortfolioEngine(initial_capital_toman=5_000_000.0, fee_rate=0.0025)

  # Buy 0.01 BTC at 100,000,000 TMN (notional = 1,000,000 TMN, fee = 2,500 TMN)
  fill = engine.record_fill(
      symbol="BTCTMN",
      side="BUY",
      quantity=0.01,
      price=100_000_000.0,
  )

  assert fill["notional"] == 1_000_000.0
  assert fill["fee"] == 2_500.0
  assert engine.cash_toman == 5_000_000.0 - 1_002_500.0
  assert "BTCTMN" in engine.positions
  assert engine.positions["BTCTMN"].quantity == 0.01
  assert engine.total_fees_paid_toman == 2_500.0


def test_sell_fill_calculates_realized_gain_and_returns_cash():
  engine = PortfolioEngine(initial_capital_toman=5_000_000.0, fee_rate=0.0025)

  # Entry: 0.01 BTC @ 100M TMN (cost: 1M + 2.5k fee)
  engine.record_fill("BTCTMN", "BUY", 0.01, 100_000_000.0)

  # Exit: 0.01 BTC @ 105M TMN (notional: 1.05M, fee: 2,625 TMN)
  sell_fill = engine.record_fill("BTCTMN", "SELL", 0.01, 105_000_000.0)

  assert sell_fill["notional"] == 1_050_000.0
  # Net proceeds: 1,050,000 - 2,625 = 1,047,375 TMN
  # Realized Gain: 1,050,000 - 1,000,000 - 2,625 = 47,375 TMN
  assert sell_fill["realized_gain"] == 47_375.0
  assert len(engine.positions) == 0  # Fully closed
  assert engine.cash_toman > 5_000_000.0  # Net profit made
