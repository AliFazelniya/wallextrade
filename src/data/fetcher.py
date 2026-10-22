"""Market Data Fetcher and Quality Validation Pipeline."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from src.data.client import WallexClient

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
  """Raised when incoming market data fails validation."""


class MarketDataFetcher:
  """Fetches and normalizes market data from Wallex API."""

  def __init__(self, client: WallexClient):
    self.client = client

  async def fetch_ohlcv_dataframe(
      self,
      symbol: str,
      resolution: str = "15",
      from_ts: int = 0,
      to_ts: int = 0,
  ) -> pd.DataFrame:
    """Fetches UDF history and returns a clean, validated pandas DataFrame.

    Columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    """
    data = await self.client.get_udf_history(symbol, resolution, from_ts, to_ts)

    if data.get("s") != "ok":
      logger.warning(
          "UDF history returned status '%s' for symbol %s",
          data.get("s"),
          symbol,
      )
      return pd.DataFrame(
          columns=["timestamp", "open", "high", "low", "close", "volume"]
      )

    timestamps = data.get("t", [])
    opens = data.get("o", [])
    highs = data.get("h", [])
    lows = data.get("l", [])
    closes = data.get("c", [])
    volumes = data.get("v", [])

    if not timestamps or len(timestamps) == 0:
      return pd.DataFrame(
          columns=["timestamp", "open", "high", "low", "close", "volume"]
      )

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps, unit="s"),
        "open": pd.to_numeric(opens, errors="coerce"),
        "high": pd.to_numeric(highs, errors="coerce"),
        "low": pd.to_numeric(lows, errors="coerce"),
        "close": pd.to_numeric(closes, errors="coerce"),
        "volume": pd.to_numeric(volumes, errors="coerce"),
    })

    # Data Quality Validation (Phase 4.1)
    df = self._validate_and_clean_dataframe(df, symbol)
    return df

  def _validate_and_clean_dataframe(
      self, df: pd.DataFrame, symbol: str
  ) -> pd.DataFrame:
    """Ensures chronological sorting, removes duplicates and drops NaNs."""
    initial_len = len(df)
    # Deduplicate timestamps
    df = df.drop_duplicates(subset=["timestamp"], keep="last")

    # Chronological sort
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # Drop NaNs
    df = df.dropna(subset=["open", "high", "low", "close"])

    # Sanity check: High >= Low, Close > 0
    valid_mask = (df["high"] >= df["low"]) & (df["close"] > 0)
    df = df[valid_mask].reset_index(drop=True)

    cleaned_len = len(df)
    if cleaned_len < initial_len:
      logger.info(
          "Cleaned %s candles: %d dropped out of %d",
          symbol,
          initial_len - cleaned_len,
          initial_len,
      )

    return df

  async def fetch_current_spread(self, symbol: str) -> Dict[str, float]:
    """Fetches top of the orderbook and computes the bid-ask spread."""
    depth = await self.client.get_depth(symbol)
    result = depth.get("result", {})
    asks = result.get("ask", [])
    bids = result.get("bid", [])

    if not asks or not bids:
      return {
          "bid": 0.0,
          "ask": 0.0,
          "spread_pct": 999.0,
          "bid_vol": 0.0,
          "ask_vol": 0.0,
      }

    best_ask = float(asks[0]["price"])
    best_bid = float(bids[0]["price"])
    bid_vol = float(bids[0].get("quantity", 0))
    ask_vol = float(asks[0].get("quantity", 0))

    spread_pct = (
        ((best_ask - best_bid) / best_bid * 100) if best_bid > 0 else 999.0
    )

    return {
        "bid": best_bid,
        "ask": best_ask,
        "spread_pct": round(spread_pct, 4),
        "bid_vol": bid_vol,
        "ask_vol": ask_vol,
    }
