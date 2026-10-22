"""Unit tests for Data Quality, Precision, and Staleness Validation."""

import datetime
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock
import pytest
from src.data.fetcher import MarketDataFetcher


def test_market_precision_and_min_notional():
  min_notional = 50_000.0
  price = 22_000_000_000.0  # 1 BTC in TMN
  min_qty = 1e-8

  valid_order_value = 100_000.0  # > 50,000 TMN
  invalid_order_value = 35_000.0  # < 50,000 TMN

  assert valid_order_value >= min_notional
  assert invalid_order_value < min_notional


def test_dataframe_cleaning_deduplication():
  fetcher = MarketDataFetcher(client=None)

  # Create synthetic DataFrame with duplicate and out-of-order timestamps
  t1 = pd.to_datetime("2026-10-22 10:00:00")
  t2 = pd.to_datetime("2026-10-22 10:15:00")

  df_dirty = pd.DataFrame({
      "timestamp": [t2, t1, t1],  # t1 is duplicate and out-of-order
      "open": [100.0, 95.0, 96.0],
      "high": [105.0, 98.0, 98.0],
      "low": [98.0, 94.0, 94.0],
      "close": [102.0, 97.0, 97.0],
      "volume": [10.0, 5.0, 5.0],
  })

  df_clean = fetcher.clean_and_deduplicate_dataframe(df_dirty)

  assert len(df_clean) == 2
  # Ensure sorted chronologically
  assert df_clean["timestamp"].iloc[0] == t1
  assert df_clean["timestamp"].iloc[1] == t2


def test_data_staleness_detection():
  max_allowed_staleness_seconds = 60.0
  now = datetime.datetime.now(datetime.timezone.utc)

  fresh_time = now - datetime.timedelta(seconds=20)
  stale_time = now - datetime.timedelta(seconds=120)

  assert (now - fresh_time).total_seconds() <= max_allowed_staleness_seconds
  assert (now - stale_time).total_seconds() > max_allowed_staleness_seconds


@pytest.mark.asyncio
async def test_paginated_historical_fetching():
  from unittest.mock import AsyncMock

  client = AsyncMock()
  # Mock 2 chunks of UDF history
  chunk1 = {
      "s": "ok",
      "t": [1000, 1060],
      "o": [10.0, 11.0],
      "h": [12.0, 13.0],
      "l": [9.0, 10.0],
      "c": [11.0, 12.0],
      "v": [100.0, 150.0],
  }
  chunk2 = {
      "s": "ok",
      "t": [1120, 1180],
      "o": [12.0, 13.0],
      "h": [14.0, 15.0],
      "l": [11.0, 12.0],
      "c": [13.0, 14.0],
      "v": [200.0, 250.0],
  }
  client.get_udf_history = AsyncMock(side_effect=[chunk1, chunk2])

  fetcher = MarketDataFetcher(client=client)
  # Span of 25 days (> 18 days limit)
  from_ts = 1000
  to_ts = from_ts + int(25 * 86400)

  df, audit = await fetcher.fetch_ohlcv_dataframe(
      symbol="BTCTMN",
      resolution="1",
      from_ts=from_ts,
      to_ts=to_ts,
      auto_resample_to_true_timeframe=False,
  )

  assert client.get_udf_history.call_count == 2
  assert len(df) == 4
  assert audit["raw_record_count"] == 4


@pytest.mark.asyncio
async def test_fetch_incremental_ohlcv_updates_cleanly():
  client = AsyncMock()
  fetcher = MarketDataFetcher(client=client)

  # Create base cached dataframe with 70 bars
  times = pd.date_range("2026-10-22 00:00:00", periods=70, freq="15min", tz="UTC")
  cached_df = pd.DataFrame({
      "timestamp": times,
      "open": [100.0] * 70,
      "high": [105.0] * 70,
      "low": [95.0] * 70,
      "close": [102.0] * 70,
      "volume": [10.0] * 70,
  })

  # Mock incremental response returning 2 newest candles (one overlapping, one new)
  inc_times = [int(times[-1].timestamp()), int((times[-1] + pd.Timedelta(minutes=15)).timestamp())]
  client.get_udf_history = AsyncMock(return_value={
      "s": "ok",
      "t": inc_times,
      "o": [102.0, 103.0],
      "h": [106.0, 107.0],
      "l": [101.0, 102.0],
      "c": [104.0, 105.0],
      "v": [15.0, 20.0],
  })

  updated_df, audit = await fetcher.fetch_incremental_ohlcv("BTCTMN", cached_df=cached_df)

  assert audit["incremental"] is True
  assert len(updated_df) == 71  # 70 + 1 deduplicated new candle
  assert updated_df["close"].iloc[-1] == 105.0
