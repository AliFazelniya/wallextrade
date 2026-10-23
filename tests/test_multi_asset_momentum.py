"""Unit tests for productionized MultiAssetMomentumStrategy (Phase 23)."""

from __future__ import annotations

import datetime
import numpy as np
import pandas as pd
import pytest

from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import ActionType, MarketRegime, ProposedTradeSignal, RegimeAnalysisOutput
from src.strategy.multi_asset_momentum import MultiAssetMomentumStrategy


def create_feature_candle(
    close: float = 20_000_000.0,
    ema_20: float = 20_400_000.0,
    ema_50: float = 19_800_000.0,
    rsi: float = 58.0,
    vol_ratio: float = 1.35,
    adx: float = 26.0,
    atr_pct: float = 1.4,
) -> pd.DataFrame:
    rows = []
    base_time = pd.Timestamp("2026-08-01 10:00:00", tz="UTC")
    for i in range(40):
        t = base_time + pd.Timedelta(minutes=15 * i)
        rows.append({
            "timestamp": str(t),
            "dt": t,
            "open": close * 0.999,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": 2.0,
            "ema_20": ema_20,
            "ema_50": ema_50,
            "ema_spread_pct": ((ema_20 - ema_50) / ema_50) * 100.0,
            "rsi_14": rsi,
            "vol_ratio": vol_ratio,
            "adx_14": adx,
            "atr_pct": atr_pct,
            "dynamic_spread": 0.10,
        })
    return pd.DataFrame(rows)


def test_strategy_instantiation():
    strat = MultiAssetMomentumStrategy()
    assert strat.take_profit_pct == 3.2
    assert strat.stop_loss_pct == 1.5
    assert strat.max_spread_pct == 0.18
    assert "BTCTMN" in strat.allowed_symbols


def test_asset_score_bullish_qualification():
    strat = MultiAssetMomentumStrategy()
    df_feat = create_feature_candle()
    eligible, score, reg_out = strat.compute_asset_score("BTCTMN", df_feat, current_spread_pct=0.10)
    assert eligible is True
    assert score >= 1.0
    assert reg_out is not None
    assert reg_out.regime == MarketRegime.BULLISH_TREND


def test_asset_score_rejection_on_wide_spread():
    strat = MultiAssetMomentumStrategy()
    df_feat = create_feature_candle()
    eligible, score, reg_out = strat.compute_asset_score("BTCTMN", df_feat, current_spread_pct=0.25)
    assert eligible is False
    assert score == 0.0


def test_rank_cross_sectional_candidates():
    strat = MultiAssetMomentumStrategy()
    df_btc = create_feature_candle(close=20_000_000.0, ema_20=20_200_000.0, ema_50=19_800_000.0)
    df_eth = create_feature_candle(close=600_000.0, ema_20=601_000.0, ema_50=599_000.0)

    market_data = {
        "BTCTMN": (df_btc, 20_000_000.0, 0.10),
        "ETHTMN": (df_eth, 600_000.0, 0.12),
    }

    ranked = strat.rank_cross_sectional_candidates(market_data)
    assert len(ranked) >= 1
    # BTC has higher ema spread, should rank first
    assert ranked[0][1] == "BTCTMN"
    assert ranked[0][0] > 1.0


def test_generate_signal():
    strat = MultiAssetMomentumStrategy()
    df_feat = create_feature_candle()
    reg_out = RegimeAnalysisOutput(
        symbol="BTCTMN",
        regime=MarketRegime.BULLISH_TREND,
        confidence=0.85,
        volatility_state="NORMAL",
        recommended_action=ActionType.BUY,
        max_suggested_allocation_pct=10.0,
        reasoning="Strong momentum",
    )
    sig = strat.generate_signal("BTCTMN", df_feat, reg_out, 20_000_000.0, 0.10)
    assert isinstance(sig, ProposedTradeSignal)
    assert sig.symbol == "BTCTMN"
    assert sig.action == ActionType.BUY
    assert sig.order_value_toman == 500_000.0


def test_evaluate_exit_conditions():
    strat = MultiAssetMomentumStrategy()

    # 1. Take Profit (+3.5% vs entry -> trigger TP)
    tp_exit = strat.evaluate_exit("BTCTMN", current_price_toman=103.5, avg_entry_price=100.0, elapsed_hours_in_window=20.0)
    assert tp_exit is not None
    assert tp_exit["reason"] == "TAKE_PROFIT"
    assert tp_exit["is_maker"] is True

    # 2. Stop Loss (-1.6% vs entry -> trigger SL)
    sl_exit = strat.evaluate_exit("BTCTMN", current_price_toman=98.4, avg_entry_price=100.0, elapsed_hours_in_window=20.0)
    assert sl_exit is not None
    assert sl_exit["reason"] == "STOP_LOSS"
    assert sl_exit["is_maker"] is False

    # 3. Graceful Wind-down at hour 67 with +0.8% profit
    wd_exit = strat.evaluate_exit("BTCTMN", current_price_toman=100.8, avg_entry_price=100.0, elapsed_hours_in_window=67.0)
    assert wd_exit is not None
    assert wd_exit["reason"] == "GRACEFUL_PASSIVE_WIND_DOWN"
    assert wd_exit["is_maker"] is True

    # 4. Hold condition: hour 40 with +0.8% profit (TP not hit, Wind-down not reached)
    hold = strat.evaluate_exit("BTCTMN", current_price_toman=100.8, avg_entry_price=100.0, elapsed_hours_in_window=40.0)
    assert hold is None
