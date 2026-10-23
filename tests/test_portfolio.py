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


def test_accounting_slippage_and_fee_reconciliation_identity():
  """Verifies the core accounting invariant:

  1. Slippage is embedded into execution price and reflected in Gross P&L.
  2. Net P&L = Gross P&L - Total Exchange Fees (no double deduction of slippage).
  3. Ending Equity - Initial Capital = Net Realized P&L when all positions are closed.
  """
  initial_capital = 5_000_000.0
  engine = PortfolioEngine(
      initial_capital_toman=initial_capital,
      maker_fee_rate=0.0025,
      taker_fee_rate=0.0030,
  )

  target_buy_price = 20_000_000_000.0
  slippage_pct = 0.15
  # Aggressive entry crossing spread: price = target * 1.0015
  exec_buy_price = target_buy_price * (1.0 + (slippage_pct / 100.0))
  buy_qty = 0.000025  # 500,000 TMN target notional
  buy_notional = buy_qty * exec_buy_price
  buy_fee = buy_notional * 0.0030

  fill_buy = engine.record_fill(
      symbol="BTCTMN",
      side="BUY",
      quantity=buy_qty,
      price=exec_buy_price,
      is_maker=False,
  )

  # Slippage impact on entry: extra cost paid
  slippage_cost_entry = buy_qty * (exec_buy_price - target_buy_price)

  # Exit at target profit price (+3.5% above target_buy_price) as passive Maker
  target_sell_price = target_buy_price * 1.035
  exec_sell_price = target_sell_price  # passive maker, zero slippage
  sell_notional = buy_qty * exec_sell_price
  sell_fee = sell_notional * 0.0025

  fill_sell = engine.record_fill(
      symbol="BTCTMN",
      side="SELL",
      quantity=buy_qty,
      price=exec_sell_price,
      is_maker=True,
  )

  # Core Invariants
  total_fees = buy_fee + sell_fee
  assert engine.total_fees_paid_toman == pytest.approx(total_fees, abs=1e-4)

  # Realized Gross Gain = sell_notional - cost_basis (where cost_basis includes entry slippage)
  expected_cost_basis = buy_notional
  expected_gross_gain = sell_notional - expected_cost_basis
  assert engine.gross_realized_pnl_toman == pytest.approx(expected_gross_gain, abs=1e-4)

  # Sell ticket net realized gain = gross_gain - sell_fee
  assert engine.net_realized_pnl_toman == pytest.approx(expected_gross_gain - sell_fee, abs=1e-4)

  # Full Portfolio Equity Reconciliation Identity:
  # Net Equity Change = Gross Realized P&L - Total Fees Paid (Buy Fees + Sell Fees)
  net_portfolio_pnl = engine.gross_realized_pnl_toman - engine.total_fees_paid_toman
  ending_equity = engine.get_total_equity()
  net_pnl_from_equity = ending_equity - initial_capital
  assert net_pnl_from_equity == pytest.approx(net_portfolio_pnl, abs=1e-4)
  assert len(engine.positions) == 0



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
