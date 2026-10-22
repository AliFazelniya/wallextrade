"""Market Regime Classification Agent.

Responsible for analyzing quantitative features, classifying the market regime
with confidence scores, and providing structured explanations. Supports both
LLM-based classification (via Google Gemini or OpenAI API) and a robust
deterministic fallback.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
import httpx
from src.agents.schemas import (
    ActionType,
    MarketFeaturesInput,
    MarketRegime,
    RegimeAnalysisOutput,
)

logger = logging.getLogger(__name__)


class RegimeClassificationAgent:
  """Agent that classifies market regimes with structured outputs."""

  def __init__(
      self,
      api_key: Optional[str] = None,
      model: str = "gemini-2.5-flash",
      timeout_seconds: float = 5.0,
  ):
    self.api_key = api_key
    self.model = model
    self.timeout = timeout_seconds

  async def classify_regime(
      self, features: MarketFeaturesInput
  ) -> RegimeAnalysisOutput:
    """Classifies the market regime for a given symbol and feature vector.

    If LLM API is available and responds within timeout, parses structured output.
    Otherwise, automatically falls back to deterministic rule-based
    classification.
    """
    if self.api_key:
      try:
        return await self._call_llm_agent(features)
      except Exception as exc:
        logger.warning(
            "LLM Agent call failed (%s). Activating deterministic fallback.",
            exc,
        )

    # Safe Deterministic Fallback
    return self._deterministic_fallback(features)

  def _deterministic_fallback(
      self, f: MarketFeaturesInput
  ) -> RegimeAnalysisOutput:
    """High-reliability deterministic classification based on statistical features."""
    # 1. Extreme volatility check
    if f.atr_pct > 6.0 or f.spread_pct > 0.40:
      return RegimeAnalysisOutput(
          symbol=f.symbol,
          regime=MarketRegime.VOLATILE_PANIC,
          confidence=0.90,
          volatility_state="HIGH/PANIC",
          recommended_action=ActionType.HOLD,
          max_suggested_allocation_pct=0.0,
          reasoning=(
              f"ATR% is abnormally elevated ({f.atr_pct:.2f}%) or spread is"
              f" wide ({f.spread_pct:.2f}%). Volatile panic regime active."
          ),
      )

    # 2. Bullish Trend check
    if f.ema_spread_pct > 0.4 and 52 <= f.rsi_14 <= 68 and f.vol_ratio >= 1.15:
      return RegimeAnalysisOutput(
          symbol=f.symbol,
          regime=MarketRegime.BULLISH_TREND,
          confidence=0.85,
          volatility_state="NORMAL",
          recommended_action=ActionType.BUY,
          max_suggested_allocation_pct=10.0,
          reasoning=(
              f"Positive EMA divergence (+{f.ema_spread_pct:.2f}%), solid RSI"
              f" ({f.rsi_14:.1f}) and volume surge ({f.vol_ratio:.2f}x)."
          ),
      )

    # 3. Bearish Trend check
    if f.ema_spread_pct < -0.4 and f.rsi_14 < 48:
      return RegimeAnalysisOutput(
          symbol=f.symbol,
          regime=MarketRegime.BEARISH_TREND,
          confidence=0.85,
          volatility_state="NORMAL",
          recommended_action=ActionType.SELL,
          max_suggested_allocation_pct=0.0,
          reasoning=(
              f"Negative EMA divergence ({f.ema_spread_pct:.2f}%) and weak RSI"
              f" ({f.rsi_14:.1f}). Bearish trend detected; capital"
              " preservation active."
          ),
      )

    # 4. Calm Range check
    return RegimeAnalysisOutput(
        symbol=f.symbol,
        regime=MarketRegime.CALM_RANGE,
        confidence=0.75,
        volatility_state="LOW",
        recommended_action=ActionType.HOLD,
        max_suggested_allocation_pct=5.0,
        reasoning=(
            "Price moving within flat EMA bands"
            f" ({f.ema_spread_pct:.2f}%) and neutral RSI ({f.rsi_14:.1f})."
            " Ranging market."
        ),
    )

  async def _call_llm_agent(
      self, f: MarketFeaturesInput
  ) -> RegimeAnalysisOutput:
    """Calls Gemini API with structured JSON output schema."""
    system_prompt = (
        "You are an expert quantitative crypto analyst for a 3-day trading"
        " competition. "
        "Classify the market regime based on input features and return strict"
        " JSON matching the schema. "
        "Regimes: BULLISH_TREND, BEARISH_TREND, CALM_RANGE, VOLATILE_PANIC. "
        "Be conservative with capital."
    )

    prompt = (
        f"Symbol: {f.symbol}\n"
        f"Price: {f.price_toman:,.0f} TMN\n"
        f"EMA 20/50 Spread: {f.ema_spread_pct:+.2f}%\n"
        f"RSI (14): {f.rsi_14:.1f}\n"
        f"ATR%: {f.atr_pct:.2f}%\n"
        f"Volume Ratio (vs 20SMA): {f.vol_ratio:.2f}x\n"
        f"Orderbook Spread: {f.spread_pct:.3f}%\n"
        f"Trend: {f.trend_direction}\n"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1,
        },
    }

    async with httpx.AsyncClient(timeout=self.timeout) as client:
      resp = await client.post(url, json=payload)
      if resp.status_code != 200:
        raise ValueError(
            f"Gemini API returned {resp.status_code}: {resp.text[:200]}"
        )
      data = resp.json()
      raw_text = (
          data.get("candidates", [{}])[0]
          .get("content", {})
          .get("parts", [{}])[0]
          .get("text", "{}")
      )
      parsed = json.loads(raw_text)
      return RegimeAnalysisOutput(**parsed)
