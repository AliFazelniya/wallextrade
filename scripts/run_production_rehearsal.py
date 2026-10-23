#!/usr/bin/env python3
"""Phase 15 Production-Like Shadow Rehearsal Runner.

Executes production-like shadow trading against live Wallex public API:
1. Real Data Ingestion (depth, spread, live 15m OHLCV candles).
2. Data freshness and quality validation.
3. Real feature extraction (EMA, ATR, RSI, VolRatio).
4. Frozen AI Regime Classification Agent.
5. Deterministic Risk Engine gating.
6. Mocked Execution Adapter (SHADOW mode, live_execution_authorized=False).
7. Full Portfolio Accounting & JSONL Decision Logging.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import pathlib
import sys
import time
from typing import Any, Dict, List
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
logger = logging.getLogger("production_rehearsal")


async def run_rehearsal(num_cycles: int = 10, cycle_delay_seconds: float = 1.0) -> Dict[str, Any]:
    logger.info("Initializing Phase 15 Production Shadow Rehearsal...")

    manifest_path = repo_root / "config" / "frozen_strategy_manifest_v0.6.0.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    target_symbol = manifest["frozen_strategy"]["symbol"]  # BTCTMN
    logger.info("Target Symbol: %s | Timeframe: 15m | Capital: 5,000,000 TMN", target_symbol)

    client = WallexClient(timeout_seconds=10.0, rate_limit_per_minute=60)
    fetcher = MarketDataFetcher(client)
    portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
    risk_engine = RiskEngine(
        max_single_order_toman=500_000.0,
        max_portfolio_exposure_pct=60.0,
        max_drawdown_pct=5.0,
        max_daily_loss_toman=200_000.0,
        allowed_symbols={target_symbol},
    )
    strategy = RegimeMomentumStrategy(
        min_confidence=manifest["frozen_strategy"]["min_confidence"],
        take_profit_pct=manifest["frozen_strategy"]["take_profit_pct"],
        stop_loss_pct=manifest["frozen_strategy"]["stop_loss_pct"],
    )
    agent = RegimeClassificationAgent(model=manifest["ai_regime_agent"]["primary_model"])
    adapter = ExchangeAdapter(
        client=client,
        portfolio=portfolio,
        trading_mode="SHADOW",
        live_execution_authorized=False,  # STRICT GUARDRAIL
        allowed_symbols={target_symbol},
        slippage_pct=0.15,
    )

    log_path = repo_root / "logs" / "production_rehearsal_phase16.jsonl"
    decision_logger = DecisionLogger(log_path=str(log_path))

    cycle_records: List[Dict[str, Any]] = []
    latencies_ms: List[float] = []
    start_wall_time = time.time()
    cached_candles: Optional[pd.DataFrame] = None

    for cycle in range(1, num_cycles + 1):
        t_start = time.perf_counter()
        cycle_time_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info("=== REHEARSAL CYCLE %d / %d [%s] ===", cycle, num_cycles, target_symbol)

        # 1. Ingest live market spread and depth
        spread_info = await fetcher.fetch_current_spread(target_symbol)
        best_bid = spread_info["bid"]
        best_ask = spread_info["ask"]
        spread_pct = spread_info["spread_pct"]

        # 2. Ingest live OHLCV candles (Cycle 1: warm-up; Cycles 2+: incremental cached update)
        df_candles, audit = await fetcher.fetch_incremental_ohlcv(
            symbol=target_symbol,
            cached_df=cached_candles,
            resolution="15",
            warmup_days=5,
        )
        cached_candles = df_candles

        is_fresh, freshness_msg = fetcher.validate_data_freshness(df_candles, max_staleness_minutes=60.0)

        # 3. Extract Features
        df_feat = extract_features(df_candles)
        snapshot = get_latest_feature_snapshot(df_feat)
        current_price = float(df_feat.iloc[-1]["close"])
        candle_timestamp = str(df_feat.iloc[-1]["timestamp"])

        portfolio.update_market_price(target_symbol, current_price)

        # 4. Form AI Feature Input & Classify Regime
        feat_input = MarketFeaturesInput(
            symbol=target_symbol,
            price_toman=current_price,
            ema_spread_pct=snapshot.get("ema_spread_pct", 0.0),
            rsi_14=snapshot.get("rsi_14", 50.0),
            atr_pct=snapshot.get("atr_pct", 2.0),
            vol_ratio=snapshot.get("vol_ratio", 1.0),
            spread_pct=spread_pct,
            trend_direction=snapshot.get("trend_direction", "BEARISH"),
        )
        regime_output = await agent.classify_regime(feat_input)

        # 5. Generate Candidate Strategy Signal
        signal = strategy.generate_signal(
            symbol=target_symbol,
            df_features=df_feat,
            regime_output=regime_output,
            current_price_toman=current_price,
            spread_pct=spread_pct,
        )

        # 6. Evaluate Signal with Risk Engine
        risk_eval = None
        exec_res = None

        if signal:
            current_equity = portfolio.get_total_equity()
            crypto_exposure = sum(p.market_value_toman for p in portfolio.positions.values())
            risk_eval = risk_engine.evaluate_signal(
                signal=signal,
                current_portfolio_value_toman=current_equity,
                current_cash_toman=portfolio.cash_toman,
                current_crypto_exposure_toman=crypto_exposure,
                active_positions=portfolio.positions,
                current_market_spread_pct=spread_pct,
            )

            # 7. Execute Mocked Shadow Order
            if risk_eval.approved:
                exec_res = await adapter.execute_order(
                    symbol=target_symbol,
                    action=signal.action,
                    target_price=current_price,
                    approved_value_toman=risk_eval.approved_value_toman,
                )

        t_end = time.perf_counter()
        cycle_latency_ms = (t_end - t_start) * 1000.0
        latencies_ms.append(cycle_latency_ms)

        # 8. Snapshot & Decision Logging
        port_snap = portfolio.get_snapshot(cycle_time_str)
        decision_logger.log_decision(
            timestamp=cycle_time_str,
            symbol=target_symbol,
            event_type="TRADE_PROPOSED" if signal else "MARKET_MONITOR",
            market_observations={
                "price": current_price,
                "bid": best_bid,
                "ask": best_ask,
                "spread_pct": spread_pct,
                "candle_time": candle_timestamp,
                "rsi_14": snapshot.get("rsi_14"),
                "vol_ratio": snapshot.get("vol_ratio"),
                "ema_spread_pct": snapshot.get("ema_spread_pct"),
            },
            regime_classification=regime_output.model_dump(),
            proposed_signal=signal.model_dump() if signal else None,
            risk_evaluation=risk_eval.model_dump() if risk_eval else None,
            execution_result=exec_res,
            portfolio_summary=port_snap.model_dump(),
            notes=f"Production rehearsal cycle {cycle} (latency {cycle_latency_ms:.1f}ms)",
        )

        record = {
            "cycle": cycle,
            "timestamp": cycle_time_str,
            "candle_timestamp": candle_timestamp,
            "data_freshness": freshness_msg,
            "price_toman": current_price,
            "spread_pct": spread_pct,
            "ai_regime": regime_output.regime.value,
            "ai_confidence": regime_output.confidence,
            "ai_action": regime_output.recommended_action.value,
            "signal_action": signal.action.value if signal else "HOLD",
            "risk_approved": risk_eval.approved if risk_eval else None,
            "risk_veto_reasons": risk_eval.veto_reasons if risk_eval else [],
            "exec_status": exec_res.get("status") if exec_res else "NO_ORDER",
            "portfolio_cash_toman": port_snap.cash_toman,
            "portfolio_equity_toman": port_snap.total_equity_toman,
            "cycle_latency_ms": round(cycle_latency_ms, 1),
        }
        cycle_records.append(record)
        logger.info(
            "Cycle %d Done: Price=%.0f TMN | Regime=%s (%.2f) | Signal=%s | Latency=%.1fms",
            cycle, current_price, regime_output.regime.value, regime_output.confidence,
            signal.action.value if signal else "HOLD", cycle_latency_ms,
        )

        if cycle < num_cycles:
            await asyncio.sleep(cycle_delay_seconds)

    await client.close()
    elapsed_wall_seconds = time.time() - start_wall_time

    rehearsal_summary = {
        "target_symbol": target_symbol,
        "total_cycles_executed": num_cycles,
        "elapsed_wall_seconds": round(elapsed_wall_seconds, 2),
        "avg_latency_ms": round(sum(latencies_ms) / len(latencies_ms), 1),
        "min_latency_ms": round(min(latencies_ms), 1),
        "max_latency_ms": round(max(latencies_ms), 1),
        "candidate_signals_count": sum(1 for r in cycle_records if r["signal_action"] != "HOLD"),
        "ai_approvals_count": sum(1 for r in cycle_records if r["ai_action"] == "BUY"),
        "ai_vetoes_count": sum(1 for r in cycle_records if r["ai_action"] == "HOLD"),
        "simulated_orders_count": sum(1 for r in cycle_records if r["exec_status"] != "NO_ORDER"),
        "final_cash_toman": portfolio.cash_toman,
        "final_equity_toman": portfolio.get_total_equity(),
        "cycles": cycle_records,
    }

    results_path = repo_root / "research" / "phase16_rehearsal_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(rehearsal_summary, f, indent=2)

    logger.info("Rehearsal finished in %.2f seconds. Summary saved to %s", elapsed_wall_seconds, results_path)
    return rehearsal_summary


if __name__ == "__main__":
    asyncio.run(run_rehearsal())
