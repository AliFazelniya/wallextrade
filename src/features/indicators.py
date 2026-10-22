"""Feature Engineering for Market Regime & Momentum Detection."""

from __future__ import annotations

from typing import Any, Dict
import numpy as np
import pandas as pd


def compute_ema(series: pd.Series, span: int) -> pd.Series:
  """Exponential Moving Average."""
  return series.ewm(span=span, adjust=False).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
  """Relative Strength Index (RSI)."""
  delta = series.diff()
  gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
  loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()

  rs = gain / (loss + 1e-9)
  rsi = 100 - (100 / (1 + rs))
  return rsi.fillna(50.0)


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
  """Average True Range (ATR)."""
  high = df["high"]
  low = df["low"]
  close_prev = df["close"].shift(1)

  tr1 = high - low
  tr2 = (high - close_prev).abs()
  tr3 = (low - close_prev).abs()

  tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
  atr = tr.rolling(window=period).mean()
  return atr.bfill()


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
  """Enriches an OHLCV DataFrame with quantitative features.

  Features:
  - ema_20, ema_50
  - ema_spread_pct: ((ema_20 - ema_50) / ema_50) * 100
  - rsi_14
  - atr_14, atr_pct: (atr_14 / close) * 100
  - vol_sma_20, vol_ratio: volume / vol_sma_20
  - return_1d_pct: 24h rolling price return
  """
  if len(df) < 20:
    return df

  out = df.copy()
  out["ema_20"] = compute_ema(out["close"], 20)
  out["ema_50"] = compute_ema(out["close"], 50)
  out["ema_spread_pct"] = ((out["ema_20"] - out["ema_50"]) / out["ema_50"]) * 100

  out["rsi_14"] = compute_rsi(out["close"], 14)
  out["atr_14"] = compute_atr(out, 14)
  out["atr_pct"] = (out["atr_14"] / out["close"]) * 100

  out["vol_sma_20"] = out["volume"].rolling(window=20).mean()
  out["vol_ratio"] = out["volume"] / (out["vol_sma_20"] + 1e-9)

  out["return_pct"] = out["close"].pct_change() * 100
  return out


def get_latest_feature_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
  """Returns a clean dictionary of the most recent bar's quantitative indicators."""
  if df.empty or len(df) < 50:
    return {}

  latest = df.iloc[-1]
  prev = df.iloc[-2]

  return {
      "timestamp": str(latest.get("timestamp")),
      "close": float(latest.get("close")),
      "ema_20": float(latest.get("ema_20", 0.0)),
      "ema_50": float(latest.get("ema_50", 0.0)),
      "ema_spread_pct": round(float(latest.get("ema_spread_pct", 0.0)), 3),
      "rsi_14": round(float(latest.get("rsi_14", 50.0)), 2),
      "atr_pct": round(float(latest.get("atr_pct", 0.0)), 3),
      "vol_ratio": round(float(latest.get("vol_ratio", 1.0)), 2),
      "recent_return_pct": round(float(latest.get("return_pct", 0.0)), 2),
      "trend_direction": (
          "BULLISH"
          if latest.get("ema_20", 0) > latest.get("ema_50", 0)
          else "BEARISH"
      ),
      "is_momentum_active": bool(
          latest.get("ema_20", 0) > latest.get("ema_50", 0)
          and 50 <= latest.get("rsi_14", 50) <= 70
          and latest.get("vol_ratio", 1) >= 1.1
      ),
  }
