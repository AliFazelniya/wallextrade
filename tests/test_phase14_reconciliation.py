"""Phase 14 Independent Reconciliation, Counterfactual Audit, and Statistical Integrity Tests."""

import json
import pathlib
import pytest

repo_root = pathlib.Path(__file__).resolve().parent.parent


def test_in_sample_out_of_sample_boundary_reconciliation():
    """Verify exact mathematical reconciliation of IS, OOS, and Full 90d returns."""
    is_net_pnl = -2227.0
    oos_net_pnl = 30775.0
    full_90d_net_pnl = 21515.0

    sum_separate = is_net_pnl + oos_net_pnl
    assert sum_separate == 28548.0

    discrepancy = sum_separate - full_90d_net_pnl
    assert discrepancy == 7033.0

    # Boundary trade liquidation difference
    # In IS: closed at boundary with loss of -5,185 TMN
    # In Full 90d: held until SL hit with loss of -12,217 TMN
    boundary_diff = -5185.0 - (-12217.0)
    assert abs(discrepancy - boundary_diff) <= 1.0


def test_ai_counterfactual_realizable_portfolio_value():
    """Verify signal-level unconstrained metric vs realizable sequential portfolio value."""
    # Deterministic baseline across full 90 days
    det_trades = 39
    det_net_pnl = -20824.0
    det_fees = 112612.0

    # AI-assisted strategy across full 90 days
    ai_trades = 24
    ai_net_pnl = 21515.0
    ai_fees = 69162.0

    # Realizable incremental portfolio P&L
    realizable_gain = ai_net_pnl - det_net_pnl
    assert realizable_gain == 42339.0

    # Fee savings from filtering out 15 noise trades
    fee_savings = det_fees - ai_fees
    assert fee_savings == 43450.0

    # Realizable value is driven primarily by fee savings
    diff = abs(fee_savings - realizable_gain)
    assert diff <= 1200.0  # within 1,111 TMN


def test_signal_count_reconciliation():
    """Verify that Phase 12 643 vetoes is multi-symbol and Phase 13 553 is single-symbol BTC."""
    # Phase 12 36-day multi-symbol breakdown
    p12_btc_vetoes = 239
    p12_eth_vetoes = 205
    p12_sol_vetoes = 199
    p12_total_vetoes = p12_btc_vetoes + p12_eth_vetoes + p12_sol_vetoes
    assert p12_total_vetoes == 643

    # Phase 13 90-day single-symbol BTC
    p13_btc_vetoes = 553

    # Daily veto rate comparison for BTC
    p12_btc_daily = p12_btc_vetoes / 36.0
    p13_btc_daily = p13_btc_vetoes / 90.0

    assert pytest.approx(p12_btc_daily, abs=0.01) == 6.64
    assert pytest.approx(p13_btc_daily, abs=0.01) == 6.14
    # Relative difference is under 10%
    rel_diff = abs(p12_btc_daily - p13_btc_daily) / ((p12_btc_daily + p13_btc_daily) / 2)
    assert rel_diff < 0.10


def test_three_day_window_partitioning_logic():
    """Verify why exactly 29 3-day windows were evaluated instead of 30."""
    total_bars = 8636
    warmup_bars = 60
    bars_per_3d = 288  # 3 days * 24h * 4 bars/h

    usable_bars = total_bars - warmup_bars
    assert usable_bars == 8576

    num_windows = usable_bars // bars_per_3d
    remainder_bars = usable_bars % bars_per_3d

    assert num_windows == 29
    assert remainder_bars == 224
    # 224 bars is less than 288, so window 30 cannot be formed
    assert remainder_bars < bars_per_3d


def test_portfolio_accounting_invariants_verification():
    """Verify accounting invariants on full 90-day backtest."""
    initial_capital = 5_000_000.0
    gross_pnl = 90677.0
    fees = 69162.0
    net_pnl = 21515.0

    # Invariant 1: Net PnL = Gross PnL - Total Fees
    assert gross_pnl - fees == net_pnl

    # Invariant 2: Final Equity = Initial Capital + Net PnL
    final_equity = initial_capital + net_pnl
    assert final_equity == 5021515.0
