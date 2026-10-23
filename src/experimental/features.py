"""Experimental Feature Engineering for Phase 22 Advanced Strategy Discovery."""

from __future__ import annotations

import numpy as np
import pandas as pd
from src.features.indicators import (
    compute_ema,
    compute_rsi,
    compute_atr,
    compute_bollinger_bands,
)


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Computes Wilder's Average Directional Index (ADX)."""
    high = df["high"]
    low = df["low"]
    
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    atr = compute_atr(df, period)
    
    plus_di = 100.0 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-9))
    minus_di = 100.0 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-9))
    
    dx = 100.0 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx.fillna(20.0)


def compute_donchian(df: pd.DataFrame, period: int = 20) -> tuple[pd.Series, pd.Series]:
    """Computes Donchian Channel High and Low over rolling period."""
    high = df["high"].shift(1).rolling(window=period).max()
    low = df["low"].shift(1).rolling(window=period).min()
    return high.bfill(), low.bfill()


def extract_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """Enriches DataFrame with baseline and advanced technical features."""
    out = df.copy()
    if "dt" not in out.columns:
        out["dt"] = pd.to_datetime(out["timestamp"], utc=True)
    out = out.sort_values("dt").reset_index(drop=True)
    
    # 1. EMAs
    out["ema_20"] = compute_ema(out["close"], 20)
    out["ema_50"] = compute_ema(out["close"], 50)
    out["ema_spread_pct"] = ((out["ema_20"] - out["ema_50"]) / out["ema_50"]) * 100.0
    
    # 2. RSI & ATR
    out["rsi_14"] = compute_rsi(out["close"], 14)
    out["atr_14"] = compute_atr(out, 14)
    out["atr_pct"] = (out["atr_14"] / out["close"]) * 100.0
    
    # 3. Bollinger Bands & Bandwidth
    mid, upper, lower = compute_bollinger_bands(out["close"], 20, 2.0)
    out["bb_mid"] = mid
    out["bb_upper"] = upper
    out["bb_lower"] = lower
    out["bb_bandwidth"] = ((upper - lower) / mid) * 100.0
    bb_range = (upper - lower).replace(0, 1e-9)
    out["bb_pct_b"] = (out["close"] - lower) / bb_range
    
    # 4. Donchian Channels
    dc_h, dc_l = compute_donchian(out, 20)
    out["dc_high_20"] = dc_h
    out["dc_low_20"] = dc_l
    
    # 5. ADX
    out["adx_14"] = compute_adx(out, 14)
    
    # 6. Volume Metrics
    out["vol_sma_20"] = out["volume"].rolling(window=20).mean()
    out["vol_ratio"] = out["volume"] / (out["vol_sma_20"] + 1e-9)
    
    # 7. Dynamic Spread Model (Expanding window mean prevents lookahead bias)
    expanding_atr = out["atr_pct"].expanding(min_periods=30).mean().bfill()
    out["dynamic_spread"] = np.clip(0.12 * (out["atr_pct"] / expanding_atr), 0.06, 0.35)
    
    return out
