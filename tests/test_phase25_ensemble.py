"""Automated unit tests for Phase 25 Ensemble Architecture and AI Evaluator."""

from __future__ import annotations

import math
import pandas as pd
import pytest

from src.experimental.ai_ablation_study import CostSensitiveAIEvaluator
from src.experimental.ensemble_engine import (
    prepare_multi_asset_features,
    simulate_portfolio_ensemble,
)


def test_cost_sensitive_ai_evaluator_high_edge():
    evaluator = CostSensitiveAIEvaluator(min_edge_threshold_pct=0.40)
    # Favorable bar: high ADX (32), strong volume (1.8), positive momentum (0.8%), low spread (0.10%)
    favorable_bar = pd.Series({
        "adx_14": 32.0,
        "vol_ratio": 1.8,
        "ema_spread_pct": 0.80,
        "atr_pct": 1.4,
    })
    approved, p_win, expected_edge, rationale = evaluator.evaluate_trade_opportunity(
        symbol="SOLTMN",
        source="H1_TREND",
        bar=favorable_bar,
        current_spread_pct=0.10,
        target_tp_pct=4.5,
        target_sl_pct=2.2,
        round_trip_friction_pct=0.70,
    )
    assert approved is True
    assert p_win > 0.50
    assert expected_edge >= 0.40
    assert "P(Win)=" in rationale


def test_cost_sensitive_ai_evaluator_low_edge_rejection():
    evaluator = CostSensitiveAIEvaluator(min_edge_threshold_pct=0.40)
    # Adverse bar: low ADX (16), low volume (0.8), weak momentum (-0.1%), wide spread (0.35%)
    adverse_bar = pd.Series({
        "adx_14": 16.0,
        "vol_ratio": 0.8,
        "ema_spread_pct": -0.10,
        "atr_pct": 2.2,
    })
    approved, p_win, expected_edge, rationale = evaluator.evaluate_trade_opportunity(
        symbol="BTCTMN",
        source="H1_TREND",
        bar=adverse_bar,
        current_spread_pct=0.35,
        target_tp_pct=4.5,
        target_sl_pct=2.2,
        round_trip_friction_pct=0.70,
    )
    assert approved is False
    assert expected_edge < 0.40


def test_prepare_multi_asset_features_integrity():
    btc, eth, sol, common_idx = prepare_multi_asset_features()
    assert len(common_idx) > 1000
    for df, name in [(btc, "BTC"), (eth, "ETH"), (sol, "SOL")]:
        assert "trend_1h_bullish" in df.columns
        assert "adx_14" in df.columns
        assert "ema_spread_pct" in df.columns
        assert "atr_pct" in df.columns
        assert "dynamic_spread" in df.columns
        # Verify no NaN in critical feature columns for common index
        df_common = df.loc[common_idx]
        assert not df_common["trend_1h_bullish"].isna().any()
        assert not df_common["dynamic_spread"].isna().any()


def test_simulate_portfolio_ensemble_short_horizon():
    btc, eth, sol, common_idx = prepare_multi_asset_features()
    # Test on a small 3-window slice for rapid regression testing
    sub_idx = common_idx[: 60 + 288 * 3 + 10]
    res = simulate_portfolio_ensemble(
        btc, eth, sol, sub_idx,
        enable_h1=True, enable_h3=True,
        ensemble_name="Test Model C",
    )
    assert "pnl" in res
    assert "mean_ret" in res
    assert "df_res" in res
    assert "trades_list" in res
    assert len(res["df_res"]) >= 2
    assert "friction" in res
