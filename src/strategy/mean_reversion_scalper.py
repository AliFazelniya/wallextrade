"""Mean Reversion & Bollinger Scalping Strategy for Range Markets.

Engineered for Wallex hackathon to ensure active trading and positive alpha
during sideways / calm market regimes (CALM_RANGE), buying near the lower
Bollinger Band and taking profit at the 20-period moving average.
"""

from __future__ import annotations

import datetime
import logging
from typing import Optional
import pandas as pd

from src.agents.schemas import ActionType, MarketRegime, ProposedTradeSignal, RegimeAnalysisOutput
from src.features.indicators import compute_bollinger_bands
from src.strategy.base import BaseStrategy

logger = logging.getLogger(__name__)


class MeanReversionScalperStrategy(BaseStrategy):
    """Exploits price bounces within bounded volatility bands during low-trend regimes."""

    def __init__(
        self,
        target_profit_pct: float = 1.0,
        stop_loss_pct: float = 1.0,
        max_order_toman: float = 350_000.0,
        max_spread_pct: float = 0.20,
    ):
        self.target_profit_pct = target_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_order_toman = max_order_toman
        self.max_spread_pct = max_spread_pct

    def generate_signal(
        self,
        symbol: str,
        df_features: pd.DataFrame,
        regime_output: RegimeAnalysisOutput,
        current_price_toman: float,
        spread_pct: float,
    ) -> Optional[ProposedTradeSignal]:
        """Generates a BUY signal on mean-reversion discount, or SELL on mean touch."""
        if df_features.empty or len(df_features) < 30:
            return None

        if spread_pct > self.max_spread_pct:
            return None

        # Only operates in CALM_RANGE or mild recovery
        if regime_output.regime not in (MarketRegime.CALM_RANGE,):
            return None

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        latest = df_features.iloc[-1]
        cur_p = current_price_toman

        # Compute or read Bollinger Bands
        upper = float(latest.get("bb_upper", 0.0))
        lower = float(latest.get("bb_lower", 0.0))
        middle = float(latest.get("bb_middle", 0.0))
        rsi = float(latest.get("rsi_14", 50.0))

        if upper <= 0 or lower <= 0:
            bb = compute_bollinger_bands(df_features["close"], window=20, num_std=2.0)
            upper = float(bb["bb_upper"].iloc[-1])
            lower = float(bb["bb_lower"].iloc[-1])
            middle = float(bb["bb_middle"].iloc[-1])

        # Entry condition: Price is at or below lower band, RSI <= 46
        if cur_p <= (lower * 1.002) and rsi <= 46.0:
            tp_price = middle if middle > cur_p else cur_p * (1.0 + (self.target_profit_pct / 100.0))
            sl_price = cur_p * (1.0 - (self.stop_loss_pct / 100.0))
            order_val = min(self.max_order_toman, 300_000.0)

            return ProposedTradeSignal(
                symbol=symbol,
                action=ActionType.BUY,
                target_price_toman=cur_p,
                order_value_toman=order_val,
                regime=regime_output.regime,
                ai_confidence=regime_output.confidence,
                stop_loss_toman=sl_price,
                take_profit_toman=tp_price,
                rationale=(
                    f"Mean-reversion entry: price near lower band ({cur_p:,.0f} <= {lower:,.0f}) "
                    f"with oversold RSI {rsi:.1f}. Target middle band: {middle:,.0f} TMN."
                ),
                timestamp=now_iso,
            )

        # Exit condition: Price touched middle band or upper band
        if cur_p >= middle and rsi >= 56.0:
            return ProposedTradeSignal(
                symbol=symbol,
                action=ActionType.SELL,
                target_price_toman=cur_p,
                order_value_toman=0.0,  # sell inventory
                regime=regime_output.regime,
                ai_confidence=regime_output.confidence,
                rationale=f"Mean-reversion take-profit: price reached SMA20 mean ({cur_p:,.0f} >= {middle:,.0f}) with RSI {rsi:.1f}.",
                timestamp=now_iso,
            )

        return None
