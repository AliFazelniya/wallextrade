"""Primary Quantitative Strategy: Regime-Aware Momentum Filter."""

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


class RegimeMomentumStrategy(BaseStrategy):
  """Regime-Aware Trend/Momentum Strategy with Volatility and Spread Filters."""

  def __init__(
      self,
      min_confidence: float = 0.70,
      max_order_toman: float = 500_000.0,
      stop_loss_pct: float = 2.0,
      take_profit_pct: float = 3.5,
      max_spread_pct: float = 0.35,
  ):
    self.min_confidence = min_confidence
    self.max_order_toman = max_order_toman
    self.stop_loss_pct = stop_loss_pct
    self.take_profit_pct = take_profit_pct
    self.max_spread_pct = max_spread_pct

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
      logger.info(
          "Spread too wide (%.3f%% > %.3f%%) for %s. No signal generated.",
          spread_pct,
          self.max_spread_pct,
          symbol,
      )
      return None

    # Exit Signal Check (if Bearish or Panic)
    if regime_output.regime in (
        MarketRegime.BEARISH_TREND,
        MarketRegime.VOLATILE_PANIC,
    ):
      return ProposedTradeSignal(
          symbol=symbol,
          action=ActionType.SELL,
          target_price_toman=current_price_toman,
          order_value_toman=0.0,  # Sell all active inventory
          regime=regime_output.regime,
          ai_confidence=regime_output.confidence,
          rationale=(
              f"Exit signal: AI classified regime as {regime_output.regime.value}."
          ),
          timestamp=now_iso,
      )

    # Entry Signal Check (Bullish Momentum)
    if (
        regime_output.regime == MarketRegime.BULLISH_TREND
        and regime_output.confidence >= self.min_confidence
    ):
      ema_20 = latest.get("ema_20", 0.0)
      ema_50 = latest.get("ema_50", 0.0)
      rsi = latest.get("rsi_14", 50.0)
      vol_ratio = latest.get("vol_ratio", 1.0)

      # Deterministic mathematical validation
      if ema_20 > ema_50 and (50.0 <= rsi <= 69.0) and vol_ratio >= 1.10:
        # Volatility sizing: calculate stop loss and take profit
        sl_price = current_price_toman * (1.0 - (self.stop_loss_pct / 100.0))
        tp_price = current_price_toman * (1.0 + (self.take_profit_pct / 100.0))

        order_val = min(
            self.max_order_toman,
            5_000_000.0 * (regime_output.max_suggested_allocation_pct / 100.0),
        )

        return ProposedTradeSignal(
            symbol=symbol,
            action=ActionType.BUY,
            target_price_toman=current_price_toman,
            order_value_toman=order_val,
            regime=regime_output.regime,
            ai_confidence=regime_output.confidence,
            stop_loss_toman=sl_price,
            take_profit_toman=tp_price,
            rationale=(
                f"Bullish trend confirmed (EMA20 > EMA50, RSI {rsi:.1f},"
                f" VolRatio {vol_ratio:.2f}x). Confidence"
                f" {regime_output.confidence:.0%}."
            ),
            timestamp=now_iso,
        )

    return None
