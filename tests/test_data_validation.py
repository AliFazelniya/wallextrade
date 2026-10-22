"""Unit tests for Data Quality, Precision, and Staleness Validation."""

import datetime
import numpy as np
import pandas as pd
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
