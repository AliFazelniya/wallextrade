"""Phase 25: Controlled AI Ablation Study for H1+H3 Ensemble.

Compares 3 distinct configurations under identical execution conditions:
1. Config 1: Purely Deterministic H1+H3 (No AI Agent)
2. Config 2: H1+H3 with Phase 23 RegimeClassificationAgent
3. Config 3: H1+H3 with Cost-Sensitive Probabilistic AI Quality Evaluator
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
from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import MarketFeaturesInput, MarketRegime


class CostSensitiveAIEvaluator:
    """Evaluates whether an H1 or H3 signal has a positive expected net edge after fees."""

    def __init__(self, min_edge_threshold_pct: float = 0.40):
        self.min_edge_threshold_pct = min_edge_threshold_pct
        # Weights calibrated on rolling statistical features:
        # High ADX (+), Strong Trend (+), Volume Ratio (+), Wide Spread (-), High ATR (-)
        self.w_adx = 0.04
        self.w_vol = 0.35
        self.w_mom = 0.40
        self.w_spr = -4.50
        self.w_atr = -0.20
        self.bias = -0.20

    def evaluate_trade_opportunity(
        self,
        symbol: str,
        source: str,
        bar: pd.Series,
        current_spread_pct: float,
        target_tp_pct: float,
        target_sl_pct: float,
        round_trip_friction_pct: float = 0.70,
    ) -> Tuple[bool, float, float, str]:
        """Calculates calibrated probability of winning and expected net edge.
        
        Returns: (approved, win_prob, net_edge_pct, rationale)
        """
        adx = float(bar.get("adx_14", 20.0))
        vol_r = float(bar.get("vol_ratio", 1.0))
        mom = float(bar.get("ema_spread_pct", 0.0))
        atr_pct = float(bar.get("atr_pct", 1.5))

        # Logit computation
        z = (
            self.bias
            + self.w_adx * (adx - 20.0)
            + self.w_vol * (vol_r - 1.0)
            + self.w_mom * mom
            + self.w_spr * current_spread_pct
            + self.w_atr * (atr_pct - 1.5)
        )
        # Sigmoid calibrated probability of winning
        p_win = 1.0 / (1.0 + math.exp(-max(-8.0, min(8.0, z))))

        # Expected net edge: E[R] = P(Win) * TP - (1 - P(Win)) * SL - Friction
        expected_edge = (p_win * target_tp_pct) - ((1.0 - p_win) * target_sl_pct) - round_trip_friction_pct

        approved = expected_edge >= self.min_edge_threshold_pct
        rationale = f"AI Evaluator: P(Win)={p_win:.2%}, Net Edge={expected_edge:+.2f}%, Spread={current_spread_pct:.3f}%"
        return approved, p_win, expected_edge, rationale


def simulate_ai_ablation(
    btc: pd.DataFrame,
    eth: pd.DataFrame,
    sol: pd.DataFrame,
    common_idx: pd.Index,
    ai_mode: str = "NONE",  # "NONE" | "PHASE23_REGIME" | "COST_SENSITIVE"
    maker_fee: float = 0.0025,
    taker_fee: float = 0.0030,
    slippage_pct: float = 0.15,
) -> Dict[str, Any]:
    t0 = common_idx[60]
    t_end = common_idx[-1]
    window_dur = pd.Timedelta(hours=72)

    regime_agent = RegimeClassificationAgent() if ai_mode == "PHASE23_REGIME" else None
    ai_evaluator = CostSensitiveAIEvaluator() if ai_mode == "COST_SENSITIVE" else None

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

            # 1. Check Exits
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

                is_sl = pnl_low <= -sl_pct
                is_tp = pnl_high >= tp_pct and not is_sl
                is_be = pos.get("reached_25", False) and pnl_close <= 0.80 and source == "H1"
                if pnl_high >= 2.5:
                    pos["reached_25"] = True
                is_winddown = elapsed_h >= 66.0 and pnl_close >= 0.50

                if is_sl or is_tp or is_be or is_winddown:
                    is_maker = is_tp or is_be or is_winddown
                    fee_rate = maker_fee if is_maker else taker_fee
                    slip = cur_close * (slippage_pct / 100.0) if not is_maker else 0.0

                    if is_sl:
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
                        "reason": reason,
                        "net_pnl": net_pnl,
                        "is_maker": is_maker,
                    })
                    closed_syms.append(sym)

            for sym in closed_syms:
                del positions[sym]

            # 2. Check Entries with AI Gating
            if len(positions) < 2 and elapsed_h < 60.0 and cash >= 550_000.0:
                candidate_signals = []

                # H3 Generator
                btc_mom = float(b_bar["ema_spread_pct"])
                btc_vol = float(b_bar["vol_ratio"])
                btc_rsi = float(b_bar["rsi_14"])
                btc_is_surging = (b_bar["ema_20"] > b_bar["ema_50"]) and (btc_vol >= 1.40) and (55 <= btc_rsi <= 70) and (btc_mom >= 0.6)

                if btc_is_surging:
                    sol_spr = float(s_bar["dynamic_spread"])
                    sol_rsi = float(s_bar["rsi_14"])
                    if "SOL" not in positions and sol_spr <= 0.18 and (50 <= sol_rsi <= 65) and s_bar["ema_20"] > s_bar["ema_50"]:
                        candidate_signals.append({"symbol": "SOL", "source": "H3", "bar": s_bar, "spr": sol_spr, "score": 2.5, "tp": 3.5, "sl": 1.8})
                    eth_spr = float(e_bar["dynamic_spread"])
                    eth_rsi = float(e_bar["rsi_14"])
                    if "ETH" not in positions and eth_spr <= 0.16 and (50 <= eth_rsi <= 65) and e_bar["ema_20"] > e_bar["ema_50"]:
                        candidate_signals.append({"symbol": "ETH", "source": "H3", "bar": e_bar, "spr": eth_spr, "score": 2.2, "tp": 3.5, "sl": 1.8})

                # H1 Generator
                for sym, bar in [("BTC", b_bar), ("ETH", e_bar), ("SOL", s_bar)]:
                    if sym in positions:
                        continue
                    cur_p = float(bar["close"])
                    spr = float(bar["dynamic_spread"])
                    mom_15m = float(bar["ema_spread_pct"])
                    trend_1h = bool(bar["trend_1h_bullish"])
                    rsi = float(bar["rsi_14"])
                    vol_r = float(bar["vol_ratio"])
                    adx = float(bar["adx_14"])

                    if trend_1h and bar["ema_20"] > bar["ema_50"] and (52 <= rsi <= 68) and vol_r >= 1.25 and spr <= 0.16 and adx >= 24.0:
                        score = (mom_15m / (float(bar["atr_pct"]) + 1e-6)) * (1.0 - (spr / 0.35))
                        if score >= 1.2:
                            candidate_signals.append({"symbol": sym, "source": "H1", "bar": bar, "spr": spr, "score": score, "tp": 4.5, "sl": 2.2})

                # AI Gating Layer
                approved_signals = []
                for cand in candidate_signals:
                    sym = cand["symbol"]
                    c_bar = cand["bar"]
                    spr = cand["spr"]

                    if ai_mode == "NONE":
                        approved_signals.append(cand)

                    elif ai_mode == "PHASE23_REGIME" and regime_agent is not None:
                        feat_in = MarketFeaturesInput(
                            symbol=f"{sym}TMN",
                            price_toman=float(c_bar["close"]),
                            ema_spread_pct=float(c_bar["ema_spread_pct"]),
                            rsi_14=float(c_bar["rsi_14"]),
                            atr_pct=float(c_bar["atr_pct"]),
                            vol_ratio=float(c_bar["vol_ratio"]),
                            spread_pct=spr,
                            trend_direction="BULLISH",
                        )
                        reg_out = regime_agent._deterministic_fallback(feat_in)
                        if reg_out.regime == MarketRegime.BULLISH_TREND and reg_out.confidence >= 0.70:
                            approved_signals.append(cand)

                    elif ai_mode == "COST_SENSITIVE" and ai_evaluator is not None:
                        ok, prob, edge, rat = ai_evaluator.evaluate_trade_opportunity(
                            symbol=sym,
                            source=cand["source"],
                            bar=c_bar,
                            current_spread_pct=spr,
                            target_tp_pct=cand["tp"],
                            target_sl_pct=cand["sl"],
                            round_trip_friction_pct=0.70,
                        )
                        if ok:
                            cand["score"] = cand["score"] * (1.0 + edge)
                            approved_signals.append(cand)

                if approved_signals:
                    approved_signals.sort(key=lambda x: x["score"], reverse=True)
                    best = approved_signals[0]
                    tgt_sym = best["symbol"]
                    c_bar = best["bar"]
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
                    positions[tgt_sym] = {
                        "symbol": tgt_sym,
                        "source": best["source"],
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

        # 4. Terminal Liquidation
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

    return {
        "mode": ai_mode,
        "pnl": agg_pnl,
        "mean_ret": mean_ret,
        "t_stat": t_stat,
        "win_rate": (wins / len(df_res) * 100.0) if len(df_res) > 0 else 0,
        "trades": df_res["trades"].sum(),
        "friction": df_res["friction"].sum(),
        "max_dd": df_res["max_dd"].max(),
        "df_res": df_res,
        "trades_list": trade_records,
    }


def main():
    print("=" * 105)
    print("PHASE 25: THREE-WAY AI ABLATION STUDY FOR H1+H3 ENSEMBLE")
    print("=" * 105)

    btc, eth, sol, common_idx = prepare_multi_asset_features()

    res_none = simulate_ai_ablation(btc, eth, sol, common_idx, ai_mode="NONE")
    res_phase23 = simulate_ai_ablation(btc, eth, sol, common_idx, ai_mode="PHASE23_REGIME")
    res_cost = simulate_ai_ablation(btc, eth, sol, common_idx, ai_mode="COST_SENSITIVE")

    ablations = [
        ("1. Purely Deterministic (No AI Agent)", res_none),
        ("2. Phase 23 RegimeClassificationAgent", res_phase23),
        ("3. Cost-Sensitive Probabilistic AI Evaluator", res_cost),
    ]

    print(f"\n{'Ablation Configuration':<46} | {'PnL (TMN)':<12} | {'Mean Ret':<8} | {'Win%':<6} | {'Trades':<6} | {'T-Stat':<7} | {'MaxDD%':<6} | {'Friction'}")
    print("-" * 105)
    for name, r in ablations:
        print(f"{name:<46} | {r['pnl']:>+10.1f} TMN | {r['mean_ret']:>+6.3f}% | {r['win_rate']:>5.1f}% | {r['trades']:>4} | {r['t_stat']:>+6.2f} | {r['max_dd']:>5.2f}% | {r['friction']:>8.0f} TMN")
    print("=" * 105)


if __name__ == "__main__":
    main()
