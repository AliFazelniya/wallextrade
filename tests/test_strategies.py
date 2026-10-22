"""Unit tests for Candidate Strategies."""

import pandas as pd
import pytest
from src.agents.schemas import ActionType, MarketRegime, RegimeAnalysisOutput
from src.strategy.capital_preservation import CapitalPreservationStrategy
from src.strategy.mean_reversion import MeanReversionStrategy
from src.strategy.selective_momentum import SelectiveMomentumStrategy


def test_mean_reversion_strategy_signals():
  dates = pd.date_range("2026-10-01", periods=40, freq="15min")
  df = pd.DataFrame({
      "timestamp": dates,
      "close": [100.0] * 38 + [80.0, 75.0],
      "high": [102.0] * 38 + [82.0, 78.0],
      "low": [98.0] * 38 + [79.0, 74.0],
      "volume": [100.0] * 40,
      "rsi_14": [50.0] * 38 + [28.0, 25.0],  # Oversold RSI < 35
      "bb_lower": [95.0] * 38 + [85.0, 82.0],
      "bb_mid": [100.0] * 40,
      "bb_upper": [105.0] * 40,
      "bb_pct_b": [0.5] * 38 + [0.02, 0.01],
  })

  strategy = MeanReversionStrategy(rsi_oversold_threshold=35.0)

  regime_ranging = RegimeAnalysisOutput(
      symbol="BTCTMN",
      regime=MarketRegime.CALM_RANGE,
      confidence=0.80,
      volatility_state="LOW",
      recommended_action=ActionType.HOLD,
      max_suggested_allocation_pct=10.0,
      reasoning="Ranging market",
  )

  sig = strategy.generate_signal(
      symbol="BTCTMN",
      df_features=df,
      regime_output=regime_ranging,
      current_price_toman=75.0,
      spread_pct=0.05,
  )

  assert sig is not None
  assert sig.action == ActionType.BUY
  assert sig.order_value_toman > 0


def test_selective_momentum_strategy_signals():
  dates = pd.date_range("2026-10-01", periods=40, freq="15min")
  df = pd.DataFrame({
      "timestamp": dates,
      "close": [100.0 + i * 2.0 for i in range(40)],
      "high": [102.0 + i * 2.0 for i in range(40)],
      "low": [98.0 + i * 2.0 for i in range(40)],
      "volume": [100.0] * 39 + [300.0],  # Volume surge 3.0x
      "ema_20": [100.0 + i * 1.8 for i in range(40)],
      "ema_50": [100.0 + i * 1.0 for i in range(40)],
      "ema_spread_pct": [0.5] * 40,
      "rsi_14": [60.0] * 40,  # 52 <= rsi <= 68
      "atr_pct": [1.5] * 40,
      "vol_ratio": [1.0] * 39 + [2.5],
  })

  strategy = SelectiveMomentumStrategy(min_confidence=0.75)

  regime_bullish = RegimeAnalysisOutput(
      symbol="BTCTMN",
      regime=MarketRegime.BULLISH_TREND,
      confidence=0.85,
      volatility_state="NORMAL",
      recommended_action=ActionType.BUY,
      max_suggested_allocation_pct=10.0,
      reasoning="Strong bull trend",
  )

  sig = strategy.generate_signal(
      symbol="BTCTMN",
      df_features=df,
      regime_output=regime_bullish,
      current_price_toman=180.0,
      spread_pct=0.05,
  )

  assert sig is not None
  assert sig.action == ActionType.BUY
  assert sig.order_value_toman > 0


def test_capital_preservation_strategy_signals():
  dates = pd.date_range("2026-10-01", periods=40, freq="15min")
  df = pd.DataFrame({
      "timestamp": dates,
      "close": [100.0] * 40,
      "high": [102.0] * 40,
      "low": [98.0] * 40,
      "volume": [100.0] * 40,
      "rsi_14": [50.0] * 40,
      "vol_ratio": [1.0] * 40,
  })

  strategy = CapitalPreservationStrategy(min_confidence=0.85)

  # Non-bullish regime -> Should NOT buy
  regime_ranging = RegimeAnalysisOutput(
      symbol="BTCTMN",
      regime=MarketRegime.CALM_RANGE,
      confidence=0.80,
      volatility_state="LOW",
      recommended_action=ActionType.HOLD,
      max_suggested_allocation_pct=0.0,
      reasoning="Ranging",
  )

  sig = strategy.generate_signal(
      symbol="BTCTMN",
      df_features=df,
      regime_output=regime_ranging,
      current_price_toman=100.0,
      spread_pct=0.05,
  )
  assert sig is not None
  assert sig.action == ActionType.SELL  # Cash preservation: exit/stay in cash
