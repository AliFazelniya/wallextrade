#!/usr/bin/env python3
"""Independent Strategy & 4-Way Baseline Validation Runner.

Compares:
1. Buy & Hold the underlying asset over the same period.
2. Remaining 100% in cash Toman (0% P&L, 0 Drawdown, 0 Fees).
3. Deterministic Strategy without AI (pure technical rules).
4. AI-Assisted Strategy (with market-regime classification filter).

Also executes Fee-Sensitivity Stress Scenarios:
- Scenario 1 (Official Base): Maker 0.25%, Taker 0.30%
- Scenario 2 (Adverse Taker): Maker 0.30%, Taker 0.30%
- Scenario 3 (Adverse Stressed): Maker 0.35%, Taker 0.35%
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import pathlib
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.agents.regime_agent import RegimeClassificationAgent
from src.backtest.engine import BacktestEngine
from src.data.client import WallexClient
from src.data.fetcher import MarketDataFetcher
from src.risk.engine import RiskEngine
from src.strategy.regime_momentum import RegimeMomentumStrategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("strategy_validation")


async def run_validation():
    symbols = ["BTCTMN", "ETHTMN"]
    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    from_ts = now_ts - (30 * 86400)

    client = WallexClient()
    fetcher = MarketDataFetcher(client)
    strategy = RegimeMomentumStrategy(min_confidence=0.70)
    agent = RegimeClassificationAgent()

    results_by_symbol = {}

    print("\n" + "="*80)
    print("  STRATEGY BENCHMARKING & 4-WAY BASELINE COMPARISON (Past 19 Days UDF)")
    print("="*80)

    for sym in symbols:
        logger.info("Fetching and resampling data for %s...", sym)
        df, audit = await fetcher.fetch_ohlcv_dataframe(sym, "15", from_ts, now_ts)
        if df.empty or len(df) < 60:
            continue

        # Asset Buy & Hold Performance
        first_price = float(df.iloc[0]["close"])
        last_price = float(df.iloc[-1]["close"])
        hold_return_pct = (last_price - first_price) / first_price * 100.0
        # Buy & Hold max drawdown
        roll_max = df["close"].cummax()
        daily_dd = (roll_max - df["close"]) / roll_max * 100.0
        hold_max_dd = float(daily_dd.max())

        risk_engine = RiskEngine(
            max_single_order_toman=500_000.0,
            max_portfolio_exposure_pct=60.0,
            max_drawdown_pct=5.0,
            allowed_symbols={sym}
        )

        # Baseline 2: 100% Cash Toman
        cash_return_pct = 0.0
        cash_max_dd = 0.0

        # Baseline 3: Deterministic Strategy WITHOUT AI
        engine_base = BacktestEngine(initial_capital_toman=5_000_000.0, maker_fee_rate=0.0025, taker_fee_rate=0.0030)
        res_determ = engine_base.run_backtest(sym, df, strategy, risk_engine, agent, audit, use_ai=False)

        # Baseline 4: AI-Assisted Strategy (WITH AI Regime Filter)
        engine_ai = BacktestEngine(initial_capital_toman=5_000_000.0, maker_fee_rate=0.0025, taker_fee_rate=0.0030)
        res_ai = engine_ai.run_backtest(sym, df, strategy, risk_engine, agent, audit, use_ai=True)

        # Fee Sensitivity Scenarios for AI Strategy
        # Scenario 2: All Taker 0.30% / 0.30%
        engine_pess = BacktestEngine(initial_capital_toman=5_000_000.0, maker_fee_rate=0.0030, taker_fee_rate=0.0030)
        res_pess = engine_pess.run_backtest(sym, df, strategy, risk_engine, agent, audit, use_ai=True)

        # Scenario 3: Stressed 0.35% / 0.35%
        engine_stress = BacktestEngine(initial_capital_toman=5_000_000.0, maker_fee_rate=0.0035, taker_fee_rate=0.0035)
        res_stress = engine_stress.run_backtest(sym, df, strategy, risk_engine, agent, audit, use_ai=True)

        results_by_symbol[sym] = {
            "buy_and_hold": {
                "return_pct": round(hold_return_pct, 2),
                "max_drawdown_pct": round(hold_max_dd, 2),
                "trades": 1,
                "net_pnl_toman": round(5_000_000.0 * (hold_return_pct / 100.0), 0)
            },
            "cash_toman": {
                "return_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "trades": 0,
                "net_pnl_toman": 0.0
            },
            "deterministic_no_ai": res_determ,
            "ai_assisted": res_ai,
            "fee_sensitivity": {
                "base_maker25_taker30": res_ai["net_return_pct"],
                "pessimistic_taker30_taker30": res_pess["net_return_pct"],
                "stressed_35_35": res_stress["net_return_pct"]
            }
        }

        print(f"\n--- Symbol: {sym} (1,825 genuine 15m candles) ---")
        print(f"1. Buy & Hold Asset:        {hold_return_pct:+.2f}% | Max DD: {hold_max_dd:.2f}% | Net P&L: {5_000_000*(hold_return_pct/100):+,.0f} TMN")
        print(f"2. 100% Cash Toman:          0.00% | Max DD:  0.00% | Net P&L:          0 TMN")
        print(f"3. Deterministic (No AI):   {res_determ['net_return_pct']:+.2f}% | Max DD: {res_determ['max_drawdown_pct']:.2f}% | Net P&L: {res_determ['net_pnl_toman']:+,.0f} TMN (Trades: {res_determ['closed_trades']})")
        print(f"4. AI-Assisted Strategy:    {res_ai['net_return_pct']:+.2f}% | Max DD: {res_ai['max_drawdown_pct']:.2f}% | Net P&L: {res_ai['net_pnl_toman']:+,.0f} TMN (Trades: {res_ai['closed_trades']})")
        print(f"   Fee Sensitivity: Base: {res_ai['net_return_pct']:+.2f}% | Taker 0.30%: {res_pess['net_return_pct']:+.2f}% | Stressed 0.35%: {res_stress['net_return_pct']:+.2f}%")
        print(f"   Turnover: {res_ai['turnover']}x | Total Fees: {res_ai['total_fees_paid_toman']:,.0f} TMN | Unfilled Orders: {res_ai['unfilled_orders_count']}")

    await client.close()
    return results_by_symbol


if __name__ == "__main__":
    asyncio.run(run_validation())
