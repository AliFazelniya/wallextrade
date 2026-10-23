"""Unified Competition Simulation Harness for Phase 22 Strategy Discovery.

Evaluates any trading strategy across independent 72-hour competition windows
with strict competition realism:
- 5,000,000 TMN initial cash reset per window
- Zero carried positions across boundaries
- Realistic Wallex Level 1 fees (0.25% maker / 0.30% taker)
- Modeled execution slippage (0.15%)
- Mark-to-market drawdown accounting
- Full accounting of terminal liquidations and graceful wind-downs
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass
class WindowResult:
    window_id: str
    start_utc: str
    end_utc: str
    is_complete: bool
    duration_hours: float
    observed_bars: int
    trades_count: int
    initial_equity: float
    final_equity: float
    net_pnl_toman: float
    net_return_pct: float
    max_drawdown_tmn: float
    max_drawdown_pct: float
    exposure_hours: float
    exposure_pct: float
    total_fees_toman: float
    total_slippage_toman: float
    boundary_liquidated: bool
    status: str  # WIN, LOSS, NEUTRAL


@dataclass
class CompetitionSummary:
    strategy_name: str
    total_windows: int
    complete_windows: int
    profitable_windows: int
    losing_windows: int
    neutral_windows: int
    zero_trade_windows: int
    active_windows: int
    win_rate_all_pct: float
    win_rate_active_pct: float
    aggregate_net_pnl_toman: float
    mean_72h_return_pct: float
    median_72h_return_pct: float
    std_72h_return_pct: float
    sem_pct: float
    t_stat: float
    ci_95_low: float
    ci_95_high: float
    min_72h_return_pct: float
    max_72h_return_pct: float
    mean_max_drawdown_pct: float
    worst_max_drawdown_pct: float
    mean_exposure_hours: float
    total_trades: int
    mean_trades_per_window: float
    total_fees_toman: float
    total_slippage_toman: float
    total_friction_toman: float
    window_results: List[WindowResult] = field(default_factory=list)


class CompetitionSimulator:
    """Runs rigorous 72-hour competition simulations."""

    def __init__(
        self,
        df_features: pd.DataFrame,
        maker_fee: float = 0.0025,
        taker_fee: float = 0.0030,
        slippage_pct: float = 0.15,
        initial_capital: float = 5_000_000.0,
        warmup_bars: int = 60,
        window_hours: float = 72.0,
    ):
        self.df = df_features.sort_values("dt").reset_index(drop=True)
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage_pct = slippage_pct
        self.initial_capital = initial_capital
        self.warmup_bars = warmup_bars
        self.window_duration = pd.Timedelta(hours=window_hours)
        
        self.t0 = self.df["dt"].iloc[warmup_bars]
        self.t_end = self.df["dt"].iloc[-1]

    def evaluate_strategy(
        self,
        strategy_name: str,
        signal_generator: Callable[[pd.DataFrame, int, float, Optional[Dict[str, Any]], Dict[str, Any]], Optional[Dict[str, Any]]],
        exit_evaluator: Callable[[Dict[str, Any], pd.Series, float, Dict[str, Any]], Optional[Dict[str, Any]]],
    ) -> CompetitionSummary:
        """Evaluates a strategy across all independent windows.
        
        signal_generator signature:
            (df_slice, current_bar_idx, elapsed_hours_in_window, open_position_or_none, context) -> order_dict or None
            order_dict: {'action': 'BUY', 'notional_toman': float, 'is_maker': bool}
            
        exit_evaluator signature:
            (open_position, current_bar, elapsed_hours_in_window, context) -> exit_dict or None
            exit_dict: {'reason': str, 'is_maker': bool, 'price_override': Optional[float]}
        """
        cur_start = self.t0
        w_idx = 1
        window_results: List[WindowResult] = []
        
        while cur_start < self.t_end:
            cur_end = cur_start + self.window_duration
            is_complete = cur_end <= self.t_end
            actual_end = min(cur_end, self.t_end)
            
            mask = (self.df["dt"] >= cur_start) & (self.df["dt"] < cur_end)
            w_df = self.df[mask]
            obs = len(w_df)
            
            cash = self.initial_capital
            open_pos: Optional[Dict[str, Any]] = None
            trades_in_window: List[Dict[str, Any]] = []
            equity_curve: List[float] = [self.initial_capital]
            exposure_bars = 0
            w_fees = 0.0
            w_slippage = 0.0
            context: Dict[str, Any] = {"window_idx": w_idx, "is_complete": is_complete}
            
            w_indices = w_df.index.tolist()
            for step_i, idx in enumerate(w_indices):
                bar = self.df.iloc[idx]
                cur_p = float(bar["close"])
                elapsed_hours = (step_i * 15.0) / 60.0
                
                # 1. Update mark-to-market
                if open_pos is not None:
                    exposure_bars += 1
                    pos_val = open_pos["qty"] * cur_p
                    equity = cash + pos_val
                else:
                    equity = cash
                    
                # 2. Check Exit if in position
                if open_pos is not None:
                    exit_decision = exit_evaluator(open_pos, bar, elapsed_hours, context)
                    if exit_decision is not None:
                        is_maker = exit_decision.get("is_maker", False)
                        fee_rate = self.maker_fee if is_maker else self.taker_fee
                        
                        slip = cur_p * (self.slippage_pct / 100.0) if not is_maker else 0.0
                        override = exit_decision.get("price_override")
                        exit_px = override if override is not None else (cur_p - slip)
                        
                        gross_proceeds = open_pos["qty"] * exit_px
                        fee = gross_proceeds * fee_rate
                        net_proceeds = gross_proceeds - fee
                        
                        cash += net_proceeds
                        w_fees += fee
                        w_slippage += open_pos["qty"] * slip
                        
                        trades_in_window.append({
                            "type": exit_decision.get("reason", "EXIT"),
                            "entry_price": open_pos["entry_px"],
                            "exit_price": exit_px,
                            "net_pnl": net_proceeds - open_pos["net_entry_cost"],
                            "is_maker": is_maker,
                        })
                        open_pos = None
                        equity = cash
                
                # 3. Check Entry if flat
                if open_pos is None:
                    order = signal_generator(self.df.iloc[:idx+1], idx, elapsed_hours, open_pos, context)
                    if order is not None and order.get("action") == "BUY":
                        notional = min(order.get("notional_toman", 500_000.0), cash * 0.60)
                        if notional >= 50_000.0 and cash >= notional:
                            is_maker = order.get("is_maker", False)
                            fee_rate = self.maker_fee if is_maker else self.taker_fee
                            slip = cur_p * (self.slippage_pct / 100.0) if not is_maker else 0.0
                            entry_px = cur_p + slip
                            
                            qty = notional / entry_px
                            entry_fee = notional * fee_rate
                            net_cost = notional + entry_fee
                            
                            if cash >= net_cost:
                                cash -= net_cost
                                w_fees += entry_fee
                                w_slippage += qty * slip
                                open_pos = {
                                    "qty": qty,
                                    "entry_px": entry_px,
                                    "raw_entry_px": cur_p,
                                    "entry_bar": idx,
                                    "entry_step": step_i,
                                    "entry_time": bar["dt"],
                                    "notional": notional,
                                    "net_entry_cost": net_cost,
                                    "atr_at_entry": float(bar.get("atr_14", cur_p * 0.015)),
                                }
                                equity = cash + (qty * cur_p)
                                
                equity_curve.append(equity)
            
            # 4. End-of-window forced liquidation if position still open
            boundary_liq = False
            if open_pos is not None:
                boundary_liq = True
                last_p = float(w_df.iloc[-1]["close"])
                slip = last_p * (self.slippage_pct / 100.0)
                exit_px = last_p - slip
                
                gross_proceeds = open_pos["qty"] * exit_px
                fee = gross_proceeds * self.taker_fee
                net_proceeds = gross_proceeds - fee
                
                cash += net_proceeds
                w_fees += fee
                w_slippage += open_pos["qty"] * slip
                
                trades_in_window.append({
                    "type": "FORCED_BOUNDARY_LIQUIDATION",
                    "entry_price": open_pos["entry_px"],
                    "exit_price": exit_px,
                    "net_pnl": net_proceeds - open_pos["net_entry_cost"],
                    "is_maker": False,
                })
                open_pos = None
                equity_curve.append(cash)
            
            final_equity = cash
            net_pnl = final_equity - self.initial_capital
            net_ret = (net_pnl / self.initial_capital) * 100.0
            
            eq_s = pd.Series(equity_curve)
            peak = eq_s.cummax()
            dd_tmn = peak - eq_s
            max_dd_tmn = float(dd_tmn.max())
            max_dd_pct = (max_dd_tmn / float(peak.max())) * 100.0 if float(peak.max()) > 0 else 0.0
            
            status = "WIN" if net_ret > 0.001 else ("LOSS" if net_ret < -0.001 else "NEUTRAL")
            
            window_results.append(WindowResult(
                window_id=f"W{w_idx:02d}",
                start_utc=str(cur_start),
                end_utc=str(cur_end),
                is_complete=is_complete,
                duration_hours=(actual_end - cur_start).total_seconds() / 3600.0,
                observed_bars=obs,
                trades_count=len(trades_in_window),
                initial_equity=self.initial_capital,
                final_equity=final_equity,
                net_pnl_toman=net_pnl,
                net_return_pct=net_ret,
                max_drawdown_tmn=max_dd_tmn,
                max_drawdown_pct=max_dd_pct,
                exposure_hours=exposure_bars * 0.25,
                exposure_pct=(exposure_bars / obs) * 100.0 if obs > 0 else 0.0,
                total_fees_toman=w_fees,
                total_slippage_toman=w_slippage,
                boundary_liquidated=boundary_liq,
                status=status,
            ))
            
            cur_start = cur_end
            w_idx += 1
            
        # Compile Summary for Complete Windows (Primary Benchmark N=29)
        comp_windows = [w for w in window_results if w.is_complete]
        n_comp = len(comp_windows)
        
        rets = [w.net_return_pct for w in comp_windows]
        wins = sum(1 for w in comp_windows if w.status == "WIN")
        losses = sum(1 for w in comp_windows if w.status == "LOSS")
        neutrals = sum(1 for w in comp_windows if w.status == "NEUTRAL")
        zero_trades = sum(1 for w in comp_windows if w.trades_count == 0)
        active_windows = n_comp - zero_trades
        
        mean_ret = float(np.mean(rets)) if n_comp > 0 else 0.0
        median_ret = float(np.median(rets)) if n_comp > 0 else 0.0
        std_ret = float(np.std(rets, ddof=1)) if n_comp > 1 else 0.0
        sem = std_ret / math.sqrt(n_comp) if n_comp > 0 else 0.0
        t_stat = mean_ret / sem if sem > 0 else 0.0
        
        # 95% t-interval (df=28, t_crit approx 2.048)
        ci_low = mean_ret - 2.048 * sem
        ci_high = mean_ret + 2.048 * sem
        
        agg_pnl = sum(w.net_pnl_toman for w in comp_windows)
        tot_trades = sum(w.trades_count for w in comp_windows)
        tot_fees = sum(w.total_fees_toman for w in comp_windows)
        tot_slip = sum(w.total_slippage_toman for w in comp_windows)
        
        return CompetitionSummary(
            strategy_name=strategy_name,
            total_windows=len(window_results),
            complete_windows=n_comp,
            profitable_windows=wins,
            losing_windows=losses,
            neutral_windows=neutrals,
            zero_trade_windows=zero_trades,
            active_windows=active_windows,
            win_rate_all_pct=(wins / n_comp * 100.0) if n_comp > 0 else 0.0,
            win_rate_active_pct=(wins / active_windows * 100.0) if active_windows > 0 else 0.0,
            aggregate_net_pnl_toman=agg_pnl,
            mean_72h_return_pct=mean_ret,
            median_72h_return_pct=median_ret,
            std_72h_return_pct=std_ret,
            sem_pct=sem,
            t_stat=t_stat,
            ci_95_low=ci_low,
            ci_95_high=ci_high,
            min_72h_return_pct=min(rets) if rets else 0.0,
            max_72h_return_pct=max(rets) if rets else 0.0,
            mean_max_drawdown_pct=float(np.mean([w.max_drawdown_pct for w in comp_windows])),
            worst_max_drawdown_pct=max(w.max_drawdown_pct for w in comp_windows),
            mean_exposure_hours=float(np.mean([w.exposure_hours for w in comp_windows])),
            total_trades=tot_trades,
            mean_trades_per_window=tot_trades / n_comp if n_comp > 0 else 0.0,
            total_fees_toman=tot_fees,
            total_slippage_toman=tot_slip,
            total_friction_toman=tot_fees + tot_slip,
            window_results=window_results,
        )
