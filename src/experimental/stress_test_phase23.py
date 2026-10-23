"""Phase 23 Comprehensive Stress Testing Matrix for MultiAssetMomentumStrategy."""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path("/root/starcoach-hack/wallex")
sys.path.insert(0, str(REPO_ROOT))

from src.experimental.audit_phase22 import load_all_assets, simulate_candidate_e


def run_phase23_stress_matrix():
    print("=" * 95)
    print("PHASE 23: COMPREHENSIVE EXECUTION STRESS TESTING MATRIX")
    print("Strategy: Productionized MultiAssetMomentumStrategy (with AI Regime Agent)")
    print("Horizon: 29 Independent 72-Hour Competition Windows (Initial Capital: 5M TMN)")
    print("=" * 95)

    btc, eth, sol, common_idx = load_all_assets(clean_lookahead=True)

    scenarios = [
        ("1. Baseline (0.15% slip, 0.25%/0.30% fees)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030)),
        ("2. High Slippage (0.30% slip)", dict(slippage_pct=0.30, maker_fee=0.0025, taker_fee=0.0030)),
        ("3. Severe Slippage (0.50% slip)", dict(slippage_pct=0.50, maker_fee=0.0025, taker_fee=0.0030)),
        ("4. Promotional Fee Scenario (0.08% flat fee)", dict(slippage_pct=0.15, maker_fee=0.0008, taker_fee=0.0008)),
        ("5. High Fee Scenario (0.40% taker fee)", dict(slippage_pct=0.15, maker_fee=0.0030, taker_fee=0.0040)),
        ("6. Strict Intra-bar High/Low Wicks", dict(check_intrabar_extremes=True, slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030)),
    ]

    results = []
    print(f"\n{'Scenario Name':<46} | {'Net PnL (TMN)':<15} | {'Mean Ret':<8} | {'Win%':<6} | {'Trades':<6} | {'Friction (TMN)'}")
    print("-" * 105)

    for name, kwargs in scenarios:
        df_res, trades = simulate_candidate_e(btc, eth, sol, common_idx, use_ai_agent=True, **kwargs)
        pnl = df_res["pnl"].sum()
        mean_ret = df_res["ret"].mean()
        wins = (df_res["ret"] > 0.001).sum()
        win_rate = (wins / len(df_res)) * 100.0
        tot_trades = df_res["trades"].sum()
        fric = df_res["friction"].sum()
        results.append({
            "scenario": name,
            "pnl": pnl,
            "mean_ret": mean_ret,
            "win_rate": win_rate,
            "trades": tot_trades,
            "friction": fric,
        })
        print(f"{name:<46} | {pnl:>+11.1f} TMN | {mean_ret:>+6.3f}% | {win_rate:>4.1f}% | {tot_trades:>4} | {fric:>10.0f} TMN")

    print("=" * 105)
    return results


if __name__ == "__main__":
    run_phase23_stress_matrix()
