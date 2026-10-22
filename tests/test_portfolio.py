"""Comprehensive Unit Tests for Portfolio Accounting, Fees, and Liquidation."""

import pytest
from src.portfolio.accounting import PortfolioEngine


def test_initial_portfolio_balance():
  engine = PortfolioEngine(initial_capital_toman=5_000_000.0)
  assert engine.cash_toman == 5_000_000.0
  assert engine.get_total_equity() == 5_000_000.0
  assert len(engine.positions) == 0


def test_maker_vs_taker_fee_rates():
  engine = PortfolioEngine(
      initial_capital_toman=5_000_000.0,
      maker_fee_rate=0.0025,  # 0.25%
      taker_fee_rate=0.0030,  # 0.30%
  )

  # Limit Buy (Maker: 0.25%)
  fill_maker = engine.record_fill(
      symbol="BTCTMN",
      side="BUY",
      quantity=0.01,
      price=100_000_000.0,  # notional: 1,000,000 TMN
      is_maker=True,
  )
  assert fill_maker["fee"] == 2_500.0  # 0.25% of 1,000,000
  assert fill_maker["fee_rate"] == 0.0025

  # Market/Emergency Sell (Taker: 0.30%)
  fill_taker = engine.record_fill(
      symbol="BTCTMN",
      side="SELL",
      quantity=0.01,
      price=110_000_000.0,  # notional: 1,100,000 TMN
      is_maker=False,
  )
  assert fill_taker["fee"] == 3_300.0  # 0.30% of 1,100,000
  assert fill_taker["fee_rate"] == 0.0030


def test_gross_and_net_pnl_accounting():
  engine = PortfolioEngine(
      initial_capital_toman=5_000_000.0,
      maker_fee_rate=0.0025,
      taker_fee_rate=0.0030,
  )

  # Buy 0.01 @ 100M TMN (Cost: 1,000,000 + 2,500 fee)
  engine.record_fill("BTCTMN", "BUY", 0.01, 100_000_000.0, is_maker=True)

  # Sell 0.01 @ 105M TMN (Notional: 1,050,000, Fee: 3,150)
  res = engine.record_fill("BTCTMN", "SELL", 0.01, 105_000_000.0, is_maker=False)

  assert res["gross_gain"] == 50_000.0  # 1.05M - 1.0M
  assert res["net_gain"] == 50_000.0 - 3_150.0  # gross - sell fee
  assert engine.total_fees_paid_toman == 2_500.0 + 3_150.0  # 5,650 TMN


def test_balance_reconciliation():
  engine = PortfolioEngine(initial_capital_toman=5_000_000.0)

  # Match
  mock_exchange_ok = {
      "result": {
          "balances": {
              "TMN": {
                  "value": "5000000.0000000000000000",
                  "locked": "0.0000000000000000",
              }
          }
      }
  }
  rec_ok = engine.reconcile_with_exchange(mock_exchange_ok)
  assert rec_ok["reconciled"] is True
  assert len(rec_ok["discrepancies"]) == 0

  # Discrepancy
  mock_exchange_mismatch = {
      "result": {
          "balances": {
              "TMN": {
                  "value": "4500000.0000000000000000",
                  "locked": "0.0000000000000000",
              }
          }
      }
  }
  rec_bad = engine.reconcile_with_exchange(mock_exchange_mismatch)
  assert rec_bad["reconciled"] is False
  assert len(rec_bad["discrepancies"]) > 0


def test_forced_liquidation_to_toman():
  engine = PortfolioEngine(initial_capital_toman=5_000_000.0)

  # Buy 2 positions
  engine.record_fill("BTCTMN", "BUY", 0.01, 100_000_000.0)
  engine.record_fill("ETHTMN", "BUY", 0.1, 10_000_000.0)

  assert len(engine.positions) == 2

  current_prices = {"BTCTMN": 102_000_000.0, "ETHTMN": 10_500_000.0}
  fills = engine.liquidate_all_to_toman(current_prices, slippage_pct=0.15)

  assert len(fills) == 2
  assert len(engine.positions) == 0  # 100% liquidated
  assert engine.cash_toman > 0
  assert engine.get_total_equity() == engine.cash_toman  # All equity is in cash
