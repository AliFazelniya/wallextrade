"""Abstract Base Class for Trading Strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd
from src.agents.schemas import ProposedTradeSignal, RegimeAnalysisOutput


class BaseStrategy(ABC):
  """Abstract interface for algorithmic trading strategies."""

  @abstractmethod
  def generate_signal(
      self,
      symbol: str,
      df_features: pd.DataFrame,
      regime_output: RegimeAnalysisOutput,
      current_price_toman: float,
      spread_pct: float,
  ) -> Optional[ProposedTradeSignal]:
    """Evaluates features and regime to return a ProposedTradeSignal or None."""
    pass
