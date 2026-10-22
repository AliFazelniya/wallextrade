"""Audited Historical Backtesting Engine.

Simulates algorithmic execution candle-by-candle with:
- Fee deductions: Maker (0.25%) for limit entries, Taker (0.30%) for stop/panic exits.
- Slippage: 0.15% per trade.
- Separate accounting for Gross P&L, Total Fees, and Net P&L.
- Drawdown calculation over the complete equity curve (cash + mark-to-market holdings).
- End-of-competition forced liquidation into Toman.
- Zero look-ahead bias.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import ActionType, MarketFeaturesInput, ProposedTradeSignal
from src.features.indicators import extract_features
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine
from src.strategy.regime_momentum import RegimeMomentumStrategy

logger = logging.getLogger(__name__)


class BacktestEngine:
  """Runs reproducible walk-forward simulations over historical OHLCV data."""

  def __init__(
      self,
      initial_capital_toman: float = 5_000_000.0,
      maker_fee_rate: float = 0.0025,  # 0.25% Wallex maker fee
      taker_fee_rate: float = 0.0030,  # 0.30% Wallex taker fee
      slippage_pct: float = 0.15,
  ):
    self.initial_capital_toman = initial_capital_toman
    self.maker_fee_rate = maker_fee_rate
    self.taker_fee_rate = taker_fee_rate
    self.slippage_pct = slippage_pct

  def run_backtest(
      self,
      symbol: str,
      df_ohlcv: pd.DataFrame,
      strategy: RegimeMomentumStrategy,
      risk_engine: RiskEngine,
      agent: RegimeClassificationAgent,
      audit_data: Optional[Dict[str, Any]] = None,
  ) -> Dict[str, Any]:
    if len(df_ohlcv) < 60:
      raise ValueError("Insufficient candle history (minimum 60 bars required)")

    portfolio = PortfolioEngine(
        initial_capital_toman=self.initial_capital_toman,
        maker_fee_rate=self.maker_fee_rate,
        taker_fee_rate=self.taker_fee_rate,
    )

    trades_history: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []

    # Pre-calculate features (each step only accesses index <= i)
    df_feat = extract_features(df_ohlcv)

    # Chronological simulation
    for i in range(50, len(df_feat)):
      current_bar = df_feat.iloc[i]
      current_price = float(current_bar["close"])
      current_time = str(current_bar["timestamp"])

      # 1. Update position valuation
      portfolio.update_market_price(symbol, current_price)

      # 2. Check existing stop-loss / take-profit triggers
      if symbol in portfolio.positions:
        pos = portfolio.positions[symbol]
        entry_price = pos.avg_entry_price
        pnl_pct = (current_price - entry_price) / entry_price * 100.0

        if pnl_pct <= -strategy.stop_loss_pct or pnl_pct >= strategy.take_profit_pct:
          is_sl = pnl_pct <= -strategy.stop_loss_pct
          exit_price = current_price * (1.0 - (self.slippage_pct / 100.0))
          # Stop loss executed as taker; take profit can be limit maker
          fill = portfolio.record_fill(
              symbol=symbol,
              side="SELL",
              quantity=pos.quantity,
              price=exit_price,
              is_maker=not is_sl,
          )
          trades_history.append({
              "timestamp": current_time,
              "symbol": symbol,
              "side": "SELL",
              "reason": f"TRIGGER_{'SL' if is_sl else 'TP'}",
              "quantity": fill["quantity"],
              "price": fill["price"],
              "gross_gain": fill.get("gross_gain", 0.0),
              "net_gain": fill.get("net_gain", 0.0),
              "fee": fill["fee"],
              "fee_rate": fill["fee_rate"],
          })

      # 3. Build current feature slice (no future lookahead)
      df_slice = df_feat.iloc[: i + 1]
      feat_input = MarketFeaturesInput(
          symbol=symbol,
          price_toman=current_price,
          ema_spread_pct=float(current_bar.get("ema_spread_pct", 0.0)),
          rsi_14=float(current_bar.get("rsi_14", 50.0)),
          atr_pct=float(current_bar.get("atr_pct", 2.0)),
          vol_ratio=float(current_bar.get("vol_ratio", 1.0)),
          spread_pct=0.05,
          trend_direction=(
              "BULLISH"
              if current_bar.get("ema_20", 0) > current_bar.get("ema_50", 0)
              else "BEARISH"
          ),
      )

      # 4. Agent regime classification
      regime_out = agent._deterministic_fallback(feat_input)

      # 5. Strategy signal generation
      signal = strategy.generate_signal(
          symbol=symbol,
          df_features=df_slice,
          regime_output=regime_out,
          current_price_toman=current_price,
          spread_pct=0.05,
      )

      # 6. Risk Engine Evaluation
      if signal and signal.action == ActionType.BUY:
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
            and symbol not in portfolio.positions
        ):
          buy_price = current_price * (1.0 + (self.slippage_pct / 100.0))
          qty = risk_res.approved_value_toman / buy_price
          fill = portfolio.record_fill(
              symbol=symbol,
              side="BUY",
              quantity=qty,
              price=buy_price,
              is_maker=True,  # Limit buy order considered maker
          )
          trades_history.append({
              "timestamp": current_time,
              "symbol": symbol,
              "side": "BUY",
              "reason": signal.rationale,
              "quantity": fill["quantity"],
              "price": fill["price"],
              "fee": fill["fee"],
              "fee_rate": fill["fee_rate"],
          })

      # Record equity curve snapshot
      snapshot = portfolio.get_snapshot(current_time)
      equity_curve.append(snapshot.model_dump())

    # End-of-competition forced liquidation into Toman
    if symbol in portfolio.positions:
      pos = portfolio.positions[symbol]
      final_price = float(df_feat.iloc[-1]["close"]) * (
          1.0 - (self.slippage_pct / 100.0)
      )
      fill = portfolio.record_fill(
          symbol=symbol,
          side="SELL",
          quantity=pos.quantity,
          price=final_price,
          is_maker=False,  # Emergency liquidation treated as taker
      )
      trades_history.append({
          "timestamp": str(df_feat.iloc[-1]["timestamp"]),
          "symbol": symbol,
          "side": "SELL",
          "reason": "END_OF_COMPETITION_LIQUIDATION_TO_TOMAN",
          "quantity": fill["quantity"],
          "price": fill["price"],
          "gross_gain": fill.get("gross_gain", 0.0),
          "net_gain": fill.get("net_gain", 0.0),
          "fee": fill["fee"],
          "fee_rate": fill["fee_rate"],
      })

    # Summary Statistics
    final_equity = portfolio.get_total_equity()
    gross_pnl = portfolio.gross_realized_pnl_toman
    total_fees = portfolio.total_fees_paid_toman
    net_pnl = final_equity - self.initial_capital_toman
    net_return_pct = (net_pnl / self.initial_capital_toman) * 100.0

    # Max Drawdown across all equity snapshots
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
    win_rate = (
        (len(winning_trades) / len(closed_sells) * 100.0)
        if closed_sells
        else 0.0
    )

    return {
        "symbol": symbol,
        "audit": audit_data or {},
        "initial_capital_toman": self.initial_capital_toman,
        "final_equity_toman": round(final_equity, 0),
        "gross_pnl_toman": round(gross_pnl, 0),
        "total_fees_paid_toman": round(total_fees, 0),
        "net_pnl_toman": round(net_pnl, 0),
        "net_return_pct": round(net_return_pct, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "total_trades": len(trades_history),
        "closed_trades": len(closed_sells),
        "winning_trades": len(winning_trades),
        "win_rate_pct": round(win_rate, 2),
        "trades": trades_history,
        "final_cash_toman": round(portfolio.cash_toman, 0),
        "final_crypto_holdings": {
            k: v.quantity for k, v in portfolio.positions.items()
        },
        "all_holdings_liquidated_to_toman": len(portfolio.positions) == 0,
    }
