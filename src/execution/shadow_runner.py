"""Shadow and Paper Execution Runner for Multi-Asset AI Strategy (Phase 23).

Coordinates Strategy, AI Regime Agent, Risk Engine, Portfolio Accounting,
and Exchange Adapter in strict SHADOW/PAPER mode.

Mandatory Constraints:
- live_execution_authorized is permanently False.
- Never sends live exchange orders.
- Records all shadow signals, order intents, simulated fills, and risk checks.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import ActionType
from src.data.client import WallexClient
from src.data.fetcher import MarketDataFetcher
from src.exchange.adapter import ExchangeAdapter
from src.features.indicators import compute_atr
from src.experimental.features import extract_advanced_features
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine
from src.strategy.multi_asset_momentum import MultiAssetMomentumStrategy

logger = logging.getLogger(__name__)


class ShadowExecutionRunner:
    """Runs the Multi-Asset AI Momentum Strategy in Paper/Shadow Execution Mode."""

    def __init__(
        self,
        strategy: Optional[MultiAssetMomentumStrategy] = None,
        initial_capital_toman: float = 5_000_000.0,
        symbols: Optional[List[str]] = None,
        data_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
    ):
        self.symbols = symbols or ["BTCTMN", "ETHTMN", "SOLTMN"]
        self.strategy = strategy or MultiAssetMomentumStrategy(allowed_symbols=self.symbols)
        self.initial_capital = initial_capital_toman
        self.data_dir = data_dir or Path("/root/starcoach-hack/wallex/data/cache")
        self.log_dir = log_dir or Path("/root/starcoach-hack/wallex/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.portfolio = PortfolioEngine(initial_capital_toman=self.initial_capital)
        self.risk = RiskEngine(
            max_single_order_toman=500_000.0,
            max_portfolio_exposure_pct=60.0,
            max_drawdown_pct=5.0,
            max_spread_pct=0.20,
            allowed_symbols=set(self.symbols),
        )
        self.client = WallexClient(base_url="https://api.wallex.ir")
        self.adapter = ExchangeAdapter(
            client=self.client,
            portfolio=self.portfolio,
            trading_mode="SHADOW",
            live_execution_authorized=False,
            slippage_pct=0.15,
            allowed_symbols=set(self.symbols),
        )

        self.shadow_events: List[Dict[str, Any]] = []

    def record_shadow_event(self, event_type: str, details: Dict[str, Any]) -> None:
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details,
        }
        self.shadow_events.append(event)
        logger.info("[SHADOW EVENT] %s: %s", event_type, details)

    async def fetch_live_market_snapshot(self) -> Dict[str, Dict[str, float]]:
        """Queries live Wallex markets endpoint for active bid/ask/spread."""
        snapshot = {}
        try:
            resp = await self.client.get_markets()
            symbols_data = resp.get("result", {}).get("symbols", {})
            for sym in self.symbols:
                if sym in symbols_data:
                    stats = symbols_data[sym].get("stats", {})
                    last_px = float(stats.get("lastPrice", 0.0))
                    bid_px = float(stats.get("bidPrice", last_px * 0.999))
                    ask_px = float(stats.get("askPrice", last_px * 1.001))
                    spread = ((ask_px - bid_px) / last_px * 100.0) if last_px > 0 else 0.12
                    snapshot[sym] = {
                        "last_price": last_px,
                        "bid_price": bid_px,
                        "ask_price": ask_px,
                        "spread_pct": spread,
                    }
        except Exception as e:
            logger.warning("Failed to fetch live markets from Wallex: %s", e)
        return snapshot

    async def run_live_shadow_cycle(self) -> Dict[str, Any]:
        """Performs a single real-time shadow cycle against live market data."""
        self.record_shadow_event("CYCLE_START", {"mode": "SHADOW", "live_auth": False})
        live_snap = await self.fetch_live_market_snapshot()
        
        cycle_result: Dict[str, Any] = {
            "snapshot_symbols": list(live_snap.keys()),
            "market_snapshot": live_snap,
            "signals": [],
            "risk_verdicts": [],
            "executions": [],
        }

        # Build feature frames using cached data appended with live snapshot price
        market_data_for_ranking: Dict[str, Any] = {}
        for sym in self.symbols:
            csv_path = self.data_dir / f"{sym}_15m_90d.csv"
            if csv_path.exists() and sym in live_snap:
                df_raw = pd.read_csv(csv_path).tail(100)
                df_feat = extract_advanced_features(df_raw)
                cur_px = live_snap[sym]["last_price"]
                spr = live_snap[sym]["spread_pct"]
                market_data_for_ranking[sym] = (df_feat, cur_px, spr)

        # Cross-sectional ranking with AI gating
        top_candidates = self.strategy.rank_cross_sectional_candidates(market_data_for_ranking)
        cycle_result["ranked_candidates"] = [
            {"symbol": sym, "score": score, "price": px, "regime": reg.regime.value, "confidence": reg.confidence}
            for score, sym, px, reg in top_candidates
        ]

        if top_candidates:
            top_score, best_sym, best_px, reg_out = top_candidates[0]
            sig = self.strategy.generate_signal(
                best_sym,
                market_data_for_ranking[best_sym][0],
                reg_out,
                best_px,
                live_snap[best_sym]["spread_pct"],
            )
            if sig:
                cycle_result["signals"].append(sig.dict())
                # Risk check
                risk_eval = self.risk.evaluate_signal(
                    sig,
                    self.portfolio.get_total_equity(),
                    self.portfolio.cash_toman,
                    0.0,
                    self.portfolio.positions,
                    live_snap[best_sym]["spread_pct"],
                )
                cycle_result["risk_verdicts"].append({
                    "symbol": best_sym,
                    "approved": risk_eval.approved,
                    "approved_value": risk_eval.approved_value_toman,
                    "reason": risk_eval.rejection_reason,
                })
                if risk_eval.approved and risk_eval.approved_value_toman >= 50_000.0:
                    exec_res = await self.adapter.execute_order(
                        best_sym,
                        ActionType.BUY,
                        best_px,
                        risk_eval.approved_value_toman,
                        order_type="LIMIT",
                        is_maker=False,
                    )
                    cycle_result["executions"].append(exec_res)

        self.record_shadow_event("CYCLE_COMPLETE", cycle_result)
        return cycle_result
