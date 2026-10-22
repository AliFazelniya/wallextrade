"""Unit tests for Feature Engineering calculations."""

import numpy as np
import pandas as pd
import pytest
from src.features.indicators import (
    compute_atr,
    compute_ema,
    compute_rsi,
    extract_features,
)


def test_ema_computation():
  prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
  ema = compute_ema(prices, span=3)
  assert len(ema) == len(prices)
  assert ema.iloc[-1] > ema.iloc[0]


def test_rsi_computation():
  # Upward trending series
  prices = pd.Series(range(100, 130))
  rsi = compute_rsi(prices, period=14)
  assert len(rsi) == len(prices)
  assert rsi.iloc[-1] >= 50.0


def test_feature_extraction():
  dates = pd.date_range("2026-01-01", periods=60, freq="15min")
  df = pd.DataFrame({
      "timestamp": dates,
      "open": np.linspace(100, 150, 60),
      "high": np.linspace(102, 152, 60),
      "low": np.linspace(98, 148, 60),
      "close": np.linspace(101, 151, 60),
      "volume": [1000.0] * 60,
  })

  features_df = extract_features(df)
  assert "ema_20" in features_df.columns
  assert "ema_50" in features_df.columns
  assert "rsi_14" in features_df.columns
  assert "atr_14" in features_df.columns
  assert "vol_ratio" in features_df.columns
