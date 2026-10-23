"""Phase 25: Structural Sniper Ensemble Implementation and Comparative Backtest.

Implements and evaluates:
- Model A: Standalone H1 (Multi-Timeframe Structural Trend)
- Model B: Standalone H3 (Cross-Asset Lead-Lag Spillover)
- Model C: Integrated H1+H3 Structural Sniper Ensemble

Shared Portfolio Controls:
- Initial Capital: 5,000,000 TMN
- Max Order Notional: 500,000 TMN
- Max Portfolio Exposure: 30% (max 2 concurrent positions = 1,000,000 TMN)
- Duplicate Prevention: No multiple orders on the same asset
- Finite-Horizon Wind-Down: No entry after hour 60, passive maker exit after hour 66
- Full Execution Realism: Intra-bar High/Low wicks for stop-loss and take-profit
- Wallex Fees: 0.25% maker, 0.30% taker, 0.15% slippage
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

from src.experimental.phase24_research_engine import prepare_multi_asset_features


def simulate_portfolio_ensemble(
    btc: pd.DataFrame,
    eth: pd.DataFrame,
    sol: pd.DataFrame,
    common_idx: pd.Index,
    enable_h1: bool = True,
    enable_h3: bool = True,
    ensemble_name: str = "H1+H3 Ensemble",
    maker_fee: float = 0.0025,
    taker_fee: float = 0.0030,
    slippage_pct: float = 0.15,
    spread_multiplier: float = 1.0,
    fill_ratio: float = 1.0,
    forced_deadline_hour: float = 72.0,
    favorable_intrabar: bool = False,
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
        # Active positions: {symbol: pos_dict}
        positions: Dict[str, Dict[str, Any]] = {}
        w_trades = 0
        w_fees = 0.0
        w_slippage = 0.0
        eq_curve = [5_000_000.0]

        for step_i, dt in enumerate(w_idx_list):
            elapsed_h = (step_i * 15.0) / 60.0
            b_bar = btc.loc[dt]
            e_bar = eth.loc[dt]
            s_bar = sol.loc[dt]

            # 1. Evaluate Exits for Open Positions
            closed_syms = []
            for sym, pos in positions.items():
                c_bar = b_bar if sym == "BTC" else (e_bar if sym == "ETH" else s_bar)
                cur_close = float(c_bar["close"])
                cur_high = float(c_bar["high"])
                cur_low = float(c_bar["low"])
                entry_p = pos["entry_px"]

                pnl_low = (cur_low - entry_p) / entry_p * 100.0
                pnl_high = (cur_high - entry_p) / entry_p * 100.0
                pnl_close = (cur_close - entry_p) / entry_p * 100.0

                source = pos.get("source", "H1")
                sl_pct = 1.8 if source == "H3" else 2.2
                tp_pct = 3.5 if source == "H3" else 4.5

                if favorable_intrabar:
                    is_tp = pnl_high >= tp_pct
                    is_sl = pnl_low <= -sl_pct and not is_tp
                else:
                    is_sl = pnl_low <= -sl_pct
                    is_tp = pnl_high >= tp_pct and not is_sl

                is_be = pos.get("reached_25", False) and pnl_close <= 0.80 and source == "H1"
                if pnl_high >= 2.5:
                    pos["reached_25"] = True
                is_winddown = elapsed_h >= 66.0 and pnl_close >= 0.50
                is_deadline = elapsed_h >= forced_deadline_hour

                if is_sl or is_tp or is_be or is_winddown or is_deadline:
                    is_maker = (is_tp or is_be or is_winddown) and not (is_sl or is_deadline)
                    fee_rate = maker_fee if is_maker else taker_fee
                    slip = cur_close * (slippage_pct / 100.0) if not is_maker else 0.0

                    if is_deadline and not (is_sl or is_tp):
                        exec_px = cur_close - slip
                        reason = "FORCED_DEADLINE_LIQUIDATION"
                    elif is_sl:
                        exec_px = entry_p * (1.0 - sl_pct / 100.0) - slip
                        reason = f"{source}_SL"
                    elif is_tp:
                        exec_px = entry_p * (1.0 + tp_pct / 100.0)
                        reason = f"{source}_TP"
                    elif is_be:
                        exec_px = cur_close
                        reason = "TRAILING_BE"
                    else:
                        exec_px = cur_close
                        reason = "WIND_DOWN"

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
                        "source": source,
                        "entry_time": pos["entry_time"],
                        "exit_time": dt,
                        "entry_px": entry_p,
                        "exit_px": exec_px,
                        "reason": reason,
                        "net_pnl": net_pnl,
                        "is_maker": is_maker,
                    })
                    closed_syms.append(sym)

            for sym in closed_syms:
                del positions[sym]

            # 2. Evaluate Candidate Entries if capacity available (max 2 positions, elapsed < 60h)
            if len(positions) < 2 and elapsed_h < 60.0 and cash >= (550_000.0 * fill_ratio):
                candidate_signals = []

                # --- H3 Opportunity Generator ---
                if enable_h3:
                    btc_mom = float(b_bar["ema_spread_pct"])
                    btc_vol = float(b_bar["vol_ratio"])
                    btc_rsi = float(b_bar["rsi_14"])
                    btc_is_surging = (b_bar["ema_20"] > b_bar["ema_50"]) and (btc_vol >= 1.40) and (55 <= btc_rsi <= 70) and (btc_mom >= 0.6)

                    if btc_is_surging:
                        sol_spr = float(s_bar["dynamic_spread"]) * spread_multiplier
                        sol_rsi = float(s_bar["rsi_14"])
                        if "SOL" not in positions and sol_spr <= 0.18 and (50 <= sol_rsi <= 65) and s_bar["ema_20"] > s_bar["ema_50"]:
                            candidate_signals.append({"symbol": "SOL", "source": "H3", "score": 2.5})
                        eth_spr = float(e_bar["dynamic_spread"]) * spread_multiplier
                        eth_rsi = float(e_bar["rsi_14"])
                        if "ETH" not in positions and eth_spr <= 0.16 and (50 <= eth_rsi <= 65) and e_bar["ema_20"] > e_bar["ema_50"]:
                            candidate_signals.append({"symbol": "ETH", "source": "H3", "score": 2.2})

                # --- H1 Opportunity Generator ---
                if enable_h1:
                    for sym, bar in [("BTC", b_bar), ("ETH", e_bar), ("SOL", s_bar)]:
                        if sym in positions:
                            continue
                        cur_p = float(bar["close"])
                        spr = float(bar["dynamic_spread"]) * spread_multiplier
                        mom_15m = float(bar["ema_spread_pct"])
                        trend_1h = bool(bar["trend_1h_bullish"])
                        rsi = float(bar["rsi_14"])
                        vol_r = float(bar["vol_ratio"])
                        adx = float(bar["adx_14"])

                        if trend_1h and bar["ema_20"] > bar["ema_50"] and (52 <= rsi <= 68) and vol_r >= 1.25 and spr <= 0.16 and adx >= 24.0:
                            score = (mom_15m / (float(bar["atr_pct"]) + 1e-6)) * (1.0 - (spr / 0.35))
                            if score >= 1.2:
                                candidate_signals.append({"symbol": sym, "source": "H1", "score": score})

                # Rank and allocate to top candidate
                if candidate_signals:
                    # Sort by score descending; H3 prioritized on tie
                    candidate_signals.sort(key=lambda x: x["score"], reverse=True)
                    best_cand = candidate_signals[0]
                    tgt_sym = best_cand["symbol"]
                    c_bar = b_bar if tgt_sym == "BTC" else (e_bar if tgt_sym == "ETH" else s_bar)
                    best_p = float(c_bar["close"])

                    notional = 500_000.0 * fill_ratio
                    slip = best_p * (slippage_pct / 100.0)
                    entry_px = best_p + slip
                    qty = notional / entry_px
                    fee = notional * taker_fee
                    net_cost = notional + fee

                    cash -= net_cost
                    w_fees += fee
                    w_slippage += qty * slip
                    positions[tgt_sym] = {
                        "symbol": tgt_sym,
                        "source": best_cand["source"],
                        "qty": qty,
                        "entry_px": entry_px,
                        "entry_time": dt,
                        "net_entry_cost": net_cost,
                    }

            # 3. Mark to Market
            total_pos_val = 0.0
            for sym, pos in positions.items():
                c_bar = b_bar if sym == "BTC" else (e_bar if sym == "ETH" else s_bar)
                total_pos_val += pos["qty"] * float(c_bar["close"])
            eq_curve.append(cash + total_pos_val)

        # 4. Terminal Liquidation at Window Boundary
        for sym, pos in list(positions.items()):
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
                "source": pos["source"],
                "entry_time": pos["entry_time"],
                "exit_time": w_idx_list[-1],
                "entry_px": pos["entry_px"],
                "exit_px": exit_px,
                "reason": "FORCED_BOUNDARY_LIQUIDATION",
                "net_pnl": net_pnl,
                "is_maker": False,
            })
        positions.clear()
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
        "name": ensemble_name,
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


def main():
    print("=" * 105)
    print("PHASE 25: COMPARISON OF STANDALONE H1, STANDALONE H3, AND H1+H3 ENSEMBLE")
    print("Shared Capital | Max 2 Concurrent Positions | Realistic Wicks | Wallex Fees")
    print("=" * 105)

    btc, eth, sol, common_idx = prepare_multi_asset_features()

    m_a = simulate_portfolio_ensemble(btc, eth, sol, common_idx, enable_h1=True, enable_h3=False, ensemble_name="Model A: H1 Only (Structural Trend)")
    m_b = simulate_portfolio_ensemble(btc, eth, sol, common_idx, enable_h1=False, enable_h3=True, ensemble_name="Model B: H3 Only (Spillover)")
    m_c = simulate_portfolio_ensemble(btc, eth, sol, common_idx, enable_h1=True, enable_h3=True, ensemble_name="Model C: H1+H3 Integrated Ensemble")

    models = [m_a, m_b, m_c]

    print(f"\n{'Model Configuration':<42} | {'PnL (TMN)':<12} | {'Mean Ret':<8} | {'Win%':<6} | {'Trades':<6} | {'T-Stat':<7} | {'MaxDD%':<6} | {'Friction'}")
    print("-" * 105)
    for m in models:
        print(f"{m['name']:<42} | {m['pnl']:>+10.1f} TMN | {m['mean_ret']:>+6.3f}% | {m['win_rate']:>5.1f}% | {m['trades']:>4} | {m['t_stat']:>+6.2f} | {m['max_dd']:>5.2f}% | {m['friction']:>8.0f} TMN")
    print("=" * 105)


if __name__ == "__main__":
    main()
