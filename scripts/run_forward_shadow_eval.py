#!/usr/bin/env python3
"""Prospective Forward Shadow Testing Runner for Phase 13.

Executes continuous live-market shadow monitoring against Wallex live API.
Records:
- Live market spread and depth
- Feature extraction & latency (ms)
- AI Regime classification
- RiskEngine deterministic gatekeeping
- Simulated shadow order execution (zero real orders: live_execution_authorized=False)
- Network error recovery and latency metrics
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import pathlib
import sys
import time
import numpy as np
import pandas as pd

repo_root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import ActionType, MarketFeaturesInput
from src.data.client import WallexClient
from src.data.fetcher import MarketDataFetcher
from src.exchange.adapter import ExchangeAdapter
from src.features.indicators import extract_features, get_latest_feature_snapshot
from src.monitoring.logger import DecisionLogger
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine
from src.strategy.regime_momentum import RegimeMomentumStrategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("forward_shadow")


async def main():
    logger.info("Starting Phase 13 Prospective Forward Shadow Evaluation...")

    # Load verified allowed symbols
    with open(repo_root / "config" / "allowed_markets.json", "r", encoding="utf-8") as f:
        allowed_data = json.load(f)
    allowed_symbols = [m["symbol"] for m in allowed_data.get("markets", [])[:6]]

    with open(repo_root / "config" / "market_restrictions.json", "r", encoding="utf-8") as f:
        restr_data = json.load(f)
    restricted_symbols = set()
    for cat in ["credit_inactive_symbols", "excluded_usdt_pairs", "excluded_low_liquidity", "excluded_high_spread"]:
        for item in restr_data.get(cat, []):
            restricted_symbols.add(item["symbol"] if isinstance(item, dict) else item)

    client = WallexClient()
    fetcher = MarketDataFetcher(client)
    portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
    risk_engine = RiskEngine(
        max_single_order_toman=500_000.0,
        max_portfolio_exposure_pct=60.0,
        max_drawdown_pct=5.0,
        allowed_symbols=set(allowed_symbols),
        restricted_symbols=restricted_symbols,
    )
    strategy = RegimeMomentumStrategy(min_confidence=0.70)
    agent = RegimeClassificationAgent()
    adapter = ExchangeAdapter(
        client=client,
        portfolio=portfolio,
        trading_mode="SHADOW",
        live_execution_authorized=False,  # STRICT GUARDRAIL
        allowed_symbols=set(allowed_symbols),
        restricted_symbols=restricted_symbols,
    )

    log_file = repo_root / "logs" / "shadow_forward_phase13.jsonl"
    decision_logger = DecisionLogger(log_path=str(log_file))

    num_cycles = 3
    cycle_delay_seconds = 1

    cycle_records = []
    latencies_ms = []
    spreads_recorded = {}
    signals_count = 0
    risk_approvals_count = 0

    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    from_ts = now_ts - (15 * 86400)

    for cycle in range(1, num_cycles + 1):
        logger.info("--- SHADOW FORWARD CYCLE %d / %d ---", cycle, num_cycles)
        for sym in allowed_symbols:
            t0 = time.perf_counter()
            try:
                # 1. Measure Depth & Spread Latency
                spread_info = await fetcher.fetch_current_spread(sym)
                t_spread = (time.perf_counter() - t0) * 1000.0
                latencies_ms.append(t_spread)

                best_bid = spread_info["bid"]
                best_ask = spread_info["ask"]
                spread_pct = spread_info["spread_pct"]
                spreads_recorded.setdefault(sym, []).append(spread_pct)

                if best_bid <= 0:
                    continue

                # 2. Fetch latest candle slice
                df, _ = await fetcher.fetch_ohlcv_dataframe(sym, "15", from_ts, now_ts)
                if df.empty or len(df) < 50:
                    continue

                df_feat = extract_features(df)
                cur_price = float(df_feat.iloc[-1]["close"])
                snapshot = get_latest_feature_snapshot(df_feat)
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

                # Update portfolio valuation mark-to-market
                portfolio.update_market_price(sym, cur_price)

                # 3. AI Regime Classification
                feat_in = MarketFeaturesInput(
                    symbol=sym,
                    price_toman=cur_price,
                    ema_spread_pct=snapshot.get("ema_spread_pct", 0.0),
                    rsi_14=snapshot.get("rsi_14", 50.0),
                    atr_pct=snapshot.get("atr_pct", 2.0),
                    vol_ratio=snapshot.get("vol_ratio", 1.0),
                    spread_pct=spread_pct,
                    trend_direction=snapshot.get("trend_direction", "BEARISH"),
                )
                t_ai_start = time.perf_counter()
                regime_out = await agent.classify_regime(feat_in)
                ai_latency_ms = (time.perf_counter() - t_ai_start) * 1000.0

                # 4. Strategy Signal Generation
                signal = strategy.generate_signal(
                    symbol=sym,
                    df_features=df_feat,
                    regime_output=regime_out,
                    current_price_toman=cur_price,
                    spread_pct=spread_pct,
                )

                risk_res = None
                exec_res = None

                if signal:
                    signals_count += 1
                    current_equity = portfolio.get_total_equity()
                    crypto_exposure = sum(p.market_value_toman for p in portfolio.positions.values())
                    risk_res = risk_engine.evaluate_signal(
                        signal=signal,
                        current_portfolio_value_toman=current_equity,
                        current_cash_toman=portfolio.cash_toman,
                        current_crypto_exposure_toman=crypto_exposure,
                        active_positions=portfolio.positions,
                        current_market_spread_pct=spread_pct,
                    )
                    if risk_res.approved:
                        risk_approvals_count += 1
                        exec_res = await adapter.execute_order(
                            symbol=sym,
                            action=signal.action,
                            target_price=cur_price,
                            approved_value_toman=risk_res.approved_value_toman,
                        )

                # 5. Log decision audit trail
                port_snap = portfolio.get_snapshot(now_str)
                total_latency_ms = (time.perf_counter() - t0) * 1000.0
                decision_logger.log_decision(
                    timestamp=now_str,
                    symbol=sym,
                    event_type="SHADOW_EVALUATION",
                    market_observations={
                        "price": cur_price,
                        "bid": best_bid,
                        "ask": best_ask,
                        "spread_pct": spread_pct,
                        "rsi": snapshot.get("rsi_14"),
                        "vol_ratio": snapshot.get("vol_ratio"),
                        "api_latency_ms": round(t_spread, 1),
                        "total_cycle_latency_ms": round(total_latency_ms, 1),
                    },
                    regime_classification=regime_out.model_dump(),
                    proposed_signal=signal.model_dump() if signal else None,
                    risk_evaluation=risk_res.model_dump() if risk_res else None,
                    execution_result=exec_res,
                    portfolio_summary=port_snap.model_dump(),
                    notes=f"Shadow Cycle {cycle}",
                )

                cycle_records.append({
                    "cycle": cycle,
                    "symbol": sym,
                    "price": cur_price,
                    "spread_pct": spread_pct,
                    "regime": regime_out.regime.value,
                    "confidence": regime_out.confidence,
                    "signal": signal.action.value if signal else "NONE",
                    "latency_ms": round(total_latency_ms, 1),
                })

            except Exception as e:
                logger.error("Error evaluating %s in shadow cycle: %s", sym, e)

        await asyncio.sleep(cycle_delay_seconds)

    # Summary metrics
    mean_lat = float(np.mean(latencies_ms)) if latencies_ms else 0.0
    p95_lat = float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0
    mean_spreads = {s: round(float(np.mean(vals)), 4) for s, vals in spreads_recorded.items()}

    summary = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mode": "PROSPECTIVE_FORWARD_SHADOW",
        "live_execution_authorized": False,
        "total_evaluations": len(cycle_records),
        "cycles_completed": num_cycles,
        "symbols_monitored": allowed_symbols,
        "signals_generated": signals_count,
        "risk_approvals": risk_approvals_count,
        "latency_metrics_ms": {
            "mean_api_latency": round(mean_lat, 1),
            "p95_api_latency": round(p95_lat, 1),
            "min_latency": round(float(np.min(latencies_ms)), 1) if latencies_ms else 0.0,
            "max_latency": round(float(np.max(latencies_ms)), 1) if latencies_ms else 0.0,
        },
        "mean_spread_pct_by_symbol": mean_spreads,
        "portfolio_final_cash_toman": portfolio.cash_toman,
        "portfolio_open_positions": len(portfolio.positions),
    }

    out_metrics = repo_root / "research" / "forward_shadow_metrics.json"
    with open(out_metrics, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Forward shadow testing complete. Summary saved to %s", out_metrics)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
