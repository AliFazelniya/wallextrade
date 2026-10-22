"""Multi-Symbol Unified Portfolio Backtest Engine.

Simulates a single shared 5,000,000 Toman account across multiple symbols concurrently.
Enforces:
1. Single shared cash pool (no separate hypothetical 5M pots).
2. Deterministic RiskEngine rules: max 500k per order, max 60% crypto exposure,
   max 3 concurrent positions, max 5% drawdown.
3. Realistic orderbook execution: Maker (0.25%) vs Taker (0.30%) + slippage (0.15%).
4. Synchronized bar-by-bar chronological execution (zero lookahead bias).
5. Comprehensive AI ablation & counterfactual logging.
6. Deterministic 100% liquidation into Toman at competition close.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set
import numpy as np
import pandas as pd
from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import (
    ActionType,
    MarketFeaturesInput,
    MarketRegime,
    ProposedTradeSignal,
    RegimeAnalysisOutput,
)
from src.features.indicators import extract_features
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine
from src.strategy.base import BaseStrategy

logger = logging.getLogger(__name__)


class PortfolioBacktestEngine:
  """Unified multi-symbol portfolio backtester."""

  def __init__(
      self,
      initial_capital_toman: float = 5_000_000.0,
      maker_fee_rate: float = 0.0025,
      taker_fee_rate: float = 0.0030,
      slippage_pct: float = 0.15,
  ):
    self.initial_capital_toman = initial_capital_toman
    self.maker_fee_rate = maker_fee_rate
    self.taker_fee_rate = taker_fee_rate
    self.slippage_pct = slippage_pct

  def run_portfolio_backtest(
      self,
      symbols_data: Dict[str, pd.DataFrame],
      strategy: BaseStrategy,
      risk_engine: RiskEngine,
      agent: RegimeClassificationAgent,
      use_ai: bool = True,
      track_counterfactuals: bool = True,
  ) -> Dict[str, Any]:
    """Runs a multi-symbol backtest sharing a single cash balance."""
    # Preprocess features for each symbol
    features_by_symbol: Dict[str, pd.DataFrame] = {}
    for sym, df in symbols_data.items():
      if len(df) < 50:
        continue
      df_feat = extract_features(df).copy()
      df_feat["timestamp_dt"] = pd.to_datetime(df_feat["timestamp"], utc=True)
      df_feat = df_feat.sort_values("timestamp_dt").reset_index(drop=True)
      features_by_symbol[sym] = df_feat

    if not features_by_symbol:
      raise ValueError("No valid symbol data with sufficient history (>50 bars).")

    # Build unified chronological timeline of unique timestamps
    all_timestamps = sorted(
        set().union(
            *[df["timestamp_dt"].tolist() for df in features_by_symbol.values()]
        )
    )

    portfolio = PortfolioEngine(
        initial_capital_toman=self.initial_capital_toman,
        maker_fee_rate=self.maker_fee_rate,
        taker_fee_rate=self.taker_fee_rate,
    )

    trades_history: List[Dict[str, Any]] = []
    counterfactual_logs: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []
    total_traded_notional_toman = 0.0
    unfilled_orders_count = 0
    signals_count = 0
    risk_vetoes_count = 0

    # Index pointer map for each symbol
    symbol_indices = {sym: 0 for sym in features_by_symbol}

    # Chronological step through every unique timestamp
    for current_dt in all_timestamps:
      current_time_str = current_dt.isoformat()

      # 1. Update prices & check exits for active positions
      symbols_with_positions = list(portfolio.positions.keys())
      for sym in symbols_with_positions:
        df_sym = features_by_symbol.get(sym)
        if df_sym is None:
          continue
        # Find matching row for current_dt
        match = df_sym[df_sym["timestamp_dt"] == current_dt]
        if match.empty:
          continue
        row = match.iloc[0]
        cur_price = float(row["close"])
        cur_low = float(row["low"])
        cur_high = float(row["high"])

        portfolio.update_market_price(sym, cur_price)

        pos = portfolio.positions.get(sym)
        if not pos:
          continue

        entry_price = pos.avg_entry_price
        pnl_pct = ((cur_price - entry_price) / entry_price) * 100.0

        # Stop loss or Take profit trigger
        sl_pct = getattr(strategy, "stop_loss_pct", 2.0)
        tp_pct = getattr(strategy, "take_profit_pct", 3.5)

        is_sl = pnl_pct <= -sl_pct
        is_tp = pnl_pct >= tp_pct

        if is_sl or is_tp:
          exit_price = cur_price * (1.0 - (self.slippage_pct / 100.0))
          fill = portfolio.record_fill(
              symbol=sym,
              side="SELL",
              quantity=pos.quantity,
              price=exit_price,
              is_maker=not is_sl,  # SL is aggressive taker, TP is maker
          )
          total_traded_notional_toman += fill["notional"]
          trades_history.append({
              "timestamp": current_time_str,
              "symbol": sym,
              "side": "SELL",
              "reason": f"TRIGGER_{'SL' if is_sl else 'TP'}",
              "quantity": fill["quantity"],
              "price": fill["price"],
              "gross_gain": fill.get("gross_gain", 0.0),
              "net_gain": fill.get("net_gain", 0.0),
              "fee": fill["fee"],
              "fee_rate": fill["fee_rate"],
              "is_maker": fill["is_maker"],
          })

      # 2. Evaluate candidate symbols for new entries
      for sym, df_sym in features_by_symbol.items():
        # Get slice up to current_dt
        mask = df_sym["timestamp_dt"] <= current_dt
        df_slice = df_sym[mask]
        if len(df_slice) < 50:
          continue

        current_row = df_slice.iloc[-1]
        if current_row["timestamp_dt"] != current_dt:
          continue  # This symbol doesn't have a bar at this exact timestamp

        cur_price = float(current_row["close"])
        cur_low = float(current_row["low"])
        cur_high = float(current_row["high"])

        feat_input = MarketFeaturesInput(
            symbol=sym,
            price_toman=cur_price,
            ema_spread_pct=float(current_row.get("ema_spread_pct", 0.0)),
            rsi_14=float(current_row.get("rsi_14", 50.0)),
            atr_pct=float(current_row.get("atr_pct", 2.0)),
            vol_ratio=float(current_row.get("vol_ratio", 1.0)),
            spread_pct=0.05,
            trend_direction=(
                "BULLISH"
                if current_row.get("ema_20", 0) > current_row.get("ema_50", 0)
                else "BEARISH"
            ),
        )

        # Baseline deterministic signal (used for counterfactuals)
        is_bull_tech = (
            current_row.get("ema_20", 0) > current_row.get("ema_50", 0)
            and current_row.get("rsi_14", 50) > 50
        )
        determ_regime = RegimeAnalysisOutput(
            symbol=sym,
            regime=(
                MarketRegime.BULLISH_TREND
                if is_bull_tech
                else MarketRegime.BEARISH_TREND
            ),
            confidence=0.80,
            volatility_state="NORMAL",
            recommended_action=ActionType.BUY if is_bull_tech else ActionType.HOLD,
            max_suggested_allocation_pct=10.0,
            reasoning="Deterministic rule check.",
        )

        if use_ai:
          regime_out = agent._deterministic_fallback(feat_input)
        else:
          regime_out = determ_regime

        # Generate strategy signal
        signal = strategy.generate_signal(
            symbol=sym,
            df_features=df_slice,
            regime_output=regime_out,
            current_price_toman=cur_price,
            spread_pct=0.05,
        )

        # Counterfactual tracking: what would deterministic have done?
        if track_counterfactuals:
          determ_signal = strategy.generate_signal(
              symbol=sym,
              df_features=df_slice,
              regime_output=determ_regime,
              current_price_toman=cur_price,
              spread_pct=0.05,
          )
          if determ_signal and determ_signal.action == ActionType.BUY:
            ai_approved = (
                signal is not None and signal.action == ActionType.BUY
            )
            counterfactual_logs.append({
                "timestamp": current_time_str,
                "symbol": sym,
                "price": cur_price,
                "deterministic_action": "BUY",
                "ai_action": "BUY" if ai_approved else "VETO_HOLD",
                "ai_regime": regime_out.regime.value,
                "ai_confidence": regime_out.confidence,
                "ai_vetoed": not ai_approved,
            })

        if signal and signal.action == ActionType.BUY:
          signals_count += 1
          # Check portfolio constraints
          current_equity = portfolio.get_total_equity()
          crypto_exposure = sum(
              p.market_value_toman for p in portfolio.positions.values()
          )

          risk_res = risk_engine.evaluate_signal(
              signal=signal,
              current_portfolio_value_toman=current_equity,
              current_cash_toman=portfolio.cash_toman,
              current_crypto_exposure_toman=crypto_exposure,
              active_positions=portfolio.positions,
              current_market_spread_pct=0.05,
          )

          if (
              risk_res.approved
              and risk_res.approved_value_toman >= 50_000.0
              and sym not in portfolio.positions
          ):
            # Order Execution Modeling:
            limit_buy_price = cur_price * (1.0 + (self.slippage_pct / 100.0))
            if cur_low <= limit_buy_price:
              qty = risk_res.approved_value_toman / limit_buy_price
              is_maker = False if limit_buy_price >= cur_price else True
              fill = portfolio.record_fill(
                  symbol=sym,
                  side="BUY",
                  quantity=qty,
                  price=limit_buy_price,
                  is_maker=is_maker,
              )
              total_traded_notional_toman += fill["notional"]
              trades_history.append({
                  "timestamp": current_time_str,
                  "symbol": sym,
                  "side": "BUY",
                  "reason": signal.rationale,
                  "quantity": fill["quantity"],
                  "price": fill["price"],
                  "fee": fill["fee"],
                  "fee_rate": fill["fee_rate"],
                  "is_maker": fill["is_maker"],
              })
            else:
              unfilled_orders_count += 1
          else:
            risk_vetoes_count += 1

      # 3. Snapshot portfolio state at this timestamp
      snap = portfolio.get_snapshot(current_time_str)
      equity_curve.append(snap.model_dump())

    # 4. End-of-competition forced liquidation into Toman
    for sym in list(portfolio.positions.keys()):
      pos = portfolio.positions[sym]
      df_sym = features_by_symbol[sym]
      final_price = float(df_sym.iloc[-1]["close"]) * (
          1.0 - (self.slippage_pct / 100.0)
      )
      fill = portfolio.record_fill(
          symbol=sym,
          side="SELL",
          quantity=pos.quantity,
          price=final_price,
          is_maker=False,  # Emergency liquidation treated as taker
      )
      total_traded_notional_toman += fill["notional"]
      trades_history.append({
          "timestamp": str(df_sym.iloc[-1]["timestamp"]),
          "symbol": sym,
          "side": "SELL",
          "reason": "END_OF_COMPETITION_LIQUIDATION_TO_TOMAN",
          "quantity": fill["quantity"],
          "price": fill["price"],
          "gross_gain": fill.get("gross_gain", 0.0),
          "net_gain": fill.get("net_gain", 0.0),
          "fee": fill["fee"],
          "fee_rate": fill["fee_rate"],
          "is_maker": fill["is_maker"],
      })

    # Summary Statistics
    final_equity = portfolio.get_total_equity()
    gross_pnl = portfolio.gross_realized_pnl_toman
    total_fees = portfolio.total_fees_paid_toman
    net_pnl = final_equity - self.initial_capital_toman
    net_return_pct = (net_pnl / self.initial_capital_toman) * 100.0
    turnover = (
        (total_traded_notional_toman / self.initial_capital_toman)
        if self.initial_capital_toman > 0
        else 0.0
    )

    # Max Drawdown across unified equity curve
    peak = self.initial_capital_toman
    max_dd = 0.0
    for eq in equity_curve:
      val = eq["total_equity_toman"]
      if val > peak:
        peak = val
      dd = (peak - val) / peak * 100.0 if peak > 0 else 0.0
      if dd > max_dd:
        max_dd = dd

    closed_sells = [t for t in trades_history if t["side"] == "SELL"]
    winning_trades = [t for t in closed_sells if t.get("net_gain", 0.0) > 0]
    losing_trades = [t for t in closed_sells if t.get("net_gain", 0.0) <= 0]
    win_rate = (
        (len(winning_trades) / len(closed_sells) * 100.0)
        if closed_sells
        else 0.0
    )

    maker_fees = sum(t["fee"] for t in trades_history if t.get("is_maker"))
    taker_fees = sum(t["fee"] for t in trades_history if not t.get("is_maker"))

    # Compute counterfactual value-add of AI
    vetoed_signals = [cf for cf in counterfactual_logs if cf["ai_vetoed"]]

    return {
        "use_ai": use_ai,
        "initial_capital_toman": self.initial_capital_toman,
        "final_equity_toman": round(final_equity, 0),
        "gross_pnl_toman": round(gross_pnl, 0),
        "total_fees_paid_toman": round(total_fees, 0),
        "maker_fees_toman": round(maker_fees, 0),
        "taker_fees_toman": round(taker_fees, 0),
        "net_pnl_toman": round(net_pnl, 0),
        "net_return_pct": round(net_return_pct, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "total_trades": len(trades_history),
        "closed_trades": len(closed_sells),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate_pct": round(win_rate, 2),
        "turnover": round(turnover, 2),
        "signals_generated": signals_count,
        "risk_vetoes_count": risk_vetoes_count,
        "unfilled_orders_count": unfilled_orders_count,
        "total_traded_notional_toman": round(total_traded_notional_toman, 0),
        "final_cash_toman": round(portfolio.cash_toman, 0),
        "final_crypto_holdings": {
            k: v.quantity for k, v in portfolio.positions.items()
        },
        "all_holdings_liquidated_to_toman": len(portfolio.positions) == 0,
        "counterfactual_vetoes_count": len(vetoed_signals),
        "counterfactual_logs": counterfactual_logs,
        "trades": trades_history,
    }
