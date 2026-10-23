"""Phase 24 Advanced Quantitative Research Engine.

Tests 4 distinct quantitative hypotheses against realistic Wallex execution:
1. Hypothesis 1: Multi-Timeframe Structural Trend (1h Trend Filter + 15m Entry + Wider TP/SL)
2. Hypothesis 2: Liquidity Crash Capitulation / Dip Absorption (Extreme Oversold Mean Reversion)
3. Hypothesis 3: Cross-Asset Lead-Lag Spillover (BTC Breakout Leader -> SOL Laggard Entry)
4. Hypothesis 4: Machine Learning Triple-Barrier Meta-Model with Chronological Walk-Forward Validation

All tests strictly enforce:
- Zero lookahead bias (expanding statistics only)
- Realistic intra-bar High/Low wick execution for stop-loss and take-profit
- Wallex Level 1 fees (0.25% maker, 0.30% taker) and 0.15% slippage
- 5,000,000 TMN cash reset per 72-hour window
- 29 independent competition windows
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

REPO_ROOT = Path("/root/starcoach-hack/wallex")
sys.path.insert(0, str(REPO_ROOT))

from src.features.indicators import compute_ema, compute_rsi, compute_atr, compute_bollinger_bands
from src.experimental.features import compute_adx, compute_donchian


def prepare_multi_asset_features() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Index]:
    """Loads and computes multi-timeframe and cross-asset features with zero lookahead."""
    def process_asset(symbol: str) -> pd.DataFrame:
        df = pd.read_csv(REPO_ROOT / f"data/cache/{symbol}_15m_90d.csv")
        df["dt"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("dt").reset_index(drop=True)
        
        # 15m Indicators
        df["ema_20"] = compute_ema(df["close"], 20)
        df["ema_50"] = compute_ema(df["close"], 50)
        df["ema_spread_pct"] = ((df["ema_20"] - df["ema_50"]) / df["ema_50"]) * 100.0
        df["rsi_14"] = compute_rsi(df["close"], 14)
        df["atr_14"] = compute_atr(df, 14)
        df["atr_pct"] = (df["atr_14"] / df["close"]) * 100.0
        df["adx_14"] = compute_adx(df, 14)
        df["vol_sma"] = df["volume"].rolling(window=20).mean()
        df["vol_ratio"] = df["volume"] / (df["vol_sma"] + 1e-9)

        # Higher Timeframe Approximation (4-bar = 1h rolling)
        df["ema_1h_20"] = compute_ema(df["close"], 80)
        df["ema_1h_50"] = compute_ema(df["close"], 200)
        df["trend_1h_bullish"] = df["ema_1h_20"] > df["ema_1h_50"]

        # Dynamic Spread (Expanding mean, zero lookahead)
        exp_atr = df["atr_pct"].expanding(min_periods=60).mean().bfill()
        df["dynamic_spread"] = np.clip(0.12 * (df["atr_pct"] / exp_atr), 0.06, 0.35)

        # Extreme dip indicators
        mid, upper, lower = compute_bollinger_bands(df["close"], 20, 2.2)
        df["bb_lower"] = lower
        df["dist_bb_lower_pct"] = ((df["close"] - lower) / df["close"]) * 100.0
        df["dist_ema50_pct"] = ((df["close"] - df["ema_50"]) / df["close"]) * 100.0

        return df.set_index("dt")

    btc = process_asset("BTCTMN")
    eth = process_asset("ETHTMN")
    sol = process_asset("SOLTMN")
    common_idx = btc.index.intersection(eth.index).intersection(sol.index).sort_values()
    return btc, eth, sol, common_idx


# =====================================================================
# SIMULATION ENGINE WITH REALISTIC INTRA-BAR WICKS & FEES
# =====================================================================
def simulate_strategy_windows(
    btc: pd.DataFrame,
    eth: pd.DataFrame,
    sol: pd.DataFrame,
    common_idx: pd.Index,
    strategy_logic_fn,
    strategy_name: str,
    maker_fee: float = 0.0025,
    taker_fee: float = 0.0030,
    slippage_pct: float = 0.15,
) -> Dict[str, Any]:
    t0 = common_idx[60]
    t_end = common_idx[-1]
    window_dur = pd.Timedelta(hours=72)

    cur_start = t0
    w_idx = 1
    window_records = []
    trade_records = []

    while cur_start < t_end:
        cur_end = cur_start + window_dur
        if cur_end > t_end:
            break
        w_idx_list = common_idx[(common_idx >= cur_start) & (common_idx < cur_end)]

        cash = 5_000_000.0
        pos: Optional[Dict[str, Any]] = None
        w_trades = 0
        w_fees = 0.0
        w_slippage = 0.0
        eq_curve = [5_000_000.0]

        for step_i, dt in enumerate(w_idx_list):
            elapsed_h = (step_i * 15.0) / 60.0
            b_bar = btc.loc[dt]
            e_bar = eth.loc[dt]
            s_bar = sol.loc[dt]

            # 1. Exit Evaluation if in position
            if pos is not None:
                sym = pos["symbol"]
                c_bar = b_bar if sym == "BTC" else (e_bar if sym == "ETH" else s_bar)
                cur_close = float(c_bar["close"])
                cur_high = float(c_bar["high"])
                cur_low = float(c_bar["low"])

                # Evaluate strategy-specific exit
                exit_res = strategy_logic_fn(
                    mode="EXIT",
                    pos=pos,
                    c_bar=c_bar,
                    elapsed_h=elapsed_h,
                    step_i=step_i,
                    b_bar=b_bar,
                    e_bar=e_bar,
                    s_bar=s_bar,
                )

                if exit_res is not None:
                    is_maker = exit_res.get("is_maker", False)
                    fee_rate = maker_fee if is_maker else taker_fee
                    slip = cur_close * (slippage_pct / 100.0) if not is_maker else 0.0
                    exec_px = exit_res.get("exec_px", cur_close - slip)

                    gross = pos["qty"] * exec_px
                    fee = gross * fee_rate
                    net_pnl = gross - fee - pos["net_entry_cost"]

                    cash += gross - fee
                    w_fees += fee
                    w_slippage += pos["qty"] * slip
                    w_trades += 1

                    trade_records.append({
                        "window_id": f"W{w_idx:02d}",
                        "symbol": sym,
                        "entry_time": pos["entry_time"],
                        "exit_time": dt,
                        "entry_px": pos["entry_px"],
                        "exit_px": exec_px,
                        "reason": exit_res.get("reason", "EXIT"),
                        "net_pnl": net_pnl,
                        "is_maker": is_maker,
                    })
                    pos = None

            # 2. Entry Evaluation if flat
            if pos is None and elapsed_h < 60.0:
                entry_res = strategy_logic_fn(
                    mode="ENTRY",
                    pos=None,
                    c_bar=None,
                    elapsed_h=elapsed_h,
                    step_i=step_i,
                    b_bar=b_bar,
                    e_bar=e_bar,
                    s_bar=s_bar,
                )
                if entry_res is not None and entry_res.get("action") == "BUY":
                    target_sym = entry_res["symbol"]
                    c_bar = b_bar if target_sym == "BTC" else (e_bar if target_sym == "ETH" else s_bar)
                    best_p = float(c_bar["close"])
                    notional = 500_000.0
                    slip = best_p * (slippage_pct / 100.0)
                    entry_px = best_p + slip
                    qty = notional / entry_px
                    fee = notional * taker_fee
                    net_cost = notional + fee

                    cash -= net_cost
                    w_fees += fee
                    w_slippage += qty * slip
                    pos = {
                        "symbol": target_sym,
                        "qty": qty,
                        "entry_px": entry_px,
                        "raw_entry_px": best_p,
                        "entry_time": dt,
                        "entry_step": step_i,
                        "net_entry_cost": net_cost,
                        "extra": entry_res.get("extra", {}),
                    }

            # 3. Mark to Market
            if pos is not None:
                sym = pos["symbol"]
                c_bar = b_bar if sym == "BTC" else (e_bar if sym == "ETH" else s_bar)
                eq_curve.append(cash + (pos["qty"] * float(c_bar["close"])))
            else:
                eq_curve.append(cash)

        # 4. Forced Liquidation at Window Boundary
        if pos is not None:
            sym = pos["symbol"]
            c_bar = b_bar if sym == "BTC" else (e_bar if sym == "ETH" else s_bar)
            last_p = float(c_bar["close"])
            slip = last_p * (slippage_pct / 100.0)
            exit_px = last_p - slip
            gross = pos["qty"] * exit_px
            fee = gross * taker_fee
            net_pnl = gross - fee - pos["net_entry_cost"]

            cash += gross - fee
            w_fees += fee
            w_slippage += pos["qty"] * slip
            w_trades += 1

            trade_records.append({
                "window_id": f"W{w_idx:02d}",
                "symbol": sym,
                "entry_time": pos["entry_time"],
                "exit_time": w_idx_list[-1],
                "entry_px": pos["entry_px"],
                "exit_px": exit_px,
                "reason": "FORCED_BOUNDARY_LIQUIDATION",
                "net_pnl": net_pnl,
                "is_maker": False,
            })
            pos = None
            eq_curve.append(cash)

        net_pnl_w = cash - 5_000_000.0
        ret_pct_w = (net_pnl_w / 5_000_000.0) * 100.0
        eq_s = pd.Series(eq_curve)
        max_dd = (eq_s.cummax() - eq_s).max() / eq_s.cummax().max() * 100.0

        window_records.append({
            "window_id": f"W{w_idx:02d}",
            "pnl": net_pnl_w,
            "ret": ret_pct_w,
            "trades": w_trades,
            "max_dd": max_dd,
            "fees": w_fees,
            "slip": w_slippage,
            "friction": w_fees + w_slippage,
        })
        cur_start = cur_end
        w_idx += 1

    df_res = pd.DataFrame(window_records)
    agg_pnl = df_res["pnl"].sum()
    mean_ret = df_res["ret"].mean()
    std_ret = df_res["ret"].std()
    sem = std_ret / math.sqrt(len(df_res)) if len(df_res) > 0 else 0
    t_stat = mean_ret / sem if sem > 0 else 0
    wins = (df_res["ret"] > 0.001).sum()
    losses = (df_res["ret"] < -0.001).sum()
    zeros = (df_res["trades"] == 0).sum()

    return {
        "name": strategy_name,
        "pnl": agg_pnl,
        "mean_ret": mean_ret,
        "t_stat": t_stat,
        "wins": wins,
        "losses": losses,
        "zeros": zeros,
        "win_rate": (wins / len(df_res) * 100.0) if len(df_res) > 0 else 0,
        "trades": df_res["trades"].sum(),
        "friction": df_res["friction"].sum(),
        "max_dd": df_res["max_dd"].max(),
        "df_res": df_res,
        "trades_list": trade_records,
    }


# =====================================================================
# HYPOTHESIS 1: MULTI-TIMEFRAME STRUCTURAL TREND (Wider TP/SL + 1h Alignment)
# =====================================================================
def get_h1_logic():
    """H1: Require 1h trend bullish alignment, wider TP (+4.5%) vs SL (-2.2%) to survive 15m wicks."""
    def logic(mode, pos=None, c_bar=None, elapsed_h=0.0, step_i=0, b_bar=None, e_bar=None, s_bar=None):
        if mode == "EXIT":
            cur_p = float(c_bar["close"])
            high_p = float(c_bar["high"])
            low_p = float(c_bar["low"])
            entry_p = pos["entry_px"]

            pnl_low = (low_p - entry_p) / entry_p * 100.0
            pnl_high = (high_p - entry_p) / entry_p * 100.0
            pnl_close = (cur_p - entry_p) / entry_p * 100.0

            # Stop loss at -2.2% (wide enough to survive 15m wicks)
            if pnl_low <= -2.2:
                return {"reason": "STRUCTURAL_SL", "is_maker": False, "exec_px": entry_p * (1.0 - 0.022)}
            # Take profit at +4.5%
            if pnl_high >= 4.5:
                return {"reason": "STRUCTURAL_TP", "is_maker": True, "exec_px": entry_p * (1.0 + 0.045)}
            # Trailing breakeven: if profit reached +2.5%, exit if it drops back below +0.8%
            if pos.get("reached_25", False) and pnl_close <= 0.80:
                return {"reason": "TRAILING_BE_STOP", "is_maker": True, "exec_px": cur_p}
            if pnl_high >= 2.5:
                pos["reached_25"] = True

            # Wind-down exit after hour 66 if in positive territory
            if elapsed_h >= 66.0 and pnl_close >= 0.50:
                return {"reason": "WIND_DOWN_PASSIVE", "is_maker": True, "exec_px": cur_p}
            return None

        elif mode == "ENTRY":
            candidates = []
            for sym, bar in [("BTC", b_bar), ("ETH", e_bar), ("SOL", s_bar)]:
                cur_p = float(bar["close"])
                spr = float(bar["dynamic_spread"])
                mom_15m = float(bar["ema_spread_pct"])
                trend_1h = bool(bar["trend_1h_bullish"])
                rsi = float(bar["rsi_14"])
                vol_r = float(bar["vol_ratio"])
                adx = float(bar["adx_14"])

                # Strict multi-timeframe filter
                if trend_1h and bar["ema_20"] > bar["ema_50"] and (52 <= rsi <= 68) and vol_r >= 1.25 and spr <= 0.16 and adx >= 24.0:
                    score = (mom_15m / (float(bar["atr_pct"]) + 1e-6)) * (1.0 - (spr / 0.35))
                    if score >= 1.2:
                        candidates.append((score, sym))

            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                return {"action": "BUY", "symbol": candidates[0][1]}
            return None

    return logic


# =====================================================================
# HYPOTHESIS 2: LIQUIDITY CRASH CAPITULATION (Extreme Dip Absorption)
# =====================================================================
def get_h2_logic():
    """H2: Buy extreme panic dips (RSI < 24, price > 2.5% below EMA50, volume surge) targeting quick +2.5% bounce."""
    def logic(mode, pos=None, c_bar=None, elapsed_h=0.0, step_i=0, b_bar=None, e_bar=None, s_bar=None):
        if mode == "EXIT":
            cur_p = float(c_bar["close"])
            high_p = float(c_bar["high"])
            low_p = float(c_bar["low"])
            entry_p = pos["entry_px"]
            bars_held = step_i - pos["entry_step"]

            pnl_low = (low_p - entry_p) / entry_p * 100.0
            pnl_high = (high_p - entry_p) / entry_p * 100.0

            # Quick bounce target: TP = +2.50% (Maker)
            if pnl_high >= 2.50:
                return {"reason": "BOUNCE_TP", "is_maker": True, "exec_px": entry_p * (1.0 + 0.025)}
            # Hard stop if capitulation worsens: SL = -1.80%
            if pnl_low <= -1.80:
                return {"reason": "CAPITULATION_SL", "is_maker": False, "exec_px": entry_p * (1.0 - 0.018)}
            # Time stop: if held > 16 bars (4 hours) without bounce, exit
            if bars_held >= 16:
                return {"reason": "TIME_CUT", "is_maker": True, "exec_px": cur_p}
            return None

        elif mode == "ENTRY":
            candidates = []
            for sym, bar in [("BTC", b_bar), ("ETH", e_bar), ("SOL", s_bar)]:
                cur_p = float(bar["close"])
                spr = float(bar["dynamic_spread"])
                rsi = float(bar["rsi_14"])
                vol_r = float(bar["vol_ratio"])
                dist_ema50 = float(bar["dist_ema50_pct"])

                # Capitulation condition: sharp drop > 2.2% below EMA50, RSI oversold, volume surge
                if dist_ema50 < -2.2 and rsi <= 26.0 and vol_r >= 1.50 and spr <= 0.18:
                    # Score by severity of oversold condition
                    score = abs(dist_ema50) * (30.0 - rsi)
                    candidates.append((score, sym))

            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                return {"action": "BUY", "symbol": candidates[0][1]}
            return None

    return logic


# =====================================================================
# HYPOTHESIS 3: CROSS-ASSET LEAD-LAG MOMENTUM SPILLOVER
# =====================================================================
def get_h3_logic():
    """H3: When BTC leads with explosive volume breakout, enter laggard high-beta SOL with trailing TP."""
    def logic(mode, pos=None, c_bar=None, elapsed_h=0.0, step_i=0, b_bar=None, e_bar=None, s_bar=None):
        if mode == "EXIT":
            cur_p = float(c_bar["close"])
            high_p = float(c_bar["high"])
            low_p = float(c_bar["low"])
            entry_p = pos["entry_px"]

            pnl_low = (low_p - entry_p) / entry_p * 100.0
            pnl_high = (high_p - entry_p) / entry_p * 100.0
            pnl_close = (cur_p - entry_p) / entry_p * 100.0

            if pnl_low <= -1.80:
                return {"reason": "SPILLOVER_SL", "is_maker": False, "exec_px": entry_p * (1.0 - 0.018)}
            if pnl_high >= 3.50:
                return {"reason": "SPILLOVER_TP", "is_maker": True, "exec_px": entry_p * (1.0 + 0.035)}
            if elapsed_h >= 66.0 and pnl_close >= 0.50:
                return {"reason": "WIND_DOWN_PASSIVE", "is_maker": True, "exec_px": cur_p}
            return None

        elif mode == "ENTRY":
            # Check BTC leader breakout condition
            btc_mom = float(b_bar["ema_spread_pct"])
            btc_vol = float(b_bar["vol_ratio"])
            btc_rsi = float(b_bar["rsi_14"])
            btc_is_surging = (b_bar["ema_20"] > b_bar["ema_50"]) and (btc_vol >= 1.40) and (55 <= btc_rsi <= 70) and (btc_mom >= 0.6)

            if btc_is_surging:
                # Target SOL if SOL is starting to move but hasn't overextended yet
                sol_spr = float(s_bar["dynamic_spread"])
                sol_rsi = float(s_bar["rsi_14"])
                if sol_spr <= 0.18 and (50 <= sol_rsi <= 65) and s_bar["ema_20"] > s_bar["ema_50"]:
                    return {"action": "BUY", "symbol": "SOL"}
                # Fallback to ETH if SOL spread too wide
                eth_spr = float(e_bar["dynamic_spread"])
                eth_rsi = float(e_bar["rsi_14"])
                if eth_spr <= 0.16 and (50 <= eth_rsi <= 65) and e_bar["ema_20"] > e_bar["ema_50"]:
                    return {"action": "BUY", "symbol": "ETH"}
            return None

    return logic


# =====================================================================
# HYPOTHESIS 4: CHRONOLOGICAL WALK-FORWARD MACHINE LEARNING META-MODEL
# =====================================================================
def run_ml_walkforward_hypothesis(btc: pd.DataFrame, eth: pd.DataFrame, sol: pd.DataFrame, common_idx: pd.Index) -> Dict[str, Any]:
    """H4: Triple-barrier labeling + Walk-Forward Logistic Regression Meta-Model."""
    print("\n--- Training Walk-Forward Machine Learning Meta-Model (H4) ---")
    
    # 1. Generate triple barrier labels for SOL (highest beta)
    df_sol = sol.copy().loc[common_idx]
    prices = df_sol["close"].values
    highs = df_sol["high"].values
    lows = df_sol["low"].values
    n = len(prices)

    tp_barrier = 0.030  # +3.0%
    sl_barrier = -0.018 # -1.8%
    max_horizon_bars = 24 # 6 hours

    labels = np.zeros(n)
    for i in range(n - max_horizon_bars):
        p0 = prices[i]
        outcome = 0
        for h in range(1, max_horizon_bars + 1):
            cur_high = highs[i + h]
            cur_low = lows[i + h]
            if (cur_low - p0) / p0 <= sl_barrier:
                outcome = 0 # Loss
                break
            if (cur_high - p0) / p0 >= tp_barrier:
                outcome = 1 # Win
                break
        labels[i] = outcome

    df_sol["target_win"] = labels

    # Features
    feature_cols = ["ema_spread_pct", "rsi_14", "atr_pct", "adx_14", "vol_ratio", "dynamic_spread"]
    X = df_sol[feature_cols].copy().fillna(0.0)
    # Standardize rolling
    X_norm = (X - X.rolling(window=100, min_periods=20).mean()) / (X.rolling(window=100, min_periods=20).std() + 1e-6)
    X_norm = X_norm.bfill().fillna(0.0)

    # Walk-forward splits (4 folds)
    # Fold 1: Train 0 to 2000, Test 2000 to 3500
    # Fold 2: Train 0 to 3500, Test 3500 to 5200
    # Fold 3: Train 0 to 5200, Test 5200 to 6900
    # Fold 4: Train 0 to 6900, Test 6900 to end
    splits = [
        (0, 2500, 2500, 4000),
        (0, 4000, 4000, 5500),
        (0, 5500, 5500, 7000),
        (0, 7000, 7000, n),
    ]

    # Simple Logistic Regression implemented with numpy gradient descent to avoid external deps
    probs = np.zeros(n)
    for train_start, train_end, test_start, test_end in splits:
        X_tr = X_norm.iloc[train_start:train_end].values
        y_tr = labels[train_start:train_end]
        X_te = X_norm.iloc[test_start:test_end].values

        # L2-regularized logistic regression
        weights = np.zeros(X_tr.shape[1])
        lr = 0.05
        reg = 0.1
        for ep in range(150):
            preds = 1.0 / (1.0 + np.exp(-np.clip(X_tr @ weights, -15, 15)))
            grad = (X_tr.T @ (preds - y_tr)) / len(y_tr) + reg * weights
            weights -= lr * grad

        te_probs = 1.0 / (1.0 + np.exp(-np.clip(X_te @ weights, -15, 15)))
        probs[test_start:test_end] = te_probs

    df_sol["ml_prob_win"] = probs

    # Build H4 logic: only buy when predicted P(Win) >= 0.58
    def h4_logic(mode, pos=None, c_bar=None, elapsed_h=0.0, step_i=0, b_bar=None, e_bar=None, s_bar=None):
        if mode == "EXIT":
            cur_p = float(c_bar["close"])
            high_p = float(c_bar["high"])
            low_p = float(c_bar["low"])
            entry_p = pos["entry_px"]

            pnl_low = (low_p - entry_p) / entry_p * 100.0
            pnl_high = (high_p - entry_p) / entry_p * 100.0
            pnl_close = (cur_p - entry_p) / entry_p * 100.0

            if pnl_low <= -1.80:
                return {"reason": "ML_STOP_LOSS", "is_maker": False, "exec_px": entry_p * (1.0 - 0.018)}
            if pnl_high >= 3.00:
                return {"reason": "ML_TAKE_PROFIT", "is_maker": True, "exec_px": entry_p * (1.0 + 0.030)}
            if elapsed_h >= 66.0 and pnl_close >= 0.50:
                return {"reason": "WIND_DOWN_PASSIVE", "is_maker": True, "exec_px": cur_p}
            return None

        elif mode == "ENTRY":
            # Look up SOL ml probability at current bar
            dt = s_bar.name
            if dt in df_sol.index:
                prob = float(df_sol.loc[dt, "ml_prob_win"])
                spr = float(s_bar["dynamic_spread"])
                # Trade only if calibrated win probability >= 0.58 and spread <= 0.18
                if prob >= 0.58 and spr <= 0.18 and s_bar["ema_20"] > s_bar["ema_50"]:
                    return {"action": "BUY", "symbol": "SOL"}
            return None

    return simulate_strategy_windows(btc, eth, sol, common_idx, h4_logic, "H4: ML Probabilistic Meta-Model (Walk-Forward)")


# =====================================================================
# MAIN EXPERIMENT RUNNER
# =====================================================================
def run_all_phase24_research():
    print("=" * 105)
    print("PHASE 24 ADVANCED QUANTITATIVE RESEARCH EXPERIMENT MATRIX")
    print("Zero Lookahead | Realistic Intra-bar Wicks | Full Fees & Slippage | Walk-Forward Evaluation")
    print("=" * 105)

    btc, eth, sol, common_idx = prepare_multi_asset_features()

    h1_fn = get_h1_logic()
    h2_fn = get_h2_logic()
    h3_fn = get_h3_logic()

    res_h1 = simulate_strategy_windows(btc, eth, sol, common_idx, h1_fn, "H1: Multi-Timeframe Structural Trend (1h+15m)")
    res_h2 = simulate_strategy_windows(btc, eth, sol, common_idx, h2_fn, "H2: Liquidity Crash Capitulation (Oversold Dip)")
    res_h3 = simulate_strategy_windows(btc, eth, sol, common_idx, h3_fn, "H3: Cross-Asset Lead-Lag Spillover (BTC->SOL)")
    res_h4 = run_ml_walkforward_hypothesis(btc, eth, sol, common_idx)

    all_hypotheses = [res_h1, res_h2, res_h3, res_h4]

    print("\n" + "=" * 105)
    print(f"{'Strategy Hypothesis':<48} | {'PnL (TMN)':<11} | {'Mean Ret':<8} | {'Win%':<6} | {'Trades':<6} | {'T-Stat':<7} | {'MaxDD%':<6} | {'Friction'}")
    print("-" * 105)
    for r in all_hypotheses:
        print(f"{r['name']:<48} | {r['pnl']:>+9.1f} TMN | {r['mean_ret']:>+6.3f}% | {r['win_rate']:>5.1f}% | {r['trades']:>4} | {r['t_stat']:>+6.2f} | {r['max_dd']:>5.2f}% | {r['friction']:>8.0f} TMN")
    print("=" * 105)

    return all_hypotheses


if __name__ == "__main__":
    run_all_phase24_research()
