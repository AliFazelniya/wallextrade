"""Unified Experiment Runner for Phase 22 Strategy Discovery.

Evaluates:
- Baseline 1: Frozen Phase 21 AI Baseline (Regime Momentum, no wind-down)
- Baseline 2: Deterministic Baseline (pure EMA cross, no AI, no wind-down)
- Baseline 3: 100% Cash Baseline (Zero risk, zero return)
- Candidate A: Adaptive Trend + Graceful Wind-down & Trailing Stop
- Candidate B: Short-Horizon Volatility Breakout (Donchian + ADX + Time Stop)
- Candidate C: Range-Bound Mean Reversion (Bollinger + RSI + Cost Hurdle)
- Candidate D: Agentic Meta-Strategy Router (Dynamic Regime Allocation)
- Candidate E: Multi-Asset Cross-Sectional Selection (BTC + ETH + SOL)
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path("/root/starcoach-hack/wallex")
sys.path.insert(0, str(REPO_ROOT))

from src.experimental.features import extract_advanced_features
from src.experimental.simulation_harness import CompetitionSimulator, CompetitionSummary
from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import MarketRegime, ActionType, MarketFeaturesInput


def load_dataset(symbol: str) -> pd.DataFrame:
    csv_path = REPO_ROOT / "data" / "cache" / f"{symbol}_15m_90d.csv"
    df = pd.read_csv(csv_path)
    df["dt"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("dt").reset_index(drop=True)
    return extract_advanced_features(df)


# =====================================================================
# 1. BASELINE 1: FROZEN PHASE 21 AI STRATEGY (Re-implementation in Harness)
# =====================================================================
def get_baseline_ai_strategy(agent: RegimeClassificationAgent):
    def signal_gen(df_slice, idx, elapsed_hours, open_pos, ctx):
        bar = df_slice.iloc[-1]
        cur_p = float(bar["close"])
        cur_spread = float(bar["dynamic_spread"])
        
        # Candidate technical check
        is_candidate = (
            bar["ema_20"] > bar["ema_50"]
            and (50.0 <= bar["rsi_14"] <= 69.0)
            and bar["vol_ratio"] >= 1.10
        )
        if not is_candidate or cur_spread > 0.20 or open_pos is not None:
            return None
            
        feat_in = MarketFeaturesInput(
            symbol="BTCTMN",
            price_toman=cur_p,
            ema_spread_pct=float(bar["ema_spread_pct"]),
            rsi_14=float(bar["rsi_14"]),
            atr_pct=float(bar["atr_pct"]),
            vol_ratio=float(bar["vol_ratio"]),
            spread_pct=cur_spread,
            trend_direction="BULLISH",
        )
        reg_out = agent._deterministic_fallback(feat_in)
        if reg_out.regime == MarketRegime.BULLISH_TREND and reg_out.confidence >= 0.70:
            return {"action": "BUY", "notional_toman": 500_000.0, "is_maker": False}
        return None

    def exit_eval(pos, current_bar, elapsed_hours, ctx):
        cur_p = float(current_bar["close"])
        entry_p = pos["entry_px"]
        pnl_pct = (cur_p - entry_p) / entry_p * 100.0
        
        # Frozen baseline rules: TP = 4.0%, SL = 2.0%
        if pnl_pct >= 4.0:
            return {"reason": "TAKE_PROFIT", "is_maker": True, "price_override": cur_p}
        if pnl_pct <= -2.0:
            return {"reason": "STOP_LOSS", "is_maker": False, "price_override": None}
        return None

    return signal_gen, exit_eval


# =====================================================================
# 2. BASELINE 2: DETERMINISTIC BASELINE (No AI)
# =====================================================================
def get_deterministic_strategy():
    def signal_gen(df_slice, idx, elapsed_hours, open_pos, ctx):
        bar = df_slice.iloc[-1]
        cur_spread = float(bar["dynamic_spread"])
        is_candidate = (
            bar["ema_20"] > bar["ema_50"]
            and (50.0 <= bar["rsi_14"] <= 69.0)
            and bar["vol_ratio"] >= 1.10
        )
        if is_candidate and cur_spread <= 0.20 and open_pos is None:
            return {"action": "BUY", "notional_toman": 500_000.0, "is_maker": False}
        return None

    def exit_eval(pos, current_bar, elapsed_hours, ctx):
        cur_p = float(current_bar["close"])
        entry_p = pos["entry_px"]
        pnl_pct = (cur_p - entry_p) / entry_p * 100.0
        if pnl_pct >= 4.0:
            return {"reason": "TAKE_PROFIT", "is_maker": True, "price_override": cur_p}
        if pnl_pct <= -2.0:
            return {"reason": "STOP_LOSS", "is_maker": False, "price_override": None}
        return None

    return signal_gen, exit_eval


# =====================================================================
# 3. CANDIDATE A: ADAPTIVE HORIZON & GRACEFUL WIND-DOWN
# =====================================================================
def get_candidate_a_strategy(agent: RegimeClassificationAgent):
    def signal_gen(df_slice, idx, elapsed_hours, open_pos, ctx):
        # 1. No new entry after hour 60 (12-hour finite-horizon buffer)
        if elapsed_hours >= 60.0:
            return None
            
        bar = df_slice.iloc[-1]
        cur_p = float(bar["close"])
        cur_spread = float(bar["dynamic_spread"])
        
        is_candidate = (
            bar["ema_20"] > bar["ema_50"]
            and (50.0 <= bar["rsi_14"] <= 68.0)
            and bar["vol_ratio"] >= 1.10
        )
        if not is_candidate or cur_spread > 0.18 or open_pos is not None:
            return None
            
        feat_in = MarketFeaturesInput(
            symbol="BTCTMN",
            price_toman=cur_p,
            ema_spread_pct=float(bar["ema_spread_pct"]),
            rsi_14=float(bar["rsi_14"]),
            atr_pct=float(bar["atr_pct"]),
            vol_ratio=float(bar["vol_ratio"]),
            spread_pct=cur_spread,
            trend_direction="BULLISH",
        )
        reg_out = agent._deterministic_fallback(feat_in)
        if reg_out.regime == MarketRegime.BULLISH_TREND and reg_out.confidence >= 0.70:
            return {"action": "BUY", "notional_toman": 500_000.0, "is_maker": False}
        return None

    def exit_eval(pos, current_bar, elapsed_hours, ctx):
        cur_p = float(current_bar["close"])
        entry_p = pos["entry_px"]
        atr = pos["atr_at_entry"]
        pnl_pct = (cur_p - entry_p) / entry_p * 100.0
        
        # Dynamic ATR-based TP and SL
        tp_pct = min(2.5, max(1.6, (2.0 * atr / entry_p) * 100.0))
        sl_pct = min(1.5, max(1.0, (1.2 * atr / entry_p) * 100.0))
        
        # Trailing break-even stop: if price was up > 1.0x ATR, lock in 0.70% to cover fees
        if pnl_pct >= (atr / entry_p * 100.0):
            pos["trailing_sl_pct"] = max(pos.get("trailing_sl_pct", -sl_pct), 0.70)
        active_sl_pct = pos.get("trailing_sl_pct", -sl_pct)
        
        if pnl_pct >= tp_pct:
            return {"reason": "TAKE_PROFIT", "is_maker": True, "price_override": cur_p}
        if pnl_pct <= active_sl_pct:
            return {"reason": "STOP_LOSS", "is_maker": False, "price_override": None}
            
        # Graceful Wind-down at hour 64 to 71:
        # If in profit (> 0.40%), close passively as Maker to secure positive return without liquidation drag
        if elapsed_hours >= 64.0 and pnl_pct >= 0.40:
            return {"reason": "GRACEFUL_PASSIVE_WIND_DOWN", "is_maker": True, "price_override": cur_p}
            
        return None

    return signal_gen, exit_eval


# =====================================================================
# 4. CANDIDATE B: SHORT-HORIZON VOLATILITY BREAKOUT (Donchian + ADX + Time Stop)
# =====================================================================
def get_candidate_b_strategy():
    def signal_gen(df_slice, idx, elapsed_hours, open_pos, ctx):
        if elapsed_hours >= 56.0 or open_pos is not None:
            return None
        bar = df_slice.iloc[-1]
        cur_p = float(bar["close"])
        cur_spread = float(bar["dynamic_spread"])
        
        # Donchian 20 High Breakout + Volume Spike + ADX >= 25
        is_breakout = (
            cur_p > bar["dc_high_20"]
            and bar["adx_14"] >= 25.0
            and bar["vol_ratio"] >= 1.40
            and cur_spread <= 0.18
        )
        if is_breakout:
            return {"action": "BUY", "notional_toman": 500_000.0, "is_maker": False}
        return None

    def exit_eval(pos, current_bar, elapsed_hours, ctx):
        cur_p = float(current_bar["close"])
        entry_p = pos["entry_px"]
        pnl_pct = (cur_p - entry_p) / entry_p * 100.0
        bars_held = ctx.get("step_i", 0) - pos["entry_step"] if "entry_step" in pos else 0
        
        # Tight targets for fast momentum: TP = +2.20%, SL = -1.30%
        if pnl_pct >= 2.20:
            return {"reason": "BREAKOUT_TP", "is_maker": True, "price_override": cur_p}
        if pnl_pct <= -1.30:
            return {"reason": "BREAKOUT_SL", "is_maker": False, "price_override": None}
            
        # Time stop: if held > 16 bars (4 hours) and PnL < 0.8%, cut trade to free capital
        if bars_held >= 16 and pnl_pct < 0.80:
            return {"reason": "TIME_HORIZON_STOP", "is_maker": False, "price_override": None}
            
        # Wind-down after hour 62
        if elapsed_hours >= 62.0 and pnl_pct > 0.30:
            return {"reason": "WIND_DOWN_EXIT", "is_maker": True, "price_override": cur_p}
            
        return None

    return signal_gen, exit_eval


# =====================================================================
# 5. CANDIDATE C: RANGE-BOUND MEAN REVERSION (Bollinger + RSI + Hurdle)
# =====================================================================
def get_candidate_c_strategy():
    def signal_gen(df_slice, idx, elapsed_hours, open_pos, ctx):
        if elapsed_hours >= 60.0 or open_pos is not None:
            return None
        bar = df_slice.iloc[-1]
        cur_p = float(bar["close"])
        cur_spread = float(bar["dynamic_spread"])
        
        # Range regime condition: ADX < 20, narrow bandwidth
        is_range = bar["adx_14"] < 20.0 and bar["bb_bandwidth"] < 3.0
        
        # Oversold lower band pierce
        is_oversold = cur_p <= bar["bb_lower"] and bar["rsi_14"] <= 30.0
        
        # Hurdle rate: distance to middle band must exceed round-trip friction (1.2%)
        dist_to_mid = (bar["bb_mid"] - cur_p) / cur_p * 100.0
        
        if is_range and is_oversold and dist_to_mid >= 1.20 and cur_spread <= 0.16:
            return {"action": "BUY", "notional_toman": 500_000.0, "is_maker": False}
        return None

    def exit_eval(pos, current_bar, elapsed_hours, ctx):
        cur_p = float(current_bar["close"])
        entry_p = pos["entry_px"]
        pnl_pct = (cur_p - entry_p) / entry_p * 100.0
        bars_held = ctx.get("step_i", 0) - pos["entry_step"] if "entry_step" in pos else 0
        
        # Target middle band or +1.5%
        target_mid = float(current_bar["bb_mid"])
        if cur_p >= target_mid or pnl_pct >= 1.60:
            return {"reason": "MEAN_REVERSION_TP", "is_maker": True, "price_override": cur_p}
        if pnl_pct <= -1.20:
            return {"reason": "MEAN_REVERSION_SL", "is_maker": False, "price_override": None}
            
        # Fast exit after 12 bars (3 hours)
        if bars_held >= 12:
            return {"reason": "MR_TIME_STOP", "is_maker": False, "price_override": None}
            
        return None

    return signal_gen, exit_eval


# =====================================================================
# 6. CANDIDATE D: AGENTIC META-STRATEGY ROUTER
# =====================================================================
def get_candidate_d_strategy(agent: RegimeClassificationAgent):
    """Dynamically routes between Breakout, Trend, Mean-Reversion or Cash."""
    strat_a_gen, strat_a_exit = get_candidate_a_strategy(agent)
    strat_b_gen, strat_b_exit = get_candidate_b_strategy()
    strat_c_gen, strat_c_exit = get_candidate_c_strategy()
    
    def signal_gen(df_slice, idx, elapsed_hours, open_pos, ctx):
        if elapsed_hours >= 60.0 or open_pos is not None:
            return None
        bar = df_slice.iloc[-1]
        adx = float(bar["adx_14"])
        spread = float(bar["dynamic_spread"])
        
        # 1. High spread / chaos -> 100% Cash preservation
        if spread > 0.20 or float(bar["atr_pct"]) > 3.5:
            ctx["sub_strategy"] = "CASH"
            return None
            
        # 2. Strong trend & momentum -> Route to Breakout / Trend
        if adx >= 24.0:
            ctx["sub_strategy"] = "BREAKOUT"
            return strat_b_gen(df_slice, idx, elapsed_hours, open_pos, ctx)
            
        # 3. Calm range -> Route to Mean-Reversion
        elif adx < 20.0:
            ctx["sub_strategy"] = "MEAN_REV"
            return strat_c_gen(df_slice, idx, elapsed_hours, open_pos, ctx)
            
        # 4. Moderate trend -> Route to Adaptive Trend
        else:
            ctx["sub_strategy"] = "ADAPTIVE_TREND"
            return strat_a_gen(df_slice, idx, elapsed_hours, open_pos, ctx)

    def exit_eval(pos, current_bar, elapsed_hours, ctx):
        sub = ctx.get("sub_strategy", "ADAPTIVE_TREND")
        if sub == "BREAKOUT":
            return strat_b_exit(pos, current_bar, elapsed_hours, ctx)
        elif sub == "MEAN_REV":
            return strat_c_exit(pos, current_bar, elapsed_hours, ctx)
        else:
            return strat_a_exit(pos, current_bar, elapsed_hours, ctx)

    return signal_gen, exit_eval


# =====================================================================
# MAIN EXECUTION
# =====================================================================
def main():
    print("=" * 80)
    print("PHASE 22: RIGOROUS COMPETITION SIMULATION & STRATEGY DISCOVERY")
    print("=" * 80)
    
    btc_df = load_dataset("BTCTMN")
    print(f"Loaded BTCTMN dataset: {len(btc_df)} bars (from {btc_df['dt'].iloc[0]} to {btc_df['dt'].iloc[-1]})")
    
    sim = CompetitionSimulator(btc_df)
    agent = RegimeClassificationAgent()
    
    candidates = [
        ("Phase 21 Frozen AI Baseline", *get_baseline_ai_strategy(agent)),
        ("Phase 21 Deterministic Baseline", *get_deterministic_strategy()),
        ("Candidate A (Adaptive Trend + Wind-Down)", *get_candidate_a_strategy(agent)),
        ("Candidate B (Donchian Volatility Breakout)", *get_candidate_b_strategy()),
        ("Candidate C (Range Mean-Reversion)", *get_candidate_c_strategy()),
        ("Candidate D (Agentic Meta-Router)", *get_candidate_d_strategy(agent)),
    ]
    
    results: List[CompetitionSummary] = []
    
    for name, s_gen, e_eval in candidates:
        print(f"\nRunning simulation for: {name} ...")
        summary = sim.evaluate_strategy(name, s_gen, e_eval)
        results.append(summary)
        print(f"  Complete Windows (N=29): PnL = {summary.aggregate_net_pnl_toman:>+10.1f} TMN | Mean Ret = {summary.mean_72h_return_pct:>+6.3f}% | Win Rate = {summary.win_rate_all_pct:>5.1f}% (Wins: {summary.profitable_windows}, Zero-trade: {summary.zero_trade_windows})")
        print(f"  T-Stat = {summary.t_stat:>+6.3f} | 95% CI = [{summary.ci_95_low:>+6.3f}%, {summary.ci_95_high:>+6.3f}%] | Max DD = {summary.worst_max_drawdown_pct:>5.2f}% | Friction = {summary.total_friction_toman:>8.0f} TMN")

    # Generate Comparative Table
    print("\n" + "=" * 105)
    print(f"{'Strategy Candidate':<36} | {'PnL (TMN)':<11} | {'Mean Ret':<8} | {'Win%':<6} | {'ZeroTr':<6} | {'T-Stat':<7} | {'MaxDD%':<6} | {'Friction':<9}")
    print("-" * 105)
    for r in results:
        print(f"{r.strategy_name:<36} | {r.aggregate_net_pnl_toman:>+9.0f} TMN | {r.mean_72h_return_pct:>+6.3f}% | {r.win_rate_all_pct:>5.1f}% | {r.zero_trade_windows:>4}/{r.complete_windows} | {r.t_stat:>+6.2f} | {r.worst_max_drawdown_pct:>5.2f}% | {r.total_friction_toman:>8.0f} TMN")
    print("=" * 105)


if __name__ == "__main__":
    main()
