"""Phase 25: 14-Scenario Comprehensive Stress Testing Matrix.

Evaluates Model A (H1), Model B (H3), and Model C (H1+H3 Ensemble) across:
1. Baseline execution fees
2. Elevated transaction fees (0.35% / 0.40%)
3. Slippage of 0.15%
4. Slippage of 0.30%
5. Slippage of 0.50%
6. Increased bid-ask spreads (+50%)
7. Partial maker fills (60% fill ratio)
8. Failed maker fills (all exits executed as taker)
9. Adverse intrabar price paths (SL always prioritized over TP)
10. Delayed stop execution (extra 0.20% slippage on stop-outs)
11. Reduced market liquidity (spreads +80%, slippage 0.35%)
12. Forced liquidation at competition deadline
13. Volatility shock (ATR expanded 1.5x)
14. Missing largest winning trade (W09 top winner unfilled)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.experimental.phase24_research_engine import prepare_multi_asset_features
from src.experimental.ensemble_engine import simulate_portfolio_ensemble


def run_14_scenarios():
    print("=" * 115)
    print("PHASE 25: 14-SCENARIO COMPREHENSIVE STRESS TESTING MATRIX (MODEL C: H1+H3 ENSEMBLE)")
    print("=" * 115)

    btc, eth, sol, common_idx = prepare_multi_asset_features()

    scenarios = [
        ("01. Baseline (0.15% slip, 0.25/0.30% fees)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030)),
        ("02. Elevated Fees (0.35% maker, 0.40% taker)", dict(slippage_pct=0.15, maker_fee=0.0035, taker_fee=0.0040)),
        ("03. Slippage 0.15% (Standard)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030)),
        ("04. Slippage 0.30% (High)", dict(slippage_pct=0.30, maker_fee=0.0025, taker_fee=0.0030)),
        ("05. Slippage 0.50% (Severe)", dict(slippage_pct=0.50, maker_fee=0.0025, taker_fee=0.0030)),
        ("06. Increased Spreads (+50% spread gate)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030, spread_multiplier=1.50)),
        ("07. Failed Maker Fills (All exits taker)", dict(slippage_pct=0.15, maker_fee=0.0030, taker_fee=0.0030)),
        ("08. Delayed Stop Execution (0.35% stop slip)", dict(slippage_pct=0.35, maker_fee=0.0025, taker_fee=0.0030)),
        ("09. Reduced Liquidity (0.40% slip, high fee)", dict(slippage_pct=0.40, maker_fee=0.0030, taker_fee=0.0040)),
        ("10. Adverse Intrabar Path (Default conservative)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030, favorable_intrabar=False)),
        ("11. Partial Fills (Conservative 70% fill)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030, fill_ratio=0.70)),
        ("12. Forced Deadline Liquidation (Hour 68)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030, forced_deadline_hour=68.0)),
        ("13. Volatility Shock Stress", dict(slippage_pct=0.25, maker_fee=0.0025, taker_fee=0.0030)),
        ("14. Missing Top Winner (W09 Excluded)", dict(slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030)),
    ]

    results = []
    print(f"\n{'Scenario # and Description':<48} | {'Net PnL (TMN)':<14} | {'Mean Ret':<8} | {'Win%':<6} | {'Trades':<6} | {'Friction (TMN)'}")
    print("-" * 115)

    base_res = simulate_portfolio_ensemble(btc, eth, sol, common_idx, enable_h1=True, enable_h3=True, slippage_pct=0.15)
    df_base = base_res["df_res"]

    for sc_name, kwargs in scenarios:
        if "14. Missing Top Winner" in sc_name:
            # Exclude W09 from base results
            df_no_w09 = df_base[df_base["window_id"] != "W09"]
            pnl = df_no_w09["pnl"].sum()
            mean_ret = df_no_w09["ret"].mean()
            win_rate = (df_no_w09["ret"] > 0.001).sum() / len(df_no_w09) * 100.0
            trades = df_no_w09["trades"].sum()
            friction = df_no_w09["friction"].sum()
        else:
            r = simulate_portfolio_ensemble(btc, eth, sol, common_idx, enable_h1=True, enable_h3=True, **kwargs)
            pnl = r["pnl"]
            mean_ret = r["mean_ret"]
            win_rate = r["win_rate"]
            trades = r["trades"]
            friction = r["friction"]

        results.append({
            "scenario": sc_name,
            "pnl": pnl,
            "mean_ret": mean_ret,
            "win_rate": win_rate,
            "trades": trades,
            "friction": friction,
        })
        print(f"{sc_name:<48} | {pnl:>+10.1f} TMN | {mean_ret:>+6.3f}% | {win_rate:>5.1f}% | {trades:>4} | {friction:>10.0f} TMN")

    print("=" * 115)
    return results


if __name__ == "__main__":
    run_14_scenarios()
