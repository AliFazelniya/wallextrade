"""Phase 24: Trade-by-Trade Performance Reconciliation.

Compares individual trades across 4 key stages:
1. Candidate E Raw (Phase 22: Global ATR, Close-only exit) -> +47,240.7 TMN (33 trades)
2. Candidate E Clean (Expanding ATR, Close-only exit) -> +32,185.9 TMN (28 trades)
3. Candidate E with AI Agent (Expanding ATR + RegimeClassificationAgent) -> +9,243.1 TMN (26 trades)
4. Candidate E with AI Agent + Intra-bar Wicks (High/Low SL/TP) -> -12,284.1 TMN (28 trades)

Identifies exact entry/exit timestamps, symbols, price levels, PnL deltas, and root causes of degradation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.experimental.audit_phase22 import load_all_assets, simulate_candidate_e


def run_trade_reconciliation():
    print("=" * 105)
    print("PHASE 24: TRADE-BY-TRADE RECONCILIATION OF PROFITABILITY DEGRADATION")
    print("=" * 105)

    # 1. Load data with global vs expanding ATR
    btc_raw, eth_raw, sol_raw, c_idx_raw = load_all_assets(clean_lookahead=False)
    btc_clean, eth_clean, sol_clean, c_idx_clean = load_all_assets(clean_lookahead=True)

    # Stage 1: Phase 22 Raw
    df_stg1, trades_stg1 = simulate_candidate_e(btc_raw, eth_raw, sol_raw, c_idx_raw, use_ai_agent=False, check_intrabar_extremes=False)
    # Stage 2: Clean Lookahead
    df_stg2, trades_stg2 = simulate_candidate_e(btc_clean, eth_clean, sol_clean, c_idx_clean, use_ai_agent=False, check_intrabar_extremes=False)
    # Stage 3: Clean Lookahead + AI Agent
    df_stg3, trades_stg3 = simulate_candidate_e(btc_clean, eth_clean, sol_clean, c_idx_clean, use_ai_agent=True, check_intrabar_extremes=False)
    # Stage 4: Clean Lookahead + AI Agent + Intra-bar High/Low Wicks
    df_stg4, trades_stg4 = simulate_candidate_e(btc_clean, eth_clean, sol_clean, c_idx_clean, use_ai_agent=True, check_intrabar_extremes=True)

    pnl1 = df_stg1["pnl"].sum()
    pnl2 = df_stg2["pnl"].sum()
    pnl3 = df_stg3["pnl"].sum()
    pnl4 = df_stg4["pnl"].sum()

    print(f"\n--- 4-STAGE PROFITABILITY WATERFALL ---")
    print(f"Stage 1 (Phase 22 Candidate E Raw - Global ATR, Close-only):      PnL = {pnl1:>+10.1f} TMN | Trades = {len(trades_stg1):>2}")
    print(f"Stage 2 (Lookahead Cleaned - Expanding ATR, Close-only):           PnL = {pnl2:>+10.1f} TMN | Trades = {len(trades_stg2):>2} | Delta = {pnl2 - pnl1:>+10.1f} TMN")
    print(f"Stage 3 (Production AI Agent Gated - Expanding ATR):              PnL = {pnl3:>+10.1f} TMN | Trades = {len(trades_stg3):>2} | Delta = {pnl3 - pnl2:>+10.1f} TMN")
    print(f"Stage 4 (Realistic Execution - Intra-bar High/Low Wicks):          PnL = {pnl4:>+10.1f} TMN | Trades = {len(trades_stg4):>2} | Delta = {pnl4 - pnl3:>+10.1f} TMN")
    print(f"TOTAL DEGRADATION (Stage 1 -> Stage 4):                           PnL Delta = {pnl4 - pnl1:>+10.1f} TMN")

    # Trade level comparison
    t1_df = pd.DataFrame(trades_stg1)
    t2_df = pd.DataFrame(trades_stg2)
    t3_df = pd.DataFrame(trades_stg3)
    t4_df = pd.DataFrame(trades_stg4)

    print("\n" + "=" * 105)
    print("DETAILED WINDOW-BY-WINDOW PNL COMPARISON ACROSS 4 STAGES")
    print("=" * 105)
    print(f"{'Window':<8} | {'Stage 1 Raw':<12} | {'Stage 2 Clean':<13} | {'Stage 3 AI':<12} | {'Stage 4 Wicks':<13} | {'Dominant Driver / Degradation Reason'}")
    print("-" * 105)

    all_windows = df_stg1["window_id"].tolist()
    for w_id in all_windows:
        r1 = df_stg1[df_stg1["window_id"] == w_id].iloc[0]
        r2 = df_stg2[df_stg2["window_id"] == w_id].iloc[0]
        r3 = df_stg3[df_stg3["window_id"] == w_id].iloc[0]
        r4 = df_stg4[df_stg4["window_id"] == w_id].iloc[0]

        driver = ""
        if abs(r1["pnl"] - r2["pnl"]) > 500:
            driver += f"ATR lookahead diff ({r2['pnl']-r1['pnl']:>+6.0f}); "
        if abs(r2["pnl"] - r3["pnl"]) > 500:
            driver += f"AI vetoed trade ({r3['pnl']-r2['pnl']:>+6.0f}); "
        if abs(r3["pnl"] - r4["pnl"]) > 500:
            driver += f"Wick stopped out ({r4['pnl']-r3['pnl']:>+6.0f}); "
        if not driver:
            driver = "Identical behavior"

        print(f"{w_id:<8} | {r1['pnl']:>+9.1f} TMN | {r2['pnl']:>+10.1f} TMN | {r3['pnl']:>+9.1f} TMN | {r4['pnl']:>+10.1f} TMN | {driver}")

    print("=" * 105)

    # Analyze Stage 3 vs Stage 4 (Intra-bar Stop Loss Analysis)
    print("\n" + "=" * 105)
    print("ANALYSIS OF INTRA-BAR WICK STOP-OUTS (Stage 3 -> Stage 4)")
    print("=" * 105)
    for i, t3 in t3_df.iterrows():
        # find matching trade in t4
        match = t4_df[(t4_df["window_id"] == t3["window_id"]) & (t4_df["symbol"] == t3["symbol"])]
        if not match.empty:
            t4 = match.iloc[0]
            if t3["exit_reason"] != t4["exit_reason"] or abs(t3["net_pnl"] - t4["net_pnl"]) > 500:
                print(f"Window {t3['window_id']} ({t3['symbol']}): Stage 3={t3['exit_reason']} ({t3['net_pnl']:>+8.1f} TMN) -> Stage 4={t4['exit_reason']} ({t4['net_pnl']:>+8.1f} TMN) | Delta = {t4['net_pnl'] - t3['net_pnl']:>+8.1f} TMN")


if __name__ == "__main__":
    run_trade_reconciliation()
