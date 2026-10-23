"""Selective Breakout & Momentum Strategy.

Engineered to overcome high exchange friction (Maker 0.25%, Taker 0.30%, slippage 0.15%)
by taking only high-conviction momentum breakout setups with favorable R:R (> 1.9).
"""

from __future__ import annotations

import datetime
import logging
from typing import Optional
import pandas as pd
from src.agents.schemas import (
    ActionType,
    MarketRegime,
    ProposedTradeSignal,
    RegimeAnalysisOutput,
)
from src.strategy.base import BaseStrategy

logger = logging.getLogger(__name__)


class SelectiveMomentumStrategy(BaseStrategy):
  """High-conviction, low-turnover momentum breakout strategy."""

  def __init__(
      self,
      min_confidence: float = 0.75,
      max_order_toman: float = 500_000.0,
      stop_loss_pct: float = 1.8,
      take_profit_pct: float = 3.6,
      max_spread_pct: float = 0.25,
      min_vol_ratio: float = 1.6,
      min_ema_spread_pct: float = 0.20,
      min_atr_pct: float = 1.0,
  ):
    self.min_confidence = min_confidence
    self.max_order_toman = max_order_toman
    self.stop_loss_pct = stop_loss_pct
    self.take_profit_pct = take_profit_pct
    self.max_spread_pct = max_spread_pct
    self.min_vol_ratio = min_vol_ratio
    self.min_ema_spread_pct = min_ema_spread_pct
    self.min_atr_pct = min_atr_pct

  def generate_signal(
      self,
      symbol: str,
      df_features: pd.DataFrame,
      regime_output: RegimeAnalysisOutput,
      current_price_toman: float,
      spread_pct: float,
  ) -> Optional[ProposedTradeSignal]:
    if df_features.empty or len(df_features) < 30:
      return None

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    latest = df_features.iloc[-1]

    # Pre-condition: Tight spread filter
    if spread_pct > self.max_spread_pct:
      return None

    # Immediate Exit on Bearish or Panic regime
    if regime_output.regime in (
        MarketRegime.BEARISH_TREND,
        MarketRegime.VOLATILE_PANIC,
    ):
      return ProposedTradeSignal(
          symbol=symbol,
          action=ActionType.SELL,
          target_price_toman=current_price_toman,
          order_value_toman=0.0,
          regime=regime_output.regime,
          ai_confidence=regime_output.confidence,
          rationale=(
              f"Exit signal: adverse regime {regime_output.regime.value}."
          ),
          timestamp=now_iso,
      )

    # Entry Filter: Only in verified BULLISH_TREND with high confidence
    if (
        regime_output.regime == MarketRegime.BULLISH_TREND
        and regime_output.confidence >= self.min_confidence
    ):
      ema_20 = float(latest.get("ema_20", 0.0))
      ema_50 = float(latest.get("ema_50", 0.0))
      ema_spread = float(latest.get("ema_spread_pct", 0.0))
      rsi = float(latest.get("rsi_14", 50.0))
      vol_ratio = float(latest.get("vol_ratio", 1.0))
      atr_pct = float(latest.get("atr_pct", 0.0))
      close = float(latest.get("close", current_price_toman))

      # Strict quantitative conditions:
      # 1. Close above EMA20 and EMA20 above EMA50
      # 2. Significant EMA spread expansion
      # 3. Volume surge
      # 4. Volatility sufficient to cover fees
      # 5. RSI indicates momentum but not overbought exhaustion
      if (
          close >= ema_20 > ema_50
          and ema_spread >= self.min_ema_spread_pct
          and vol_ratio >= self.min_vol_ratio
          and atr_pct >= self.min_atr_pct
          and 52.0 <= rsi <= 68.0
      ):
        order_val = min(
            self.max_order_toman,
            5_000_000.0 * (regime_output.max_suggested_allocation_pct / 100.0),
        )
        return ProposedTradeSignal(
            symbol=symbol,
            action=ActionType.BUY,
            target_price_toman=current_price_toman,
            order_value_toman=order_val,
            stop_loss_price_toman=current_price_toman
            * (1.0 - (self.stop_loss_pct / 100.0)),
            take_profit_price_toman=current_price_toman
            * (1.0 + (self.take_profit_pct / 100.0)),
            regime=regime_output.regime,
            ai_confidence=regime_output.confidence,
            rationale=(
                f"Selective Breakout: VolRatio={vol_ratio:.2f},"
                f" EMASpread={ema_spread:.2f}%, ATR={atr_pct:.2f}%,"
                f" RSI={rsi:.1f}."
            ),
            timestamp=now_iso,
        )

    return None
