"""Market Data Fetcher, Resampler, and Data Quality Auditor."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from src.data.client import WallexClient

logger = logging.getLogger(__name__)


class DataQualityAudit(dict):
  """Container for market data audit results."""


class MarketDataFetcher:
  """Fetches, audits, and normalizes market data from Wallex API."""

  def __init__(self, client: WallexClient):
    self.client = client

  async def fetch_ohlcv_dataframe(
      self,
      symbol: str,
      resolution: str = "15",
      from_ts: int = 0,
      to_ts: int = 0,
      auto_resample_to_true_timeframe: bool = True,
  ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Fetches UDF history, audits data quality, and optionally resamples to true timeframe.

    Returns:
        (df_cleaned, audit_metrics_dict)
    """
    MAX_CHUNK_SECONDS = 18 * 86400
    if from_ts > 0 and to_ts > from_ts and (to_ts - from_ts) > MAX_CHUNK_SECONDS:
      logger.info(
          "Requested span of %.1f days exceeds single-request limit. Paginating"
          " historical requests for %s...",
          (to_ts - from_ts) / 86400,
          symbol,
      )
      all_t, all_o, all_h, all_l, all_c, all_v = [], [], [], [], [], []
      curr = from_ts
      while curr < to_ts:
        curr_end = min(curr + MAX_CHUNK_SECONDS, to_ts)
        chunk_raw = await self.client.get_udf_history(
            symbol, resolution, curr, curr_end
        )
        if chunk_raw.get("s") == "ok":
          all_t.extend(chunk_raw.get("t", []))
          all_o.extend(chunk_raw.get("o", []))
          all_h.extend(chunk_raw.get("h", []))
          all_l.extend(chunk_raw.get("l", []))
          all_c.extend(chunk_raw.get("c", []))
          all_v.extend(chunk_raw.get("v", []))
        curr = curr_end
      raw_data = {
          "s": "ok" if all_t else "no_data",
          "t": all_t,
          "o": all_o,
          "h": all_h,
          "l": all_l,
          "c": all_c,
          "v": all_v,
      }
    else:
      raw_data = await self.client.get_udf_history(
          symbol, resolution, from_ts, to_ts
      )

    if raw_data.get("s") != "ok":
      logger.warning(
          "UDF history returned non-ok status '%s' for %s",
          raw_data.get("s"),
          symbol,
      )
      return pd.DataFrame(
          columns=["timestamp", "open", "high", "low", "close", "volume"]
      ), {}

    t = raw_data.get("t", [])
    o = raw_data.get("o", [])
    h = raw_data.get("h", [])
    l = raw_data.get("l", [])
    c = raw_data.get("c", [])
    v = raw_data.get("v", [])

    raw_count = len(t)
    if raw_count == 0:
      return pd.DataFrame(
          columns=["timestamp", "open", "high", "low", "close", "volume"]
      ), {}

    # Raw audit
    first_ts = int(t[0])
    last_ts = int(t[-1])
    raw_step_seconds = (t[1] - t[0]) if raw_count > 1 else 0

    df_raw = pd.DataFrame({
        "timestamp": pd.to_datetime(t, unit="s", utc=True),
        "open": pd.to_numeric(o, errors="coerce"),
        "high": pd.to_numeric(h, errors="coerce"),
        "low": pd.to_numeric(l, errors="coerce"),
        "close": pd.to_numeric(c, errors="coerce"),
        "volume": pd.to_numeric(v, errors="coerce"),
    })

    # Duplicates check
    dup_count = int(df_raw.duplicated(subset=["timestamp"]).sum())
    df = self.clean_and_deduplicate_dataframe(df_raw)

    # Missing bars check (expected based on raw_step_seconds)
    missing_count = 0
    if raw_step_seconds > 0 and len(df) > 1:
      expected_bars = (
          int((df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds())
          // raw_step_seconds
      ) + 1
      missing_count = max(0, expected_bars - len(df))

    # Resampling to true target timeframe if needed (e.g. Wallex resolution=15 returns 1m bars)
    target_rule = "15min" if resolution in ("15", "15m") else f"{resolution}min"
    if (
        auto_resample_to_true_timeframe
        and resolution == "15"
        and raw_step_seconds == 60
    ):
      logger.info(
          "Resampling raw 1-minute bars into genuine 15-minute OHLCV candles"
          " for %s...",
          symbol,
      )
      df_resampled = (
          df.set_index("timestamp")
          .resample(target_rule)
          .agg({
              "open": "first",
              "high": "max",
              "low": "min",
              "close": "last",
              "volume": "sum",
          })
          .dropna()
          .reset_index()
      )
      final_df = df_resampled
    else:
      final_df = df

    audit = {
        "symbol": symbol,
        "requested_resolution": resolution,
        "raw_record_count": raw_count,
        "raw_step_seconds": raw_step_seconds,
        "raw_timeframe_description": (
            f"{raw_step_seconds}s ({raw_step_seconds/60:.1f}m)"
            if raw_step_seconds
            else "unknown"
        ),
        "first_timestamp_iso": df_raw["timestamp"].iloc[0].isoformat(),
        "last_timestamp_iso": df_raw["timestamp"].iloc[-1].isoformat(),
        "duplicate_count": dup_count,
        "missing_count": missing_count,
        "valid_unique_candles": len(final_df),
        "resampled": len(final_df) != raw_count,
    }

    return final_df, audit

  def clean_and_deduplicate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
    """Removes duplicate timestamps, sorts chronologically, and cleans NaNs."""
    cleaned = df.drop_duplicates(subset=["timestamp"], keep="last")
    cleaned = cleaned.sort_values(by="timestamp").reset_index(drop=True)
    return cleaned

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
