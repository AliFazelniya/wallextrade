"""Unit tests for AI Market Regime Agent and Schema Validation."""

import pytest
from pydantic import ValidationError
from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import (
    ActionType,
    MarketFeaturesInput,
    MarketRegime,
    RegimeAnalysisOutput,
)


def test_valid_pydantic_schema_parsing():
  valid_data = {
      "symbol": "BTCTMN",
      "regime": "BULLISH_TREND",
      "confidence": 0.85,
      "volatility_state": "NORMAL",
      "recommended_action": "BUY",
      "max_suggested_allocation_pct": 10.0,
      "reasoning": "Solid trend confirmation across EMA20/50 and RSI.",
  }

  output = RegimeAnalysisOutput(**valid_data)
  assert output.regime == MarketRegime.BULLISH_TREND
  assert output.confidence == 0.85
  assert output.recommended_action == ActionType.BUY


def test_invalid_confidence_bounds_triggers_validation_error():
  invalid_data = {
      "symbol": "BTCTMN",
      "regime": "BULLISH_TREND",
      "confidence": 1.5,  # Exceeds maximum 1.0
      "volatility_state": "NORMAL",
      "recommended_action": "BUY",
      "max_suggested_allocation_pct": 10.0,
      "reasoning": "Invalid confidence test.",
  }

  with pytest.raises(ValidationError):
    RegimeAnalysisOutput(**invalid_data)


def test_deterministic_fallback_classification():
  agent = RegimeClassificationAgent(api_key=None)

  # Bullish Features
  f_bull = MarketFeaturesInput(
      symbol="BTCTMN",
      price_toman=22_000_000_000.0,
      ema_spread_pct=1.2,
      rsi_14=60.0,
      atr_pct=2.0,
      vol_ratio=1.5,
      spread_pct=0.05,
      trend_direction="BULLISH",
  )
  res_bull = agent._deterministic_fallback(f_bull)
  assert res_bull.regime == MarketRegime.BULLISH_TREND
  assert res_bull.recommended_action == ActionType.BUY

  # Panic Features (high ATR% or wide spread)
  f_panic = MarketFeaturesInput(
      symbol="BTCTMN",
      price_toman=22_000_000_000.0,
      ema_spread_pct=-2.0,
      rsi_14=25.0,
      atr_pct=7.5,  # High volatility panic
      vol_ratio=3.0,
      spread_pct=0.50,  # Wide spread
      trend_direction="BEARISH",
  )
  res_panic = agent._deterministic_fallback(f_panic)
  assert res_panic.regime == MarketRegime.VOLATILE_PANIC
  assert res_panic.recommended_action == ActionType.HOLD


@pytest.mark.asyncio
async def test_ai_agent_failure_and_timeout_handles_safely():
  from unittest.mock import AsyncMock

  agent = RegimeClassificationAgent(api_key="fake-key-for-test")
  # Mock _call_llm_agent to simulate network timeout / exception
  agent._call_llm_agent = AsyncMock(
      side_effect=TimeoutError("Gemini API call timed out after 5.0s")
  )

  f_bull = MarketFeaturesInput(
      symbol="BTCTMN",
      price_toman=22_000_000_000.0,
      ema_spread_pct=1.0,
      rsi_14=60.0,
      atr_pct=2.0,
      vol_ratio=1.3,
      spread_pct=0.05,
      trend_direction="BULLISH",
  )

  # Agent must not crash! It must gracefully return the deterministic fallback
  res = await agent.classify_regime(f_bull)
  assert res is not None
  assert res.regime == MarketRegime.BULLISH_TREND
  assert res.recommended_action == ActionType.BUY

