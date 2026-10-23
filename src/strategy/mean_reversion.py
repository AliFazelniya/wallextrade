"""Mean Reversion Quantitative Strategy for Range-Bound Regimes."""

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


class MeanReversionStrategy(BaseStrategy):
  """Mean-Reversion strategy using Bollinger Bands and RSI in ranging regimes."""

  def __init__(
      self,
      min_confidence: float = 0.65,
      max_order_toman: float = 500_000.0,
      stop_loss_pct: float = 2.0,
      take_profit_pct: float = 2.5,
      max_spread_pct: float = 0.35,
      rsi_oversold_threshold: float = 35.0,
  ):
    self.min_confidence = min_confidence
    self.max_order_toman = max_order_toman
    self.stop_loss_pct = stop_loss_pct
    self.take_profit_pct = take_profit_pct
    self.max_spread_pct = max_spread_pct
    self.rsi_oversold_threshold = rsi_oversold_threshold

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

    # Pre-condition: Spread check
    if spread_pct > self.max_spread_pct:
      return None

    # Exit on Bearish or Panic
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

    # Entry: In CALM_RANGE (or range-bound market) when price is oversold
    rsi = float(latest.get("rsi_14", 50.0))
    bb_pct_b = float(latest.get("bb_pct_b", 0.5))
    close = float(latest.get("close", current_price_toman))
    bb_lower = float(latest.get("bb_lower", 0.0))

    is_ranging = regime_output.regime == MarketRegime.CALM_RANGE
    is_oversold = (rsi <= self.rsi_oversold_threshold) or (
        bb_pct_b <= 0.05 and bb_lower > 0
    )

    if (
        is_ranging
        and is_oversold
        and regime_output.confidence >= self.min_confidence
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
              f"Mean Reversion entry: RSI={rsi:.1f}, %B={bb_pct_b:.2f} in"
              f" {regime_output.regime.value}."
          ),
          timestamp=now_iso,
      )

    return None
