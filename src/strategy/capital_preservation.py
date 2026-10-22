"""Defensive Capital Preservation Strategy.

Default stance is 100% Toman cash (zero drawdown, zero transaction fees).
Only deploys capital under exceptional, high-probability market regimes.
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


class CapitalPreservationStrategy(BaseStrategy):
  """Defensive capital preservation strategy prioritizing cash protection."""

  def __init__(
      self,
      min_confidence: float = 0.85,
      max_order_toman: float = 250_000.0,
      stop_loss_pct: float = 1.5,
      take_profit_pct: float = 2.8,
      max_spread_pct: float = 0.15,
      min_vol_ratio: float = 2.0,
  ):
    self.min_confidence = min_confidence
    self.max_order_toman = max_order_toman
    self.stop_loss_pct = stop_loss_pct
    self.take_profit_pct = take_profit_pct
    self.max_spread_pct = max_spread_pct
    self.min_vol_ratio = min_vol_ratio

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

    # Spread must be exceptionally tight
    if spread_pct > self.max_spread_pct:
      return None

    # Immediate exit on anything non-bullish
    if regime_output.regime != MarketRegime.BULLISH_TREND:
      return ProposedTradeSignal(
          symbol=symbol,
          action=ActionType.SELL,
          target_price_toman=current_price_toman,
          order_value_toman=0.0,
          regime=regime_output.regime,
          ai_confidence=regime_output.confidence,
          rationale=(
              f"Defensive liquidation to cash: regime is"
              f" {regime_output.regime.value}."
          ),
          timestamp=now_iso,
      )

    # Ultra-high conviction entry only
    if (
        regime_output.regime == MarketRegime.BULLISH_TREND
        and regime_output.confidence >= self.min_confidence
    ):
      ema_20 = float(latest.get("ema_20", 0.0))
      ema_50 = float(latest.get("ema_50", 0.0))
      rsi = float(latest.get("rsi_14", 50.0))
      vol_ratio = float(latest.get("vol_ratio", 1.0))
      close = float(latest.get("close", current_price_toman))

      if close > ema_20 > ema_50 and vol_ratio >= self.min_vol_ratio and 55.0 <= rsi <= 65.0:
        return ProposedTradeSignal(
            symbol=symbol,
            action=ActionType.BUY,
            target_price_toman=current_price_toman,
            order_value_toman=self.max_order_toman,
            stop_loss_price_toman=current_price_toman
            * (1.0 - (self.stop_loss_pct / 100.0)),
            take_profit_price_toman=current_price_toman
            * (1.0 + (self.take_profit_pct / 100.0)),
            regime=regime_output.regime,
            ai_confidence=regime_output.confidence,
            rationale=(
                f"Capital Preservation high-conviction entry: Conf={regime_output.confidence:.2f},"
                f" Vol={vol_ratio:.1f}x."
            ),
            timestamp=now_iso,
        )

    return None
