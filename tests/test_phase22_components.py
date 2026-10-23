"""Automated tests for Phase 22 components and experimental framework."""

from __future__ import annotations

import math
import numpy as np
import pandas as pd
import pytest

from src.experimental.features import (
    compute_adx,
    compute_donchian,
    extract_advanced_features,
)
from src.experimental.simulation_harness import (
    CompetitionSimulator,
    CompetitionSummary,
    WindowResult,
)
from src.experimental.audit_phase22 import (
    student_t_pdf,
    student_t_cdf,
    simulate_candidate_e,
    load_all_assets,
)
from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import MarketFeaturesInput, MarketRegime


def create_synthetic_bars(n_bars: int = 100, trend: float = 0.001) -> pd.DataFrame:
    """Generates synthetic price bars for unit testing."""
    times = pd.date_range("2026-08-01", periods=n_bars, freq="15min", tz="UTC")
    base_p = 50_000_000.0
    prices = [base_p * (1.0 + trend * i + 0.002 * np.sin(i / 5.0)) for i in range(n_bars)]
    highs = [p * 1.005 for p in prices]
    lows = [p * 0.995 for p in prices]
    closes = prices
    volumes = [1.0 + 0.1 * (i % 5) for i in range(n_bars)]
    
    return pd.DataFrame({
        "timestamp": [str(t) for t in times],
        "dt": times,
        "open": closes,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


def test_adx_indicator_computation():
    df = create_synthetic_bars(80, trend=0.005)
    adx = compute_adx(df, 14)
    assert len(adx) == len(df)
    assert isinstance(adx, pd.Series)
    assert not adx.isna().any()
    assert (adx >= 0.0).all() and (adx <= 100.0).all()


def test_donchian_channels_computation():
    df = create_synthetic_bars(60)
    high, low = compute_donchian(df, 20)
    assert len(high) == len(df)
    assert len(low) == len(df)
    assert (high >= low).all()


def test_extract_advanced_features_expanding_spread():
    df = create_synthetic_bars(100)
    out = extract_advanced_features(df)
    assert "adx_14" in out.columns
    assert "dc_high_20" in out.columns
    assert "dc_low_20" in out.columns
    assert "dynamic_spread" in out.columns
    assert not out["dynamic_spread"].isna().any()
    assert (out["dynamic_spread"] >= 0.06).all()
    assert (out["dynamic_spread"] <= 0.35).all()


def test_student_t_distribution_functions():
    # Symmetry at t=0
    assert abs(student_t_cdf(0.0, 13) - 0.5) < 1e-4
    # t=1.199 on df=13: two-tailed p-value should be approx 0.252 (cdf approx 0.874)
    cdf_val = student_t_cdf(1.199, 13)
    assert 0.86 < cdf_val < 0.89
    two_tail_p = 2.0 * (1.0 - cdf_val)
    assert 0.24 < two_tail_p < 0.27  # Proves t=1.199 has p ~ 25% (NOT statistically significant)


def test_simulation_harness_accounting_and_wind_down():
    df = create_synthetic_bars(300, trend=0.001)
    df_feat = extract_advanced_features(df)
    sim = CompetitionSimulator(
        df_feat,
        maker_fee=0.0025,
        taker_fee=0.0030,
        slippage_pct=0.15,
        initial_capital=5_000_000.0,
        warmup_bars=10,
        window_hours=24.0,
    )

    def dummy_signal(df_slice, idx, elapsed_h, open_pos, ctx):
        if elapsed_h < 5.0 and open_pos is None:
            return {"action": "BUY", "notional_toman": 500_000.0, "is_maker": False}
        return None

    def dummy_exit(pos, bar, elapsed_h, ctx):
        if elapsed_h >= 10.0:
            return {"reason": "TIME_EXIT", "is_maker": True, "price_override": float(bar["close"])}
        return None

    summary = sim.evaluate_strategy("DummyTest", dummy_signal, dummy_exit)
    assert isinstance(summary, CompetitionSummary)
    assert summary.total_windows > 0
    assert summary.initial_capital == 5_000_000.0 if hasattr(summary, "initial_capital") else True
    assert summary.total_friction_toman >= 0.0


def test_candidate_e_ai_gated_execution():
    """Verifies that Candidate E with AI agent gating produces valid accounting and passes cleanly."""
    btc, eth, sol, common_idx = load_all_assets(clean_lookahead=True)
    # Run on first 3 windows to verify rapid execution and valid ledger
    t_3w = common_idx[60 + 288 * 3 + 10]
    sub_idx = common_idx[common_idx <= t_3w]

    df_res, trades = simulate_candidate_e(btc, eth, sol, sub_idx, use_ai_agent=True)
    assert len(df_res) >= 2
    for w in df_res.itertuples():
        assert w.pnl == pytest.approx((w.ret / 100.0) * 5_000_000.0, rel=1e-3)
        assert w.fees >= 0.0
        assert w.slip >= 0.0
